"""
Game management endpoints.

Handles loading games from Kalshi tickers and managing game state.
Provides endpoints for browsing available NBA games by date.
"""

from datetime import date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid

from backend.models.game import Game, GameCreate, GameUpdate
from backend.integrations.kalshi.client import KalshiClient
from backend.integrations.kalshi.exceptions import (
    KalshiAPIError,
    KalshiAuthError,
    KalshiNotFoundError,
)
from backend.integrations.balldontlie.client import BallDontLieClient
from backend.integrations.balldontlie.exceptions import (
    BallDontLieAPIError,
    BallDontLieAuthError,
    GameMatchError,
)
from backend.utils.ticker_parser import extract_game_info_from_kalshi_ticker
from backend.config.supabase import get_supabase_client
from backend.database import helpers as db

logger = logging.getLogger(__name__)

router = APIRouter()


class LoadGameByTicker(BaseModel):
    """Request model for loading a game by event ticker."""
    event_ticker: str


class LoadGameByIndex(BaseModel):
    """Request model for loading a game by date and index."""
    date: str
    game_index: int


class LoadGameRequest(BaseModel):
    """Request model for loading a game."""
    event_ticker: Optional[str] = None
    date: Optional[str] = None
    game_index: Optional[int] = None


@router.get("/available")
async def get_available_games(
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Get all available NBA games from Kalshi for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
    
    Returns:
        List of games with basic info (teams, date, market counts)
    """
    logger.info(f"Fetching available NBA games for date: {date}")
    
    try:
        client = KalshiClient()
        games = await client.get_nba_games_for_date(date)
        
        # Format response
        available_games = []
        for i, game in enumerate(games):
            available_games.append({
                "index": i,
                "away_team": game.get("away_team", ""),
                "home_team": game.get("home_team", ""),
                "event_ticker": game.get("event_ticker", ""),
                "title": game.get("title", ""),
                "game_date": game.get("game_date", date),
                "market_count": game.get("market_count", 0),
                "market_types": list(game.get("markets", {}).keys()),
            })
        
        return {
            "date": date,
            "game_count": len(available_games),
            "games": available_games,
        }
        
    except KalshiAuthError as e:
        logger.error(f"Kalshi authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Kalshi authentication failed")
    except KalshiAPIError as e:
        logger.error(f"Kalshi API error: {e}")
        raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch available games: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch available games")


@router.post("/load")
async def load_game(request: LoadGameRequest):
    """
    Load a game and all its markets from Kalshi.
    
    Accepts either:
    - event_ticker: Direct Kalshi event ticker
    - date + game_index: Select from available games for a date
    
    Returns:
        Complete game info with all markets
    """
    logger.info(f"Loading game: {request}")
    
    try:
        client = KalshiClient()
        
        # Determine which game to load
        if request.event_ticker:
            event_ticker = request.event_ticker
        elif request.date is not None and request.game_index is not None:
            # Get available games and select by index
            games = await client.get_nba_games_for_date(request.date)
            if request.game_index >= len(games):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid game index. Only {len(games)} games available."
                )
            event_ticker = games[request.game_index].get("event_ticker", "")
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either event_ticker or date+game_index"
            )
        
        # Parse ticker to get game info
        try:
            game_info = extract_game_info_from_kalshi_ticker(event_ticker)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid ticker: {e}")
        
        # Fetch event with markets from Kalshi
        try:
            event_response = await client.get_event(event_ticker, with_nested_markets=True)
            event = event_response.get("event", event_response)
        except KalshiNotFoundError:
            raise HTTPException(status_code=404, detail=f"Event not found: {event_ticker}")
        
        # Get all related markets (moneyline, spread, total)
        all_markets = await _fetch_all_game_markets(client, game_info, event_ticker)
        
        # Store in database
        game_id = await _store_game_in_database(game_info, event_ticker, event, all_markets)
        
        # Try to match to NBA game and fetch initial odds
        nba_game_id = None
        nba_match_status = "not_attempted"
        try:
            bdl_client = BallDontLieClient()
            nba_game = await bdl_client.match_kalshi_game(event_ticker)
            nba_game_id = nba_game.get("id")
            
            # Update game with NBA game ID
            supabase = get_supabase_client()
            supabase.table("games").update({"nba_game_id": nba_game_id}).eq("id", game_id).execute()
            
            nba_match_status = "matched"
            logger.info(f"Matched NBA game ID {nba_game_id} for {event_ticker}")
            
            # Fetch initial odds
            try:
                odds_data = await bdl_client.get_odds(game_ids=[nba_game_id])
                if odds_data:
                    await _store_odds_data(game_id, nba_game_id, odds_data)
                    logger.info(f"Stored initial odds for game {game_id}")
            except Exception as odds_error:
                logger.warning(f"Failed to fetch initial odds: {odds_error}")
            
            await bdl_client.close()
        except GameMatchError as e:
            nba_match_status = f"no_match: {str(e)}"
            logger.warning(f"Could not match NBA game: {e}")
        except BallDontLieAuthError as e:
            nba_match_status = "auth_error"
            logger.error(f"BallDontLie auth error: {e}")
        except Exception as e:
            nba_match_status = f"error: {str(e)}"
            logger.error(f"Error matching NBA game: {e}")
        
        return {
            "success": True,
            "game_id": game_id,
            "event_ticker": event_ticker,
            "away_team": game_info["away_team_abbr"],
            "home_team": game_info["home_team_abbr"],
            "game_date": game_info["date"],
            "title": event.get("title", ""),
            "market_count": len(all_markets),
            "markets": all_markets,
            "nba_game_id": nba_game_id,
            "nba_match_status": nba_match_status,
        }
        
    except HTTPException:
        raise
    except KalshiAuthError as e:
        logger.error(f"Kalshi authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Kalshi authentication failed")
    except KalshiAPIError as e:
        logger.error(f"Kalshi API error: {e}")
        raise HTTPException(status_code=502, detail=f"Kalshi API error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to load game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load game")


async def _fetch_all_game_markets(
    client: KalshiClient,
    game_info: dict,
    event_ticker: str,
) -> List[dict]:
    """
    Fetch all related markets for a game (moneyline, spread, total).
    
    Args:
        client: Kalshi client instance
        game_info: Parsed game info with date and teams
        event_ticker: Base event ticker
    
    Returns:
        List of all market data
    """
    all_markets = []
    
    # Get the date pattern for matching related events
    game_date = game_info["date"]  # YYYY-MM-DD
    away_team = game_info["away_team_abbr"]
    home_team = game_info["home_team_abbr"]
    
    # Try to fetch markets from each series
    series_tickers = [
        f"KXNBAGAME",
        f"KXNBASPREAD", 
        f"KXNBATOTAL",
    ]
    
    for series in series_tickers:
        try:
            response = await client.get_markets(series_ticker=series, status="open")
            markets = response.get("markets", [])
            
            # Filter markets for this game (matching teams and date pattern)
            for market in markets:
                ticker = market.get("ticker", "").upper()
                # Check if ticker contains both teams
                if away_team in ticker and home_team in ticker:
                    market_type = _determine_market_type(series, market)
                    all_markets.append({
                        "ticker": market.get("ticker"),
                        "title": market.get("title", ""),
                        "subtitle": market.get("subtitle", ""),
                        "market_type": market_type,
                        "status": market.get("status"),
                        "yes_bid": market.get("yes_bid"),
                        "yes_ask": market.get("yes_ask"),
                        "no_bid": market.get("no_bid"),
                        "no_ask": market.get("no_ask"),
                        "volume": market.get("volume"),
                        "open_interest": market.get("open_interest"),
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch {series} markets: {e}")
    
    return all_markets


def _determine_market_type(series: str, market: dict) -> str:
    """Determine the market type from series and market data."""
    if "SPREAD" in series:
        return "spread"
    elif "TOTAL" in series:
        return "total"
    else:
        # Check if it's home or away moneyline
        title = market.get("title", "").lower()
        if "win" in title:
            return "moneyline"
        return "moneyline"


async def _store_game_in_database(
    game_info: dict,
    event_ticker: str,
    event: dict,
    markets: List[dict],
) -> str:
    """
    Store game and markets in database.
    
    Returns:
        Game UUID
    """
    try:
        supabase = get_supabase_client()
        
        # Generate game ID
        game_id = str(uuid.uuid4())
        
        # Insert game record
        game_data = {
            "id": game_id,
            "kalshi_event_ticker": event_ticker,
            "kalshi_market_ticker_seed": event_ticker,
            "home_team": game_info["home_team_abbr"],
            "away_team": game_info["away_team_abbr"],
            "game_date": game_info["date"],
            "status": "scheduled",
            "is_active": True,
        }
        
        supabase.table("games").upsert(game_data).execute()
        
        # Insert market records
        for market in markets:
            market_data = {
                "id": str(uuid.uuid4()),
                "game_id": game_id,
                "ticker": market.get("ticker"),
                "market_type": market.get("market_type"),
                "status": market.get("status", "open"),
            }
            supabase.table("kalshi_markets").upsert(market_data).execute()
        
        logger.info(f"Stored game {game_id} with {len(markets)} markets")
        return game_id
        
    except Exception as e:
        logger.error(f"Failed to store game in database: {e}")
        # Return a temporary ID if database fails
        return str(uuid.uuid4())


async def _store_odds_data(game_id: str, nba_game_id: int, odds_data: List[dict]) -> None:
    """
    Store betting odds data in the database.
    
    Args:
        game_id: Internal game UUID
        nba_game_id: NBA game ID from balldontlie.io
        odds_data: List of odds objects from API
    """
    from datetime import datetime
    
    supabase = get_supabase_client()
    
    for odds in odds_data:
        for book in odds.get("sportsbooks", []):
            vendor = book.get("name", "unknown")
            
            odds_record = {
                "game_id": game_id,
                "nba_game_id": nba_game_id,
                "timestamp": datetime.utcnow().isoformat(),
                "vendor": vendor,
            }
            
            for line in book.get("odds", []):
                line_type = line.get("type", "")
                if line_type == "moneyline":
                    odds_record["moneyline_home"] = line.get("home_odds")
                    odds_record["moneyline_away"] = line.get("away_odds")
                elif line_type == "spread":
                    odds_record["spread_home_value"] = line.get("home_spread")
                    odds_record["spread_home_odds"] = line.get("home_odds")
                    odds_record["spread_away_value"] = line.get("away_spread")
                    odds_record["spread_away_odds"] = line.get("away_odds")
                elif line_type == "total":
                    odds_record["total_value"] = line.get("total")
                    odds_record["total_over_odds"] = line.get("over_odds")
                    odds_record["total_under_odds"] = line.get("under_odds")
            
            try:
                supabase.table("betting_odds").insert(odds_record).execute()
            except Exception as e:
                logger.warning(f"Failed to store odds for {vendor}: {e}")


@router.get("/{game_id}")
async def get_game(game_id: str):
    """
    Get game details by ID.

    Args:
        game_id: Game UUID.

    Returns:
        Game information with markets and current data.
    """
    logger.info(f"Getting game: {game_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Fetch game
        game_response = supabase.table("games").select("*").eq("id", game_id).execute()
        
        if not game_response.data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = game_response.data[0]
        
        # Fetch associated markets
        markets_response = supabase.table("kalshi_markets").select("*").eq("game_id", game_id).execute()
        markets = markets_response.data or []
        
        # Fetch latest orderbook data for each market
        for market in markets:
            orderbook_response = (
                supabase.table("orderbook_snapshots")
                .select("*")
                .eq("market_id", market["id"])
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            if orderbook_response.data:
                market["latest_orderbook"] = orderbook_response.data[0]
        
        # Fetch latest NBA live data (if available)
        nba_live_data = None
        nba_data_response = (
            supabase.table("nba_live_data")
            .select("*")
            .eq("game_id", game_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        if nba_data_response.data:
            nba_live_data = nba_data_response.data[0]
        
        # Fetch latest betting odds
        betting_odds = []
        odds_response = (
            supabase.table("betting_odds")
            .select("*")
            .eq("game_id", game_id)
            .order("timestamp", desc=True)
            .limit(10)
            .execute()
        )
        if odds_response.data:
            betting_odds = odds_response.data
        
        return {
            "game": game,
            "markets": markets,
            "nba_live_data": nba_live_data,
            "betting_odds": betting_odds,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve game")


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    """
    Delete a game and all associated data.

    Args:
        game_id: Game UUID.

    Returns:
        Success message.
    """
    logger.info(f"Deleting game: {game_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Check if game exists
        game_response = supabase.table("games").select("id").eq("id", game_id).execute()
        
        if not game_response.data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Delete game (CASCADE will handle related records)
        supabase.table("games").delete().eq("id", game_id).execute()
        
        logger.info(f"Deleted game: {game_id}")
        
        return {
            "success": True,
            "message": "Game deleted successfully",
            "game_id": game_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete game: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete game")


@router.get("/")
async def list_games(
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """
    List all games.

    Args:
        status: Optional status filter (scheduled, live, finished)
        is_active: Optional active status filter

    Returns:
        List of games with status.
    """
    logger.info("Listing all games")
    
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("games").select("*")
        
        if status:
            query = query.eq("status", status)
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        # Order by game date descending
        query = query.order("game_date", desc=True)
        
        response = query.execute()
        games = response.data or []
        
        # Get market counts for each game
        for game in games:
            markets_response = (
                supabase.table("kalshi_markets")
                .select("id", count="exact")
                .eq("game_id", game["id"])
                .execute()
            )
            game["market_count"] = markets_response.count or 0
        
        return {
            "game_count": len(games),
            "games": games,
        }
        
    except Exception as e:
        logger.error(f"Failed to list games: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list games")


@router.post("/{game_id}/refresh-nba")
async def refresh_nba_data(game_id: str):
    """
    Fetch latest NBA data for a game from balldontlie.io.
    
    Args:
        game_id: Game UUID.
    
    Returns:
        Fresh NBA game data and status.
    """
    logger.info(f"Refreshing NBA data for game: {game_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Fetch game
        game_response = supabase.table("games").select("*").eq("id", game_id).execute()
        
        if not game_response.data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = game_response.data[0]
        nba_game_id = game.get("nba_game_id")
        
        if not nba_game_id:
            raise HTTPException(
                status_code=400,
                detail="Game has no NBA game ID. Try re-matching the game first."
            )
        
        # Fetch fresh data from balldontlie.io
        bdl_client = BallDontLieClient()
        try:
            nba_game = await bdl_client.get_game(nba_game_id)
            
            # Store live data if game has scores
            if nba_game.get("home_team_score") is not None:
                from datetime import datetime
                
                live_data = {
                    "game_id": game_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "period": nba_game.get("period", 0),
                    "time_remaining": nba_game.get("time", ""),
                    "home_score": nba_game.get("home_team_score", 0),
                    "away_score": nba_game.get("visitor_team_score", 0),
                    "game_status": nba_game.get("status", "unknown"),
                    "raw_data": nba_game,
                }
                
                supabase.table("nba_live_data").insert(live_data).execute()
                
                # Update game status if changed
                game_status = nba_game.get("status", "").lower()
                if "final" in game_status:
                    supabase.table("games").update({"status": "finished"}).eq("id", game_id).execute()
                elif nba_game.get("period", 0) > 0:
                    supabase.table("games").update({"status": "live"}).eq("id", game_id).execute()
            
            await bdl_client.close()
            
            return {
                "success": True,
                "game_id": game_id,
                "nba_game_id": nba_game_id,
                "nba_data": nba_game,
            }
            
        except Exception as e:
            await bdl_client.close()
            raise HTTPException(status_code=502, detail=f"Failed to fetch NBA data: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh NBA data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh NBA data")


@router.post("/{game_id}/refresh-odds")
async def refresh_odds(game_id: str):
    """
    Fetch latest betting odds for a game from balldontlie.io.
    
    Args:
        game_id: Game UUID.
    
    Returns:
        Fresh betting odds data.
    """
    logger.info(f"Refreshing odds for game: {game_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Fetch game
        game_response = supabase.table("games").select("*").eq("id", game_id).execute()
        
        if not game_response.data:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = game_response.data[0]
        nba_game_id = game.get("nba_game_id")
        
        if not nba_game_id:
            raise HTTPException(
                status_code=400,
                detail="Game has no NBA game ID. Try re-matching the game first."
            )
        
        # Fetch fresh odds from balldontlie.io
        bdl_client = BallDontLieClient()
        try:
            odds_data = await bdl_client.get_odds(game_ids=[nba_game_id])
            
            if odds_data:
                await _store_odds_data(game_id, nba_game_id, odds_data)
            
            await bdl_client.close()
            
            return {
                "success": True,
                "game_id": game_id,
                "nba_game_id": nba_game_id,
                "odds_count": len(odds_data),
                "odds_data": odds_data,
            }
            
        except Exception as e:
            await bdl_client.close()
            raise HTTPException(status_code=502, detail=f"Failed to fetch odds: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh odds: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh odds")

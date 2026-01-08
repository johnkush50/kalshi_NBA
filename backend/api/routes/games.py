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
from backend.utils.ticker_parser import extract_game_info_from_kalshi_ticker
from backend.config.supabase import get_supabase_client

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
        
        return {
            "game": game,
            "markets": markets,
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

"""
Database helper functions for storing and retrieving data.

Provides async functions for common database operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from backend.config.supabase import get_supabase_client

logger = logging.getLogger(__name__)


# =============================================================================
# Games Table
# =============================================================================

async def create_game(
    kalshi_event_ticker: str,
    kalshi_market_ticker_seed: str,
    home_team: str,
    away_team: str,
    game_date: datetime,
    nba_game_id: int = None,
    home_team_id: int = None,
    away_team_id: int = None
) -> Dict[str, Any]:
    """
    Create a new game record.
    
    Returns:
        Created game record
    """
    client = get_supabase_client()
    
    data = {
        "kalshi_event_ticker": kalshi_event_ticker,
        "kalshi_market_ticker_seed": kalshi_market_ticker_seed,
        "home_team": home_team,
        "away_team": away_team,
        "game_date": game_date.isoformat() if isinstance(game_date, datetime) else game_date,
        "status": "scheduled",
        "is_active": True
    }
    
    if nba_game_id:
        data["nba_game_id"] = nba_game_id
    if home_team_id:
        data["home_team_id"] = home_team_id
    if away_team_id:
        data["away_team_id"] = away_team_id
    
    result = client.table("games").insert(data).execute()
    
    if result.data:
        logger.info(f"Created game: {kalshi_event_ticker}")
        return result.data[0]
    
    raise Exception("Failed to create game record")


async def get_game_by_id(game_id: str) -> Optional[Dict[str, Any]]:
    """Get a game by its UUID."""
    client = get_supabase_client()
    result = client.table("games").select("*").eq("id", game_id).execute()
    return result.data[0] if result.data else None


async def get_game_by_event_ticker(event_ticker: str) -> Optional[Dict[str, Any]]:
    """Get a game by its Kalshi event ticker."""
    client = get_supabase_client()
    result = client.table("games").select("*").eq("kalshi_event_ticker", event_ticker).execute()
    return result.data[0] if result.data else None


async def get_active_games() -> List[Dict[str, Any]]:
    """Get all active games."""
    client = get_supabase_client()
    result = client.table("games").select("*").eq("is_active", True).execute()
    return result.data or []


async def update_game(game_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a game record."""
    client = get_supabase_client()
    result = client.table("games").update(updates).eq("id", game_id).execute()
    return result.data[0] if result.data else None


async def delete_game(game_id: str) -> bool:
    """Delete a game and all associated data (cascades)."""
    client = get_supabase_client()
    result = client.table("games").delete().eq("id", game_id).execute()
    return len(result.data) > 0 if result.data else False


# =============================================================================
# Kalshi Markets Table
# =============================================================================

async def create_kalshi_market(
    game_id: str,
    ticker: str,
    market_type: str,
    strike_value: float = None,
    side: str = None,
    status: str = None
) -> Dict[str, Any]:
    """Create a new Kalshi market record."""
    client = get_supabase_client()
    
    data = {
        "game_id": game_id,
        "ticker": ticker,
        "market_type": market_type
    }
    
    if strike_value is not None:
        data["strike_value"] = strike_value
    if side:
        data["side"] = side
    if status:
        data["status"] = status
    
    result = client.table("kalshi_markets").insert(data).execute()
    
    if result.data:
        logger.debug(f"Created market: {ticker}")
        return result.data[0]
    
    raise Exception(f"Failed to create market record: {ticker}")


async def get_markets_for_game(game_id: str) -> List[Dict[str, Any]]:
    """Get all markets for a game."""
    client = get_supabase_client()
    result = client.table("kalshi_markets").select("*").eq("game_id", game_id).execute()
    return result.data or []


async def get_market_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """Get a market by its ticker."""
    client = get_supabase_client()
    result = client.table("kalshi_markets").select("*").eq("ticker", ticker).execute()
    return result.data[0] if result.data else None


# =============================================================================
# NBA Live Data Table
# =============================================================================

async def store_nba_live_data(
    game_id: str,
    period: int,
    time_remaining: str,
    home_score: int,
    away_score: int,
    game_status: str,
    raw_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Store NBA live game data."""
    client = get_supabase_client()
    
    data = {
        "game_id": game_id,
        "timestamp": datetime.utcnow().isoformat(),
        "period": period,
        "time_remaining": time_remaining,
        "home_score": home_score,
        "away_score": away_score,
        "game_status": game_status,
        "raw_data": raw_data
    }
    
    result = client.table("nba_live_data").insert(data).execute()
    return result.data[0] if result.data else None


async def get_latest_nba_data(game_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent NBA data for a game."""
    client = get_supabase_client()
    result = (
        client.table("nba_live_data")
        .select("*")
        .eq("game_id", game_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# =============================================================================
# Betting Odds Table
# =============================================================================

async def store_betting_odds(
    game_id: str,
    nba_game_id: int,
    vendor: str,
    moneyline_home: int = None,
    moneyline_away: int = None,
    spread_home_value: float = None,
    spread_home_odds: int = None,
    spread_away_value: float = None,
    spread_away_odds: int = None,
    total_value: float = None,
    total_over_odds: int = None,
    total_under_odds: int = None
) -> Dict[str, Any]:
    """Store betting odds from a sportsbook."""
    client = get_supabase_client()
    
    data = {
        "game_id": game_id,
        "nba_game_id": nba_game_id,
        "timestamp": datetime.utcnow().isoformat(),
        "vendor": vendor,
        "moneyline_home": moneyline_home,
        "moneyline_away": moneyline_away,
        "spread_home_value": spread_home_value,
        "spread_home_odds": spread_home_odds,
        "spread_away_value": spread_away_value,
        "spread_away_odds": spread_away_odds,
        "total_value": total_value,
        "total_over_odds": total_over_odds,
        "total_under_odds": total_under_odds
    }
    
    result = client.table("betting_odds").insert(data).execute()
    return result.data[0] if result.data else None


async def get_latest_odds(game_id: str, vendor: str = None) -> List[Dict[str, Any]]:
    """Get the latest odds for a game, optionally filtered by vendor."""
    client = get_supabase_client()
    query = client.table("betting_odds").select("*").eq("game_id", game_id)
    
    if vendor:
        query = query.eq("vendor", vendor)
    
    result = query.order("timestamp", desc=True).limit(10).execute()
    return result.data or []


# =============================================================================
# Orderbook Snapshots Table
# =============================================================================

async def store_orderbook_snapshot(
    market_id: str,
    yes_bid: float = None,
    yes_ask: float = None,
    no_bid: float = None,
    no_ask: float = None,
    yes_bid_size: int = None,
    yes_ask_size: int = None,
    no_bid_size: int = None,
    no_ask_size: int = None
) -> Dict[str, Any]:
    """Store an orderbook snapshot."""
    client = get_supabase_client()
    
    data = {
        "market_id": market_id,
        "timestamp": datetime.utcnow().isoformat(),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "yes_bid_size": yes_bid_size,
        "yes_ask_size": yes_ask_size,
        "no_bid_size": no_bid_size,
        "no_ask_size": no_ask_size
    }
    
    result = client.table("orderbook_snapshots").insert(data).execute()
    return result.data[0] if result.data else None


async def get_latest_orderbook(market_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent orderbook snapshot for a market."""
    client = get_supabase_client()
    result = (
        client.table("orderbook_snapshots")
        .select("*")
        .eq("market_id", market_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# =============================================================================
# Strategies Table
# =============================================================================

async def get_strategy_by_id(strategy_id: str) -> Optional[Dict[str, Any]]:
    """Get a strategy by its UUID."""
    client = get_supabase_client()
    try:
        result = client.table("strategies").select("id").eq("id", strategy_id).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


# =============================================================================
# Simulated Orders Table
# =============================================================================

async def create_simulated_order(order_data: dict) -> dict:
    """Create a new simulated order in the database."""
    client = get_supabase_client()
    result = client.table("simulated_orders").insert(order_data).execute()
    
    if result.data:
        logger.debug(f"Created simulated order: {order_data.get('id')}")
        return result.data[0]
    return order_data


async def get_simulated_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Get a simulated order by ID."""
    client = get_supabase_client()
    result = client.table("simulated_orders").select("*").eq("id", order_id).execute()
    
    if result.data:
        return result.data[0]
    return None


async def get_orders_by_strategy(strategy_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get orders for a strategy."""
    client = get_supabase_client()
    result = client.table("simulated_orders")\
        .select("*")\
        .eq("strategy_id", strategy_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data or []


async def get_orders_by_game(game_id: str) -> List[Dict[str, Any]]:
    """Get orders for a game."""
    client = get_supabase_client()
    result = client.table("simulated_orders")\
        .select("*")\
        .eq("game_id", game_id)\
        .order("created_at", desc=True)\
        .execute()
    
    return result.data or []


async def get_recent_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent orders across all strategies."""
    client = get_supabase_client()
    result = client.table("simulated_orders")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data or []


# =============================================================================
# Positions Table
# =============================================================================

async def upsert_position(position_data: dict) -> dict:
    """Create or update a position."""
    client = get_supabase_client()
    result = client.table("positions")\
        .upsert(position_data, on_conflict="id")\
        .execute()
    
    if result.data:
        logger.debug(f"Upserted position: {position_data.get('market_ticker')}")
        return result.data[0]
    return position_data


async def get_position(position_id: str) -> Optional[Dict[str, Any]]:
    """Get a position by ID."""
    client = get_supabase_client()
    result = client.table("positions").select("*").eq("id", position_id).execute()
    
    if result.data:
        return result.data[0]
    return None


async def get_position_by_ticker(market_ticker: str) -> Optional[Dict[str, Any]]:
    """Get a position by market ticker."""
    client = get_supabase_client()
    result = client.table("positions")\
        .select("*")\
        .eq("market_ticker", market_ticker)\
        .eq("is_open", True)\
        .execute()
    
    if result.data:
        return result.data[0]
    return None


async def get_positions_by_game(game_id: str) -> List[Dict[str, Any]]:
    """Get all positions for a game."""
    client = get_supabase_client()
    result = client.table("positions")\
        .select("*")\
        .eq("game_id", game_id)\
        .execute()
    
    return result.data or []


async def get_open_positions() -> List[Dict[str, Any]]:
    """Get all open positions."""
    client = get_supabase_client()
    result = client.table("positions")\
        .select("*")\
        .eq("is_open", True)\
        .gt("quantity", 0)\
        .execute()
    
    return result.data or []


async def close_position(position_id: str, realized_pnl: float = 0.0) -> Optional[Dict[str, Any]]:
    """Close a position."""
    client = get_supabase_client()
    result = client.table("positions")\
        .update({
            "is_open": False,
            "closed_at": datetime.utcnow().isoformat(),
            "realized_pnl": realized_pnl
        })\
        .eq("id", position_id)\
        .execute()
    
    if result.data:
        logger.debug(f"Closed position: {position_id}")
        return result.data[0]
    return None

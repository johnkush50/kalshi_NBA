"""
API routes for the Data Aggregator.

Provides endpoints for:
- Loading/unloading games into the aggregator
- Retrieving unified game state
- Manual data refresh triggers
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging

from backend.engine.aggregator import get_aggregator
from backend.models.game_state import GameState

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/states", response_model=Dict[str, Any])
async def get_all_states():
    """
    Get all active game states.
    
    Returns a dictionary of game_id -> GameState for all loaded games.
    """
    aggregator = get_aggregator()
    states = aggregator.get_all_game_states()
    
    # Convert to dict for JSON serialization
    result = {}
    for game_id, state in states.items():
        result[game_id] = state.dict()
    
    return {
        "count": len(result),
        "games": result
    }


@router.get("/state/{game_id}")
async def get_state(game_id: str):
    """
    Get unified GameState for a specific game.
    
    Args:
        game_id: UUID of the game
        
    Returns:
        GameState object with all aggregated data
    """
    aggregator = get_aggregator()
    state = aggregator.get_game_state(game_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not loaded: {game_id}"
        )
    
    return state.dict()


@router.post("/load/{game_id}")
async def load_game(game_id: str):
    """
    Load a game into the aggregator.
    
    This initializes tracking for the game, fetching initial data
    from Kalshi, NBA, and betting odds sources.
    
    Args:
        game_id: UUID of the game (must exist in database)
        
    Returns:
        Initial GameState after loading
    """
    aggregator = get_aggregator()
    
    # Check if already loaded
    existing = aggregator.get_game_state(game_id)
    if existing:
        return {
            "status": "already_loaded",
            "message": f"Game {game_id} is already loaded",
            "game_state": existing.dict()
        }
    
    # Load the game
    state = await aggregator.load_game(game_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not found in database: {game_id}"
        )
    
    return {
        "status": "loaded",
        "message": f"Game loaded: {state.away_team} @ {state.home_team}",
        "game_state": state.dict()
    }


@router.post("/unload/{game_id}")
async def unload_game(game_id: str):
    """
    Stop tracking a game and remove from aggregator.
    
    Args:
        game_id: UUID of the game
        
    Returns:
        Confirmation message
    """
    aggregator = get_aggregator()
    
    success = await aggregator.unload_game(game_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not loaded: {game_id}"
        )
    
    return {
        "status": "unloaded",
        "message": f"Game {game_id} unloaded successfully"
    }


@router.post("/refresh/{game_id}/kalshi")
async def refresh_kalshi(game_id: str):
    """
    Manually refresh Kalshi orderbook data for a game.
    
    Args:
        game_id: UUID of the game
        
    Returns:
        Updated GameState
    """
    aggregator = get_aggregator()
    
    state = aggregator.get_game_state(game_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not loaded: {game_id}"
        )
    
    await aggregator._refresh_kalshi_orderbooks(game_id)
    
    # Get updated state
    state = aggregator.get_game_state(game_id)
    
    return {
        "status": "refreshed",
        "message": "Kalshi orderbook data refreshed",
        "game_state": state.dict() if state else None
    }


@router.post("/refresh/{game_id}/nba")
async def refresh_nba(game_id: str):
    """
    Manually refresh NBA live data for a game.
    
    Args:
        game_id: UUID of the game
        
    Returns:
        Updated GameState
    """
    aggregator = get_aggregator()
    
    state = aggregator.get_game_state(game_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not loaded: {game_id}"
        )
    
    if not state.has_nba_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game has no NBA data linked"
        )
    
    await aggregator._refresh_nba_data(game_id)
    
    # Get updated state
    state = aggregator.get_game_state(game_id)
    
    return {
        "status": "refreshed",
        "message": "NBA live data refreshed",
        "game_state": state.dict() if state else None
    }


@router.post("/refresh/{game_id}/odds")
async def refresh_odds(game_id: str):
    """
    Manually refresh betting odds for a game.
    
    Args:
        game_id: UUID of the game
        
    Returns:
        Updated GameState
    """
    aggregator = get_aggregator()
    
    state = aggregator.get_game_state(game_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game not loaded: {game_id}"
        )
    
    if not state.has_nba_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game has no NBA data linked"
        )
    
    await aggregator._refresh_odds(game_id)
    
    # Get updated state
    state = aggregator.get_game_state(game_id)
    
    return {
        "status": "refreshed",
        "message": "Betting odds refreshed",
        "num_sportsbooks": len(state.odds) if state else 0,
        "game_state": state.dict() if state else None
    }


@router.get("/game-ids")
async def get_game_ids():
    """
    Get list of all loaded game IDs.
    
    Returns:
        List of game UUIDs currently being tracked
    """
    aggregator = get_aggregator()
    game_ids = aggregator.get_game_ids()
    
    return {
        "count": len(game_ids),
        "game_ids": game_ids
    }

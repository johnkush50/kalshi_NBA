"""
Strategy Management API Endpoints.

Provides endpoints for:
- Loading/unloading strategies
- Enabling/disabling strategies
- Updating strategy configuration
- Viewing strategy status and signals
- Manual signal generation
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from backend.engine.strategy_engine import (
    get_strategy_engine, 
    StrategyEngine,
    STRATEGY_REGISTRY
)
from backend.engine.aggregator import get_aggregator

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class LoadStrategyRequest(BaseModel):
    """Request to load a strategy."""
    strategy_type: str
    strategy_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enable: bool = False


class UpdateConfigRequest(BaseModel):
    """Request to update strategy configuration."""
    config: Dict[str, Any]


class StrategyResponse(BaseModel):
    """Strategy information response."""
    strategy_id: str
    strategy_type: str
    strategy_name: str
    is_enabled: bool
    config: Dict[str, Any]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/types")
async def list_strategy_types():
    """List all available strategy types."""
    types = []
    for type_name, strategy_class in STRATEGY_REGISTRY.items():
        types.append({
            "type": type_name,
            "name": strategy_class.STRATEGY_NAME,
            "description": strategy_class.STRATEGY_DESCRIPTION,
            "default_config": strategy_class(strategy_id="temp").get_default_config()
        })
    return {"strategy_types": types}


@router.get("/")
async def list_strategies():
    """List all loaded strategies."""
    engine = get_strategy_engine()
    strategies = []
    
    for strategy_id, strategy in engine.get_all_strategies().items():
        strategies.append({
            "strategy_id": strategy_id,
            "strategy_type": strategy.STRATEGY_TYPE,
            "strategy_name": strategy.STRATEGY_NAME,
            "is_enabled": strategy.is_enabled,
            "config": strategy.config
        })
    
    return {"strategies": strategies, "count": len(strategies)}


@router.post("/load")
async def load_strategy(request: LoadStrategyRequest):
    """Load a new strategy instance."""
    engine = get_strategy_engine()
    
    try:
        strategy = await engine.load_strategy(
            strategy_type=request.strategy_type,
            strategy_id=request.strategy_id,
            config=request.config,
            enable=request.enable
        )
        
        return {
            "status": "loaded",
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.STRATEGY_NAME,
            "is_enabled": strategy.is_enabled,
            "config": strategy.config
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{strategy_id}")
async def unload_strategy(strategy_id: str):
    """Unload a strategy."""
    engine = get_strategy_engine()
    
    if strategy_id not in engine.get_all_strategies():
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    await engine.unload_strategy(strategy_id)
    
    return {"status": "unloaded", "strategy_id": strategy_id}


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get strategy details."""
    engine = get_strategy_engine()
    strategy = engine.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    return {
        "strategy_id": strategy.strategy_id,
        "strategy_type": strategy.STRATEGY_TYPE,
        "strategy_name": strategy.STRATEGY_NAME,
        "is_enabled": strategy.is_enabled,
        "config": strategy.config,
        "recent_signals": [s.model_dump() for s in strategy.get_signal_history()[-10:]]
    }


@router.post("/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """Enable a strategy."""
    engine = get_strategy_engine()
    
    if not await engine.enable_strategy(strategy_id):
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    return {"status": "enabled", "strategy_id": strategy_id}


@router.post("/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """Disable a strategy."""
    engine = get_strategy_engine()
    
    if not await engine.disable_strategy(strategy_id):
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    return {"status": "disabled", "strategy_id": strategy_id}


@router.put("/{strategy_id}/config")
async def update_strategy_config(strategy_id: str, request: UpdateConfigRequest):
    """Update strategy configuration."""
    engine = get_strategy_engine()
    
    if not await engine.update_strategy_config(strategy_id, request.config):
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    strategy = engine.get_strategy(strategy_id)
    return {
        "status": "updated",
        "strategy_id": strategy_id,
        "config": strategy.config
    }


@router.post("/{strategy_id}/evaluate")
async def evaluate_strategy(strategy_id: str, game_id: str, debug: bool = False):
    """
    Manually run a strategy evaluation on a specific game.
    
    Returns any generated signals.
    """
    engine = get_strategy_engine()
    strategy = engine.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    aggregator = get_aggregator()
    game_state = aggregator.get_game_state(game_id)
    
    if not game_state:
        raise HTTPException(status_code=404, detail=f"Game not loaded: {game_id}")
    
    # Debug info
    debug_info = {}
    if debug:
        debug_info["config"] = strategy.config
        debug_info["consensus"] = {
            "exists": game_state.consensus is not None,
            "home_prob": float(game_state.consensus.home_win_probability) if game_state.consensus and game_state.consensus.home_win_probability else None,
            "away_prob": float(game_state.consensus.away_win_probability) if game_state.consensus and game_state.consensus.away_win_probability else None,
            "num_sportsbooks": game_state.consensus.num_sportsbooks if game_state.consensus else 0,
        }
        debug_info["markets"] = []
        for ticker, market in game_state.markets.items():
            market_debug = {
                "ticker": ticker,
                "market_type": market.market_type,
                "has_orderbook": market.orderbook is not None,
                "mid_price": float(market.orderbook.mid_price) if market.orderbook and market.orderbook.mid_price else None,
                "yes_bid": float(market.orderbook.yes_bid) if market.orderbook and market.orderbook.yes_bid else None,
                "yes_ask": float(market.orderbook.yes_ask) if market.orderbook and market.orderbook.yes_ask else None,
            }
            debug_info["markets"].append(market_debug)
    
    # Temporarily enable for evaluation if disabled
    was_enabled = strategy.is_enabled
    if not was_enabled:
        strategy.enable()
    
    try:
        signals = await strategy.evaluate(game_state)
        result = {
            "strategy_id": strategy_id,
            "game_id": game_id,
            "signals_generated": len(signals),
            "signals": [s.model_dump() for s in signals]
        }
        if debug:
            result["debug"] = debug_info
        return result
    except Exception as e:
        logger.error(f"Error evaluating strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")
    finally:
        if not was_enabled:
            strategy.disable()


@router.post("/evaluate-all")
async def evaluate_all_strategies():
    """
    Run all enabled strategies on all loaded games.
    
    Returns all generated signals.
    """
    engine = get_strategy_engine()
    
    results = await engine.evaluate_all_games()
    
    total_signals = sum(len(signals) for signals in results.values())
    
    return {
        "games_evaluated": len(results),
        "total_signals": total_signals,
        "signals_by_game": {
            game_id: [s.model_dump() for s in signals]
            for game_id, signals in results.items()
        }
    }


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(strategy_id: str, limit: int = 20):
    """Get recent signals from a strategy."""
    engine = get_strategy_engine()
    strategy = engine.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    signals = strategy.get_signal_history()
    
    return {
        "strategy_id": strategy_id,
        "signal_count": len(signals),
        "signals": [s.model_dump() for s in signals[-limit:]]
    }


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str):
    """
    Get strategy performance metrics.
    
    Returns:
        dict: Performance metrics (placeholder - to be implemented with execution engine).
    """
    engine = get_strategy_engine()
    strategy = engine.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    # Placeholder - will be implemented with order execution engine
    return {
        "strategy_id": strategy_id,
        "strategy_name": strategy.STRATEGY_NAME,
        "signals_generated": len(strategy.get_signal_history()),
        "message": "Full performance metrics will be available after order execution is implemented"
    }

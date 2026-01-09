"""
Order Execution API Endpoints.

Provides endpoints for:
- Manual order execution
- Viewing orders and positions
- Execution statistics
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import uuid

from backend.engine.execution import get_execution_engine
from backend.engine.strategy_engine import get_strategy_engine
from backend.engine.aggregator import get_aggregator
from backend.models.order import TradeSignal, OrderSide
from backend.database import helpers as db

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class ManualOrderRequest(BaseModel):
    """Request for manual order placement."""
    game_id: str
    market_ticker: str
    side: str  # "yes" or "no"
    quantity: int
    reason: Optional[str] = "Manual order"


class ExecuteSignalRequest(BaseModel):
    """Request to execute a specific signal."""
    strategy_id: str
    market_ticker: str
    side: str
    quantity: int
    confidence: float = 0.5
    reason: str = "Manual signal execution"


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/stats")
async def get_execution_stats():
    """Get execution engine statistics."""
    engine = get_execution_engine()
    return engine.get_stats()


@router.get("/positions")
async def get_positions():
    """Get all current positions."""
    engine = get_execution_engine()
    positions = engine.get_all_positions()
    
    return {
        "count": len(positions),
        "positions": {
            ticker: {
                "id": pos.id,
                "game_id": pos.game_id,
                "side": pos.side.value,
                "quantity": pos.quantity,
                "avg_entry_price": float(pos.avg_entry_price),
                "total_cost": float(pos.total_cost),
                "unrealized_pnl": float(pos.unrealized_pnl),
                "realized_pnl": float(pos.realized_pnl),
                "is_open": pos.is_open
            }
            for ticker, pos in positions.items()
        }
    }


@router.get("/positions/open")
async def get_open_positions():
    """Get only open positions with quantity > 0."""
    engine = get_execution_engine()
    positions = engine.get_open_positions()
    
    return {
        "count": len(positions),
        "positions": [
            {
                "market_ticker": pos.market_ticker,
                "side": pos.side.value,
                "quantity": pos.quantity,
                "avg_entry_price": float(pos.avg_entry_price),
                "total_cost": float(pos.total_cost)
            }
            for pos in positions
        ]
    }


@router.get("/orders")
async def get_recent_orders(limit: int = 50):
    """Get recent orders from database."""
    orders = await db.get_recent_orders(limit)
    
    return {
        "count": len(orders),
        "orders": orders
    }


@router.get("/orders/game/{game_id}")
async def get_orders_for_game(game_id: str):
    """Get orders for a specific game."""
    orders = await db.get_orders_by_game(game_id)
    
    return {
        "game_id": game_id,
        "count": len(orders),
        "orders": orders
    }


@router.get("/orders/strategy/{strategy_id}")
async def get_orders_for_strategy(strategy_id: str, limit: int = 50):
    """Get orders for a specific strategy."""
    orders = await db.get_orders_by_strategy(strategy_id, limit)
    
    return {
        "strategy_id": strategy_id,
        "count": len(orders),
        "orders": orders
    }


@router.post("/execute/manual")
async def execute_manual_order(request: ManualOrderRequest):
    """
    Place a manual order (not from a strategy signal).
    
    Useful for testing and manual interventions.
    """
    engine = get_execution_engine()
    
    # Create a manual signal with a generated UUID for manual orders
    manual_strategy_id = str(uuid.uuid4())
    
    signal = TradeSignal(
        strategy_id=manual_strategy_id,
        strategy_name="Manual Order",
        market_ticker=request.market_ticker,
        side=OrderSide(request.side),
        quantity=request.quantity,
        confidence=1.0,
        reason=request.reason
    )
    
    # Execute
    result = await engine.execute_signal(signal, request.game_id)
    
    if result.success:
        return {
            "status": "filled",
            "order_id": str(result.order.id),
            "fill_price": float(result.order.filled_price) if result.order.filled_price else None,
            "quantity": result.order.quantity,
            "position": {
                "quantity": result.new_position.quantity,
                "avg_price": float(result.new_position.avg_entry_price)
            } if result.new_position else None
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Order rejected: {result.error}"
        )


@router.post("/execute/signal")
async def execute_signal_manually(request: ExecuteSignalRequest):
    """
    Execute a trading signal manually.
    
    This simulates what would happen when a strategy generates a signal.
    """
    engine = get_execution_engine()
    aggregator = get_aggregator()
    
    # Find the game for this market
    game_id = None
    for gid, game_state in aggregator.get_all_game_states().items():
        if request.market_ticker in game_state.markets:
            game_id = gid
            break
    
    if not game_id:
        raise HTTPException(
            status_code=404,
            detail=f"Market not found in any loaded game: {request.market_ticker}"
        )
    
    # Create signal
    signal = TradeSignal(
        strategy_id=request.strategy_id,
        strategy_name="Manual Signal",
        market_ticker=request.market_ticker,
        side=OrderSide(request.side),
        quantity=request.quantity,
        confidence=request.confidence,
        reason=request.reason
    )
    
    # Execute
    result = await engine.execute_signal(signal, game_id)
    
    return {
        "success": result.success,
        "order": {
            "id": str(result.order.id),
            "market_ticker": result.order.market_ticker,
            "side": result.order.side.value,
            "quantity": result.order.quantity,
            "status": result.order.status.value,
            "filled_price": float(result.order.filled_price) if result.order.filled_price else None
        } if result.order else None,
        "error": result.error,
        "position": {
            "market_ticker": result.new_position.market_ticker,
            "side": result.new_position.side.value,
            "quantity": result.new_position.quantity,
            "avg_entry_price": float(result.new_position.avg_entry_price)
        } if result.new_position else None
    }


@router.post("/execute/strategy/{strategy_id}")
async def execute_strategy_signals(strategy_id: str, game_id: str):
    """
    Run a strategy and immediately execute any signals generated.
    
    This is a convenience endpoint that combines evaluation + execution.
    """
    strategy_engine = get_strategy_engine()
    execution_engine = get_execution_engine()
    aggregator = get_aggregator()
    
    # Get strategy
    strategy = strategy_engine.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy not found: {strategy_id}")
    
    # Get game state
    game_state = aggregator.get_game_state(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail=f"Game not loaded: {game_id}")
    
    # Evaluate strategy
    signals = await strategy.evaluate(game_state)
    
    if not signals:
        return {
            "signals_generated": 0,
            "orders_executed": 0,
            "message": "No signals generated"
        }
    
    # Execute signals
    results = await execution_engine.execute_signals(signals, game_id)
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    return {
        "signals_generated": len(signals),
        "orders_executed": len(successful),
        "orders_rejected": len(failed),
        "orders": [
            {
                "order_id": str(r.order.id),
                "market": r.order.market_ticker,
                "side": r.order.side.value,
                "quantity": r.order.quantity,
                "fill_price": float(r.order.filled_price) if r.order.filled_price else None,
                "status": r.order.status.value
            }
            for r in results if r.order
        ],
        "rejections": [r.error for r in failed]
    }

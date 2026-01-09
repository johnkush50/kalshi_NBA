"""
Risk Management API Endpoints.

Provides endpoints for:
- Viewing risk status and limits
- Configuring risk limits
- Enabling/disabling risk management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
import logging

from backend.engine.risk_manager import get_risk_manager, RiskLimitType

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request Models
# =============================================================================

class SetLimitRequest(BaseModel):
    """Request to set a risk limit."""
    limit_type: str
    value: float


class BulkLimitsRequest(BaseModel):
    """Request to set multiple limits."""
    limits: Dict[str, float]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status")
async def get_risk_status():
    """Get current risk management status."""
    risk_manager = get_risk_manager()
    return risk_manager.get_status()


@router.get("/limits")
async def get_risk_limits():
    """Get all risk limit values."""
    risk_manager = get_risk_manager()
    return {
        "limits": risk_manager.get_all_limits(),
        "enabled": risk_manager.is_enabled()
    }


@router.put("/limits")
async def set_risk_limit(request: SetLimitRequest):
    """Set a specific risk limit."""
    risk_manager = get_risk_manager()
    
    # Validate limit type
    try:
        limit_type = RiskLimitType(request.limit_type)
    except ValueError:
        valid_types = [lt.value for lt in RiskLimitType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid limit type. Valid types: {valid_types}"
        )
    
    # Validate value
    if request.value < 0:
        raise HTTPException(
            status_code=400,
            detail="Limit value must be non-negative"
        )
    
    risk_manager.set_limit(limit_type, request.value)
    
    return {
        "status": "updated",
        "limit_type": request.limit_type,
        "value": request.value
    }


@router.put("/limits/bulk")
async def set_bulk_limits(request: BulkLimitsRequest):
    """Set multiple risk limits at once."""
    risk_manager = get_risk_manager()
    updated = []
    errors = []
    
    for limit_type_str, value in request.limits.items():
        try:
            limit_type = RiskLimitType(limit_type_str)
            risk_manager.set_limit(limit_type, value)
            updated.append(limit_type_str)
        except ValueError:
            errors.append(f"Invalid limit type: {limit_type_str}")
    
    return {
        "updated": updated,
        "errors": errors
    }


@router.post("/enable")
async def enable_risk_management():
    """Enable risk management."""
    risk_manager = get_risk_manager()
    risk_manager.enable()
    return {"status": "enabled"}


@router.post("/disable")
async def disable_risk_management():
    """
    Disable risk management.
    
    WARNING: This removes all risk controls. Use with caution!
    """
    risk_manager = get_risk_manager()
    risk_manager.disable()
    return {
        "status": "disabled",
        "warning": "All risk controls are now disabled!"
    }


@router.post("/reset")
async def reset_risk_counters():
    """Reset all risk tracking counters."""
    risk_manager = get_risk_manager()
    risk_manager.reset_all()
    return {"status": "reset", "message": "All risk counters have been reset"}


@router.get("/check")
async def check_hypothetical_order(
    market_ticker: str,
    game_id: str,
    side: str,
    quantity: int
):
    """
    Check if a hypothetical order would pass risk checks.
    
    Useful for testing without actually placing an order.
    """
    from backend.models.order import SimulatedOrder, OrderSide, OrderType, OrderStatus
    from backend.engine.execution import get_execution_engine
    from datetime import datetime
    import uuid
    
    risk_manager = get_risk_manager()
    execution_engine = get_execution_engine()
    
    # Validate side
    try:
        order_side = OrderSide(side)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid side. Must be 'yes' or 'no'"
        )
    
    # Create hypothetical order
    order = SimulatedOrder(
        id=str(uuid.uuid4()),
        strategy_id=None,
        game_id=game_id,
        market_id=None,
        market_ticker=market_ticker,
        order_type=OrderType.MARKET,
        side=order_side,
        quantity=quantity,
        limit_price=None,
        filled_price=None,
        status=OrderStatus.PENDING,
        placed_at=datetime.utcnow(),
        filled_at=None,
        signal_data=None,
        created_at=datetime.utcnow()
    )
    
    # Run risk check
    result = risk_manager.check_order(order, execution_engine.get_all_positions())
    
    return {
        "would_approve": result.approved,
        "reason": result.reason,
        "limit_type": result.limit_type.value if result.limit_type else None,
        "current_value": result.current_value,
        "limit_value": result.limit_value
    }

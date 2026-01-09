"""
Pydantic models for Order entities.

Defines data validation schemas for simulated order operations.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(str, Enum):
    """Order side enumeration."""
    YES = "yes"
    NO = "no"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class OrderBase(BaseModel):
    """Base order model with common fields."""
    game_id: UUID4 = Field(..., description="Associated game ID")
    strategy_id: UUID4 = Field(..., description="Associated strategy ID")
    market_id: Optional[UUID4] = Field(None, description="Associated market ID")
    market_ticker: str = Field(..., description="Kalshi market ticker")
    order_type: OrderType = Field(..., description="Order type (market or limit)")
    side: OrderSide = Field(..., description="Order side (yes or no)")
    quantity: int = Field(..., gt=0, description="Number of contracts")
    limit_price: Optional[Decimal] = Field(None, description="Limit price for limit orders (cents)")
    signal_data: Optional[Dict[str, Any]] = Field(None, description="Trading signal that triggered this order")


class OrderCreate(OrderBase):
    """Model for creating a new order."""
    pass


class SimulatedOrder(OrderBase):
    """Complete simulated order model including database fields."""
    id: UUID4 = Field(..., description="Unique order identifier")
    filled_price: Optional[Decimal] = Field(None, description="Actual fill price (cents)")
    status: OrderStatus = Field(..., description="Order status")
    placed_at: datetime = Field(..., description="Order placement timestamp")
    filled_at: Optional[datetime] = Field(None, description="Order fill timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "game_id": "456e7890-e89b-12d3-a456-426614174111",
                "strategy_id": "789e0123-e89b-12d3-a456-426614174222",
                "market_id": "012e3456-e89b-12d3-a456-426614174333",
                "market_ticker": "kxnbagame-26jan06dalsac",
                "order_type": "market",
                "side": "yes",
                "quantity": 10,
                "limit_price": None,
                "filled_price": 0.43,
                "status": "filled",
                "placed_at": "2026-01-06T19:32:15",
                "filled_at": "2026-01-06T19:32:15",
                "signal_data": {
                    "strategy": "sharp_line",
                    "reason": "Kalshi undervalued by 7%",
                    "confidence": 0.85
                },
                "created_at": "2026-01-06T19:32:15"
            }
        }


# ============================================================================
# Trade Signal Models
# ============================================================================

class TradeSignalBase(BaseModel):
    """Base trade signal model."""
    strategy_id: str = Field(..., description="Strategy generating the signal")
    strategy_name: str = Field(..., description="Name of the strategy")
    market_ticker: str = Field(..., description="Target market ticker")
    side: OrderSide = Field(..., description="Recommended side (yes or no)")
    quantity: int = Field(..., gt=0, description="Recommended quantity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence (0-1)")
    reason: str = Field(..., description="Human-readable reason for signal")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional signal data")


class TradeSignal(TradeSignalBase):
    """Complete trade signal model with timestamp."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal generation time")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "strategy_name": "Sharp Line Detection",
                "market_ticker": "KXNBAGAME-26JAN08DALUTA-DAL",
                "side": "yes",
                "quantity": 10,
                "confidence": 0.85,
                "reason": "Kalshi undervalued by 7.5%. Kalshi: 45.0%, Consensus: 52.5%. EV: +8.2%",
                "metadata": {
                    "kalshi_prob": 0.45,
                    "consensus_prob": 0.525,
                    "divergence_percent": 7.5,
                    "expected_value": 0.082
                },
                "timestamp": "2026-01-08T19:32:15Z"
            }
        }


# ============================================================================
# Order Execution Response Models
# ============================================================================

class OrderExecutionResponse(BaseModel):
    """Response model for order execution."""
    success: bool = Field(..., description="Whether execution was successful")
    order: Optional[SimulatedOrder] = Field(None, description="Executed order details")
    error: Optional[str] = Field(None, description="Error message if execution failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "order": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "market_ticker": "kxnbagame-26jan06dalsac",
                    "side": "yes",
                    "quantity": 10,
                    "filled_price": 0.43,
                    "status": "filled"
                },
                "error": None
            }
        }


# ============================================================================
# Execution Engine Models
# ============================================================================

class ExecutionPosition(BaseModel):
    """
    Position model for execution engine tracking.
    
    Lightweight position tracking used internally by the execution engine.
    """
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    game_id: str
    market_ticker: str
    side: OrderSide
    quantity: int = Field(default=0, description="Current position size")
    avg_entry_price: Decimal = Field(default=Decimal("0"), description="Average entry price")
    total_cost: Decimal = Field(default=Decimal("0"), description="Total cost basis")
    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl: Decimal = Field(default=Decimal("0"))
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(default=None)
    is_open: bool = Field(default=True)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class ExecutionResult(BaseModel):
    """Result of an order execution attempt."""
    success: bool
    order: Optional[SimulatedOrder] = None
    error: Optional[str] = None
    position_updated: bool = False
    new_position: Optional[ExecutionPosition] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "order": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "market_ticker": "KXNBAGAME-26JAN08DALUTA-DAL",
                    "side": "yes",
                    "quantity": 10,
                    "filled_price": 45.0,
                    "status": "filled"
                },
                "error": None,
                "position_updated": True,
                "new_position": {
                    "market_ticker": "KXNBAGAME-26JAN08DALUTA-DAL",
                    "side": "yes",
                    "quantity": 10,
                    "avg_entry_price": 45.0
                }
            }
        }

"""
Pydantic models for Position entities.

Defines data validation schemas for position tracking and P&L calculations.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PositionSide(str, Enum):
    """Position side enumeration."""
    YES = "yes"
    NO = "no"


class PositionBase(BaseModel):
    """Base position model with common fields."""
    game_id: UUID4 = Field(..., description="Associated game ID")
    strategy_id: UUID4 = Field(..., description="Associated strategy ID")
    market_id: Optional[UUID4] = Field(None, description="Associated market ID")
    market_ticker: str = Field(..., description="Kalshi market ticker")
    side: PositionSide = Field(..., description="Position side (yes or no)")
    quantity: int = Field(..., gt=0, description="Number of contracts")
    avg_price: Decimal = Field(..., description="Average entry price (cents)")


class PositionCreate(PositionBase):
    """Model for creating a new position."""
    opened_at: datetime = Field(default_factory=datetime.utcnow, description="Position open timestamp")


class PositionUpdate(BaseModel):
    """Model for updating an existing position."""
    quantity: Optional[int] = None
    avg_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    is_open: Optional[bool] = None
    closed_at: Optional[datetime] = None


class Position(PositionBase):
    """Complete position model including database fields."""
    id: UUID4 = Field(..., description="Unique position identifier")
    current_price: Optional[Decimal] = Field(None, description="Current market price (cents)")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Unrealized profit/loss ($)")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized profit/loss ($)")
    is_open: bool = Field(default=True, description="Whether position is still open")
    opened_at: datetime = Field(..., description="Position open timestamp")
    closed_at: Optional[datetime] = Field(None, description="Position close timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "game_id": "456e7890-e89b-12d3-a456-426614174111",
                "strategy_id": "789e0123-e89b-12d3-a456-426614174222",
                "market_id": "012e3456-e89b-12d3-a456-426614174333",
                "market_ticker": "kxnbagame-26jan06dalsac",
                "side": "yes",
                "quantity": 10,
                "avg_price": 0.43,
                "current_price": 0.45,
                "unrealized_pnl": 0.20,
                "realized_pnl": 0.00,
                "is_open": True,
                "opened_at": "2026-01-06T19:32:15",
                "closed_at": None,
                "updated_at": "2026-01-06T19:35:00"
            }
        }


# ============================================================================
# P&L Calculation Models
# ============================================================================

class PnLSummary(BaseModel):
    """Summary of profit and loss for a strategy or overall."""
    strategy_id: Optional[UUID4] = Field(None, description="Strategy ID (None for overall)")
    total_unrealized_pnl: Decimal = Field(..., description="Total unrealized P&L ($)")
    total_realized_pnl: Decimal = Field(..., description="Total realized P&L ($)")
    total_pnl: Decimal = Field(..., description="Total P&L (realized + unrealized) ($)")
    open_positions_count: int = Field(..., description="Number of open positions")
    closed_positions_count: int = Field(..., description="Number of closed positions")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of profitable trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_unrealized_pnl": 5.25,
                "total_realized_pnl": 12.80,
                "total_pnl": 18.05,
                "open_positions_count": 3,
                "closed_positions_count": 15,
                "total_trades": 18,
                "winning_trades": 12,
                "losing_trades": 6,
                "win_rate": 66.67
            }
        }


class PositionWithPnL(Position):
    """Position model with calculated P&L details."""
    pnl_dollars: Decimal = Field(..., description="P&L in dollars")
    pnl_percent: Decimal = Field(..., description="P&L as percentage of entry cost")
    entry_cost: Decimal = Field(..., description="Total entry cost ($)")
    current_value: Decimal = Field(..., description="Current position value ($)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "market_ticker": "kxnbagame-26jan06dalsac",
                "side": "yes",
                "quantity": 10,
                "avg_price": 0.43,
                "current_price": 0.45,
                "unrealized_pnl": 0.20,
                "pnl_dollars": 0.20,
                "pnl_percent": 4.65,
                "entry_cost": 4.30,
                "current_value": 4.50,
                "is_open": True
            }
        }

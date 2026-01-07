"""
Pydantic models for Strategy entities.

Defines data validation schemas for trading strategies and performance metrics.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class StrategyType(str, Enum):
    """Strategy type enumeration."""
    SHARP_LINE = "sharp_line"
    MOMENTUM = "momentum"
    EV_MULTI = "ev_multi"
    MEAN_REVERSION = "mean_reversion"
    CORRELATION = "correlation"


class StrategyBase(BaseModel):
    """Base strategy model with common fields."""
    name: str = Field(..., description="Strategy name")
    type: StrategyType = Field(..., description="Strategy type")
    is_enabled: bool = Field(default=False, description="Whether strategy is enabled")
    config: Dict[str, Any] = Field(..., description="Strategy-specific configuration parameters")


class StrategyCreate(StrategyBase):
    """Model for creating a new strategy."""
    pass


class StrategyUpdate(BaseModel):
    """Model for updating an existing strategy."""
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class Strategy(StrategyBase):
    """Complete strategy model including database fields."""
    id: UUID4 = Field(..., description="Unique strategy identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Sharp Line Detector",
                "type": "sharp_line",
                "is_enabled": True,
                "config": {
                    "threshold_percent": 5.0,
                    "min_sample_sportsbooks": 3,
                    "position_size": 10,
                    "cooldown_minutes": 5
                },
                "created_at": "2026-01-05T10:00:00",
                "updated_at": "2026-01-05T10:00:00"
            }
        }


# ============================================================================
# Strategy Performance Models
# ============================================================================

class StrategyPerformanceBase(BaseModel):
    """Base strategy performance model."""
    strategy_id: UUID4 = Field(..., description="Associated strategy ID")
    game_id: Optional[UUID4] = Field(None, description="Associated game ID (if game-specific)")
    timestamp: datetime = Field(..., description="Performance snapshot timestamp")
    total_trades: int = Field(default=0, description="Total number of trades")
    winning_trades: int = Field(default=0, description="Number of winning trades")
    losing_trades: int = Field(default=0, description="Number of losing trades")
    total_pnl: Decimal = Field(default=Decimal("0"), description="Total P&L")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="Unrealized P&L")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="Realized P&L")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    avg_trade_pnl: Optional[Decimal] = Field(None, description="Average P&L per trade")
    max_drawdown: Optional[Decimal] = Field(None, description="Maximum drawdown")
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")


class StrategyPerformanceCreate(StrategyPerformanceBase):
    """Model for creating strategy performance record."""
    pass


class StrategyPerformance(StrategyPerformanceBase):
    """Complete strategy performance model."""
    id: UUID4 = Field(..., description="Unique performance record identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# Risk Limits Models
# ============================================================================

class RiskLimitsBase(BaseModel):
    """Base risk limits model."""
    strategy_id: UUID4 = Field(..., description="Associated strategy ID")
    max_position_size: Optional[int] = Field(None, description="Max contracts per position")
    max_total_exposure: Optional[int] = Field(None, description="Max total open contracts")
    max_loss_per_trade: Optional[Decimal] = Field(None, description="Max loss per single trade ($)")
    max_daily_loss: Optional[Decimal] = Field(None, description="Max total loss per day ($)")
    max_drawdown_percent: Optional[Decimal] = Field(None, description="Max drawdown percentage")


class RiskLimitsCreate(RiskLimitsBase):
    """Model for creating risk limits."""
    pass


class RiskLimitsUpdate(BaseModel):
    """Model for updating risk limits."""
    max_position_size: Optional[int] = None
    max_total_exposure: Optional[int] = None
    max_loss_per_trade: Optional[Decimal] = None
    max_daily_loss: Optional[Decimal] = None
    max_drawdown_percent: Optional[Decimal] = None


class RiskLimits(RiskLimitsBase):
    """Complete risk limits model."""
    id: UUID4 = Field(..., description="Unique risk limits identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "strategy_id": "456e7890-e89b-12d3-a456-426614174111",
                "max_position_size": 100,
                "max_total_exposure": 500,
                "max_loss_per_trade": 50.00,
                "max_daily_loss": 200.00,
                "max_drawdown_percent": 20.0,
                "created_at": "2026-01-05T10:00:00",
                "updated_at": "2026-01-05T10:00:00"
            }
        }

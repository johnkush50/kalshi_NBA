"""
Pydantic models for Kalshi Market entities.

Defines data validation schemas for market and orderbook operations.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MarketType(str, Enum):
    """Market type enumeration."""
    MONEYLINE_HOME = "moneyline_home"
    MONEYLINE_AWAY = "moneyline_away"
    SPREAD = "spread"
    TOTAL = "total"


class MarketSide(str, Enum):
    """Market side enumeration."""
    YES = "yes"
    NO = "no"


class MarketBase(BaseModel):
    """Base market model with common fields."""
    game_id: UUID4 = Field(..., description="Associated game ID")
    ticker: str = Field(..., description="Kalshi market ticker")
    market_type: MarketType = Field(..., description="Type of market")
    strike_value: Optional[Decimal] = Field(None, description="Strike value for spreads and totals")
    side: Optional[MarketSide] = Field(None, description="YES or NO side")
    status: Optional[str] = Field(None, description="Market status")


class MarketCreate(MarketBase):
    """Model for creating a new market."""
    pass


class Market(MarketBase):
    """Complete market model including database fields."""
    id: UUID4 = Field(..., description="Unique market identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# Orderbook Models
# ============================================================================

class OrderbookSnapshotBase(BaseModel):
    """Base orderbook snapshot model."""
    market_id: UUID4 = Field(..., description="Associated market ID")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    yes_bid: Optional[Decimal] = Field(None, description="Best YES bid price (cents)")
    yes_ask: Optional[Decimal] = Field(None, description="Best YES ask price (cents)")
    no_bid: Optional[Decimal] = Field(None, description="Best NO bid price (cents)")
    no_ask: Optional[Decimal] = Field(None, description="Best NO ask price (cents)")
    yes_bid_size: Optional[int] = Field(None, description="YES bid size (contracts)")
    yes_ask_size: Optional[int] = Field(None, description="YES ask size (contracts)")
    no_bid_size: Optional[int] = Field(None, description="NO bid size (contracts)")
    no_ask_size: Optional[int] = Field(None, description="NO ask size (contracts)")


class OrderbookSnapshotCreate(OrderbookSnapshotBase):
    """Model for creating a new orderbook snapshot."""
    pass


class OrderbookSnapshot(OrderbookSnapshotBase):
    """Complete orderbook snapshot model."""
    id: int = Field(..., description="Unique snapshot identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "market_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-01-06T19:32:15",
                "yes_bid": 0.42,
                "yes_ask": 0.44,
                "no_bid": 0.56,
                "no_ask": 0.58,
                "yes_bid_size": 100,
                "yes_ask_size": 150,
                "no_bid_size": 120,
                "no_ask_size": 180,
                "created_at": "2026-01-06T19:32:15"
            }
        }


# ============================================================================
# NBA Live Data Models
# ============================================================================

class NBALiveDataBase(BaseModel):
    """Base NBA live data model."""
    game_id: UUID4 = Field(..., description="Associated game ID")
    timestamp: datetime = Field(..., description="Data timestamp")
    period: Optional[int] = Field(None, description="Current period/quarter")
    time_remaining: Optional[str] = Field(None, description="Time remaining in period")
    home_score: Optional[int] = Field(None, description="Home team score")
    away_score: Optional[int] = Field(None, description="Away team score")
    game_status: Optional[str] = Field(None, description="Game status")
    raw_data: Optional[dict] = Field(None, description="Full box score data")


class NBALiveDataCreate(NBALiveDataBase):
    """Model for creating NBA live data."""
    pass


class NBALiveData(NBALiveDataBase):
    """Complete NBA live data model."""
    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# Betting Odds Models
# ============================================================================

class BettingOddsBase(BaseModel):
    """Base betting odds model."""
    game_id: UUID4 = Field(..., description="Associated game ID")
    nba_game_id: int = Field(..., description="NBA game ID")
    timestamp: datetime = Field(..., description="Odds timestamp")
    vendor: Optional[str] = Field(None, description="Sportsbook vendor")
    moneyline_home: Optional[int] = Field(None, description="Home moneyline odds")
    moneyline_away: Optional[int] = Field(None, description="Away moneyline odds")
    spread_home_value: Optional[Decimal] = Field(None, description="Home spread value")
    spread_home_odds: Optional[int] = Field(None, description="Home spread odds")
    spread_away_value: Optional[Decimal] = Field(None, description="Away spread value")
    spread_away_odds: Optional[int] = Field(None, description="Away spread odds")
    total_value: Optional[Decimal] = Field(None, description="Total points value")
    total_over_odds: Optional[int] = Field(None, description="Over odds")
    total_under_odds: Optional[int] = Field(None, description="Under odds")


class BettingOddsCreate(BettingOddsBase):
    """Model for creating betting odds."""
    pass


class BettingOdds(BettingOddsBase):
    """Complete betting odds model."""
    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True

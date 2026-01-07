"""
Pydantic models for Game entities.

Defines data validation schemas for game-related operations.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


class GameStatus(str, Enum):
    """Game status enumeration."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"


class GameBase(BaseModel):
    """Base game model with common fields."""
    kalshi_event_ticker: str = Field(..., description="Kalshi event ticker")
    kalshi_market_ticker_seed: str = Field(..., description="Initial market ticker entered by user")
    nba_game_id: Optional[int] = Field(None, description="NBA game ID from balldontlie.io")
    home_team: str = Field(..., description="Home team name or abbreviation")
    away_team: str = Field(..., description="Away team name or abbreviation")
    home_team_id: Optional[int] = Field(None, description="Home team ID")
    away_team_id: Optional[int] = Field(None, description="Away team ID")
    game_date: datetime = Field(..., description="Game date and time")
    status: GameStatus = Field(default=GameStatus.SCHEDULED, description="Game status")
    is_active: bool = Field(default=True, description="Whether game is actively being tracked")


class GameCreate(GameBase):
    """Model for creating a new game."""
    pass


class GameUpdate(BaseModel):
    """Model for updating an existing game."""
    nba_game_id: Optional[int] = None
    status: Optional[GameStatus] = None
    is_active: Optional[bool] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None


class Game(GameBase):
    """Complete game model including database fields."""
    id: UUID4 = Field(..., description="Unique game identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "kalshi_event_ticker": "NBAGAME-26JAN06-DALSAC",
                "kalshi_market_ticker_seed": "kxnbagame-26jan06dalsac",
                "nba_game_id": 12345,
                "home_team": "Sacramento Kings",
                "away_team": "Dallas Mavericks",
                "home_team_id": 25,
                "away_team_id": 7,
                "game_date": "2026-01-06T19:00:00",
                "status": "scheduled",
                "is_active": True,
                "created_at": "2026-01-05T10:00:00",
                "updated_at": "2026-01-05T10:00:00"
            }
        }


class GameWithMarkets(Game):
    """Game model with associated markets."""
    markets: list = Field(default_factory=list, description="Associated Kalshi markets")

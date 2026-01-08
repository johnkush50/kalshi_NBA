"""
Unified GameState model for the Data Aggregation Layer.

Combines Kalshi orderbook data, NBA live data, and betting odds into
a single unified state object that strategies can consume.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class GamePhase(str, Enum):
    """Current phase of the game."""
    SCHEDULED = "scheduled"
    PREGAME = "pregame"
    LIVE = "live"
    HALFTIME = "halftime"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class OrderbookState(BaseModel):
    """Current orderbook state for a single market."""
    ticker: str
    yes_bid: Optional[Decimal] = None
    yes_ask: Optional[Decimal] = None
    no_bid: Optional[Decimal] = None
    no_ask: Optional[Decimal] = None
    yes_bid_size: Optional[int] = None
    yes_ask_size: Optional[int] = None
    no_bid_size: Optional[int] = None
    no_ask_size: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid-price between yes bid and ask."""
        if self.yes_bid is not None and self.yes_ask is not None:
            return (self.yes_bid + self.yes_ask) / 2
        return None

    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate spread between yes bid and ask."""
        if self.yes_bid is not None and self.yes_ask is not None:
            return self.yes_ask - self.yes_bid
        return None

    @property
    def has_liquidity(self) -> bool:
        """Check if there's liquidity on both sides."""
        return (
            self.yes_bid is not None and
            self.yes_ask is not None and
            self.yes_bid_size is not None and
            self.yes_ask_size is not None and
            self.yes_bid_size > 0 and
            self.yes_ask_size > 0
        )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class MarketState(BaseModel):
    """State of a single Kalshi market with its orderbook."""
    id: str
    ticker: str
    market_type: str  # 'moneyline', 'spread', 'total'
    strike_value: Optional[Decimal] = None
    team: Optional[str] = None  # For spreads: which team the spread applies to
    orderbook: Optional[OrderbookState] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class NBAGameState(BaseModel):
    """Current state of the NBA game."""
    nba_game_id: Optional[int] = None
    status: str = "scheduled"  # 'scheduled', 'in_progress', 'final'
    period: int = 0
    time_remaining: str = ""
    home_score: int = 0
    away_score: int = 0
    home_team: str = ""
    away_team: str = ""
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_score(self) -> int:
        """Total combined score."""
        return self.home_score + self.away_score

    @property
    def score_differential(self) -> int:
        """Home score minus away score (positive = home leading)."""
        return self.home_score - self.away_score

    @property
    def is_live(self) -> bool:
        """Check if game is currently in progress."""
        return self.status == "in_progress"

    @property
    def is_finished(self) -> bool:
        """Check if game has ended."""
        return self.status == "final"

    @property
    def minutes_elapsed(self) -> Optional[float]:
        """Estimate minutes elapsed in the game."""
        if self.period == 0:
            return 0.0
        
        # Parse time remaining (format: "MM:SS" or "M:SS")
        try:
            if ":" in self.time_remaining:
                parts = self.time_remaining.split(":")
                minutes = int(parts[0])
                seconds = int(parts[1])
                time_left_in_period = minutes + seconds / 60
            else:
                time_left_in_period = 12.0  # Default to start of period
            
            # Each period is 12 minutes, calculate elapsed
            completed_periods = max(0, self.period - 1)
            elapsed_in_current = 12.0 - time_left_in_period
            return completed_periods * 12.0 + elapsed_in_current
        except (ValueError, IndexError):
            return None


class OddsState(BaseModel):
    """Betting odds from a single sportsbook vendor."""
    vendor: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Moneyline odds (American format, e.g., -150, +130)
    moneyline_home: Optional[int] = None
    moneyline_away: Optional[int] = None
    
    # Spread odds
    spread_home_value: Optional[Decimal] = None  # e.g., -5.5
    spread_home_odds: Optional[int] = None       # e.g., -110
    spread_away_value: Optional[Decimal] = None
    spread_away_odds: Optional[int] = None
    
    # Total odds
    total_value: Optional[Decimal] = None        # e.g., 220.5
    total_over_odds: Optional[int] = None        # e.g., -110
    total_under_odds: Optional[int] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class ConsensusOdds(BaseModel):
    """Aggregated consensus odds from multiple sportsbooks."""
    num_sportsbooks: int = 0
    
    # Implied probabilities (as Decimal, 0-1)
    home_win_probability: Optional[Decimal] = None
    away_win_probability: Optional[Decimal] = None
    
    # Spread consensus
    spread_line: Optional[Decimal] = None
    spread_home_probability: Optional[Decimal] = None
    
    # Total consensus
    total_line: Optional[Decimal] = None
    over_probability: Optional[Decimal] = None
    under_probability: Optional[Decimal] = None
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


class GameState(BaseModel):
    """
    Unified game state combining all data sources.
    
    This is the primary data object consumed by trading strategies.
    It aggregates Kalshi market data, NBA live data, and betting odds
    into a single consistent view.
    """
    # Identifiers
    game_id: str
    event_ticker: str
    
    # Game info
    home_team: str
    away_team: str
    game_date: datetime
    phase: GamePhase = GamePhase.SCHEDULED
    
    # Kalshi markets (ticker -> MarketState)
    markets: Dict[str, MarketState] = Field(default_factory=dict)
    
    # NBA live data
    nba_state: Optional[NBAGameState] = None
    
    # Betting odds by vendor (vendor_name -> OddsState)
    odds: Dict[str, OddsState] = Field(default_factory=dict)
    
    # Aggregated consensus odds
    consensus: Optional[ConsensusOdds] = None
    
    # Calculated implied probabilities from Kalshi prices (ticker -> probability)
    kalshi_probabilities: Dict[str, Decimal] = Field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    @property
    def is_live(self) -> bool:
        """Check if the game is currently live."""
        return self.phase == GamePhase.LIVE

    @property
    def is_finished(self) -> bool:
        """Check if the game has finished."""
        return self.phase == GamePhase.FINISHED

    @property
    def has_nba_data(self) -> bool:
        """Check if NBA data is available."""
        return self.nba_state is not None and self.nba_state.nba_game_id is not None

    @property
    def has_odds_data(self) -> bool:
        """Check if betting odds are available."""
        return len(self.odds) > 0

    @property
    def num_active_markets(self) -> int:
        """Count markets with active orderbooks."""
        return sum(
            1 for m in self.markets.values()
            if m.orderbook is not None and m.orderbook.has_liquidity
        )

    def get_moneyline_market(self, side: str = "home") -> Optional[MarketState]:
        """Get the moneyline market for a side."""
        for market in self.markets.values():
            if market.market_type == "moneyline":
                if side == "home" and "home" in market.ticker.lower():
                    return market
                elif side == "away" and "away" in market.ticker.lower():
                    return market
        return None

    def get_spread_markets(self) -> List[MarketState]:
        """Get all spread markets."""
        return [m for m in self.markets.values() if m.market_type == "spread"]

    def get_total_markets(self) -> List[MarketState]:
        """Get all total (over/under) markets."""
        return [m for m in self.markets.values() if m.market_type == "total"]

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None,
            datetime: lambda v: v.isoformat() if v else None
        }

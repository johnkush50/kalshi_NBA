"""
Live Game Mean Reversion Strategy.

Detects when live game odds have overreacted to in-game events and
trades on the expectation of mean reversion toward pre-game levels.

Strategy Logic:
1. Store pre-game prices when game goes live
2. Compare current live prices to pre-game baseline
3. If swing is within tradeable range, bet on reversion
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import logging

from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState, MarketState, GamePhase
from backend.models.order import TradeSignal, OrderSide

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Live Game Mean Reversion Strategy.
    
    Trades when live odds swing significantly from pre-game levels,
    expecting reversion to the mean.
    """
    
    STRATEGY_NAME = "Live Mean Reversion"
    STRATEGY_TYPE = "mean_reversion"
    STRATEGY_DESCRIPTION = "Trade on overreactions during live games, expecting mean reversion"
    
    def __init__(self, strategy_id: str, config: Dict[str, Any] = None):
        super().__init__(strategy_id, config)
        
        # Store pre-game prices per game: game_id -> {ticker -> price}
        self._pregame_prices: Dict[str, Dict[str, Decimal]] = {}
        
        # Track which games we've seen go live
        self._games_seen_live: set = set()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "min_reversion_percent": 15.0,    # Min swing to trigger (15%)
            "max_reversion_percent": 40.0,    # Max swing (beyond = real shift)
            "min_time_remaining_pct": 25.0,   # Min % of game remaining
            "position_size": 10,              # Contracts per trade
            "cooldown_minutes": 10,           # Longer cooldown for live
            "only_first_half": True,          # Only trade in first half
            "market_types": ["moneyline"],    # Markets to trade
            "max_score_deficit": 20           # Max point deficit to trade (NBA)
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """Evaluate game state for mean reversion opportunities."""
        if not self.is_enabled:
            return []
        
        signals = []
        game_id = game_state.game_id
        
        # Check if game is live
        is_live = self._is_game_live(game_state)
        
        logger.info(
            f"DEBUG {game_id}: phase={game_state.phase}, is_live={is_live}, "
            f"has_pregame_prices={game_id in self._pregame_prices}"
        )
        
        # If game just went live, store pre-game prices
        if is_live and game_id not in self._games_seen_live:
            self._store_pregame_prices(game_state)
            self._games_seen_live.add(game_id)
            logger.info(f"DEBUG {game_id}: Stored pre-game prices for {len(self._pregame_prices.get(game_id, {}))} markets")
            return []  # Don't trade on first live evaluation
        
        # Only evaluate during live games
        if not is_live:
            logger.info(f"DEBUG {game_id}: SKIP not live")
            return []
        
        # Check if we have pre-game prices
        if game_id not in self._pregame_prices:
            logger.info(f"DEBUG {game_id}: SKIP no pre-game prices stored")
            return []
        
        # Check time remaining
        if not self._check_time_remaining(game_state):
            logger.info(f"DEBUG {game_id}: SKIP insufficient time remaining")
            return []
        
        # Check first half restriction
        if self.config["only_first_half"] and not self._is_first_half(game_state):
            logger.info(f"DEBUG {game_id}: SKIP not first half (period={game_state.nba_state.period if game_state.nba_state else 'unknown'})")
            return []
        
        # Evaluate each market
        for ticker, market in game_state.markets.items():
            signal = self._evaluate_market(game_state, market)
            if signal:
                signals.append(signal)
                self.record_signal(signal)
        
        return signals
    
    def _is_game_live(self, game_state: GameState) -> bool:
        """Check if game is currently live."""
        # Check phase
        if game_state.phase == GamePhase.LIVE:
            return True
        
        # Also check NBA state if available
        if game_state.nba_state:
            status = game_state.nba_state.status
            # NBA API returns status like "in_progress" or period > 0
            if game_state.nba_state.period and game_state.nba_state.period > 0:
                return True
        
        return False
    
    def _is_first_half(self, game_state: GameState) -> bool:
        """Check if game is in first half (Q1 or Q2 for NBA)."""
        if not game_state.nba_state:
            return True  # Assume first half if no data
        
        period = game_state.nba_state.period
        if period is None:
            return True
        
        # NBA: periods 1-2 are first half
        return period <= 2
    
    def _check_time_remaining(self, game_state: GameState) -> bool:
        """Check if enough game time remains for mean reversion."""
        min_pct = self.config["min_time_remaining_pct"]
        
        if not game_state.nba_state:
            return True  # Assume enough time if no data
        
        period = game_state.nba_state.period or 1
        
        # NBA has 4 periods, estimate % remaining
        # Period 1 = 75-100% remaining, Period 2 = 50-75%, etc.
        periods_remaining = 4 - period + 1
        pct_remaining = (periods_remaining / 4) * 100
        
        return pct_remaining >= min_pct
    
    def _store_pregame_prices(self, game_state: GameState) -> None:
        """Store current prices as pre-game baseline."""
        game_id = game_state.game_id
        self._pregame_prices[game_id] = {}
        
        for ticker, market in game_state.markets.items():
            if market.orderbook and market.orderbook.mid_price:
                self._pregame_prices[game_id][ticker] = market.orderbook.mid_price
    
    def _evaluate_market(
        self, 
        game_state: GameState, 
        market: MarketState
    ) -> Optional[TradeSignal]:
        """Evaluate a single market for mean reversion opportunity."""
        
        # Check market type
        if market.market_type not in self.config["market_types"]:
            return None
        
        # Check cooldown
        if not self.check_cooldown(market.ticker):
            logger.info(f"DEBUG {market.ticker}: SKIP in cooldown")
            return None
        
        # Get orderbook
        if not market.orderbook:
            return None
        
        # Get current and pre-game prices
        current_price = market.orderbook.mid_price
        pregame_prices = self._pregame_prices.get(game_state.game_id, {})
        pregame_price = pregame_prices.get(market.ticker)
        
        if not current_price or not pregame_price:
            logger.info(f"DEBUG {market.ticker}: SKIP missing prices (current={current_price}, pregame={pregame_price})")
            return None
        
        # Calculate swing (in percentage points)
        # Prices are in cents (0-100), so swing is already in percentage points
        swing = float(current_price) - float(pregame_price)
        swing_pct = abs(swing)
        
        logger.info(
            f"DEBUG {market.ticker}: pregame={float(pregame_price):.1f}¢, "
            f"current={float(current_price):.1f}¢, swing={swing:+.1f}pp"
        )
        
        # Check swing is within tradeable range
        min_swing = self.config["min_reversion_percent"]
        max_swing = self.config["max_reversion_percent"]
        
        if swing_pct < min_swing:
            logger.info(f"DEBUG {market.ticker}: SKIP swing {swing_pct:.1f}pp < min {min_swing}pp")
            return None
        
        if swing_pct > max_swing:
            logger.info(f"DEBUG {market.ticker}: SKIP swing {swing_pct:.1f}pp > max {max_swing}pp (real shift?)")
            return None
        
        # Check score deficit isn't too extreme
        if not self._check_score_deficit(game_state, market):
            logger.info(f"DEBUG {market.ticker}: SKIP score deficit too large")
            return None
        
        # Determine trade direction (bet on reversion)
        if swing < 0:
            # Price dropped (team doing worse) → BUY YES (expect reversion up)
            side = OrderSide.YES
            entry_price = market.orderbook.yes_ask
        else:
            # Price increased (team doing better) → BUY NO (expect reversion down)
            side = OrderSide.NO
            entry_price = market.orderbook.no_ask
        
        if not entry_price or entry_price <= 0:
            return None
        
        # Record trade for cooldown
        self.record_trade(market.ticker)
        
        # Calculate confidence based on swing magnitude
        # Larger swings (closer to max) = higher confidence in overreaction
        confidence = min(swing_pct / max_swing, 1.0)
        
        signal = TradeSignal(
            strategy_id=self.strategy_id,
            strategy_name=self.STRATEGY_NAME,
            market_ticker=market.ticker,
            side=side,
            quantity=self.config["position_size"],
            confidence=confidence,
            reason=self._format_reason(market, pregame_price, current_price, swing),
            metadata={
                "pregame_price": float(pregame_price),
                "current_price": float(current_price),
                "swing_percent": swing_pct,
                "swing_direction": "down" if swing < 0 else "up",
                "entry_price": float(entry_price),
                "period": game_state.nba_state.period if game_state.nba_state else None,
                "score_home": game_state.nba_state.home_score if game_state.nba_state else None,
                "score_away": game_state.nba_state.away_score if game_state.nba_state else None
            }
        )
        
        logger.info(
            f"Mean Reversion signal: {side.value.upper()} {self.config['position_size']} "
            f"{market.ticker} (swing: {swing:+.1f}pp from {float(pregame_price):.1f}¢)"
        )
        
        return signal
    
    def _check_score_deficit(self, game_state: GameState, market: MarketState) -> bool:
        """
        Check if score deficit is within acceptable range.
        
        Don't trade mean reversion if a team is getting blown out.
        """
        max_deficit = self.config.get("max_score_deficit", 20)
        
        if not game_state.nba_state:
            return True
        
        home_score = game_state.nba_state.home_score or 0
        away_score = game_state.nba_state.away_score or 0
        deficit = abs(home_score - away_score)
        
        return deficit <= max_deficit
    
    def _format_reason(
        self, 
        market: MarketState,
        pregame_price: Decimal,
        current_price: Decimal,
        swing: float
    ) -> str:
        """Format human-readable reason for the signal."""
        direction = "dropped" if swing < 0 else "increased"
        return (
            f"Price {direction} {abs(swing):.1f}pp from pre-game ({float(pregame_price):.1f}¢ → "
            f"{float(current_price):.1f}¢). Expecting mean reversion."
        )
    
    def get_pregame_prices(self, game_id: str) -> Dict[str, float]:
        """Get stored pre-game prices for a game (for debugging)."""
        prices = self._pregame_prices.get(game_id, {})
        return {ticker: float(price) for ticker, price in prices.items()}
    
    def clear_game_data(self, game_id: str) -> None:
        """Clear stored data for a game."""
        if game_id in self._pregame_prices:
            del self._pregame_prices[game_id]
        if game_id in self._games_seen_live:
            self._games_seen_live.remove(game_id)
        logger.info(f"Cleared mean reversion data for game {game_id}")
    
    def simulate_pregame_prices(self, game_id: str, prices: Dict[str, float]) -> None:
        """
        Manually set pre-game prices for testing.
        
        Usage: strategy.simulate_pregame_prices(game_id, {"TICKER": 50.0})
        """
        self._pregame_prices[game_id] = {
            ticker: Decimal(str(price)) for ticker, price in prices.items()
        }
        self._games_seen_live.add(game_id)
        logger.info(f"Simulated pre-game prices for {game_id}: {len(prices)} markets")

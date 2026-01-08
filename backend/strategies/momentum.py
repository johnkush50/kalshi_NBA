"""
Momentum Scalping Strategy.

Detects rapid price movements in Kalshi markets and trades in the direction
of momentum, assuming informed traders are moving the market.

Strategy Logic:
1. Track rolling price history for each market
2. Compare current price to price N seconds ago
3. If price moved significantly, trade in direction of movement
"""

from typing import Dict, Any, List, Optional, Deque
from datetime import datetime, timedelta
from decimal import Decimal
from collections import deque
import logging

from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState, MarketState
from backend.models.order import TradeSignal, OrderSide

logger = logging.getLogger(__name__)


class PricePoint:
    """A single price observation with timestamp."""
    def __init__(self, price: Decimal, timestamp: datetime):
        self.price = price
        self.timestamp = timestamp


class MomentumStrategy(BaseStrategy):
    """
    Momentum Scalping Strategy.
    
    Tracks price history and generates signals when significant
    price movements are detected within a time window.
    """
    
    STRATEGY_NAME = "Momentum Scalping"
    STRATEGY_TYPE = "momentum"
    STRATEGY_DESCRIPTION = "Trade in the direction of rapid price movements"
    
    def __init__(self, strategy_id: str, config: Dict[str, Any] = None):
        super().__init__(strategy_id, config)
        
        # Price history per market: ticker -> deque of PricePoint
        # Use deque with maxlen for automatic old data removal
        self._price_history: Dict[str, Deque[PricePoint]] = {}
        
        # Max history to keep (enough for lookback + buffer)
        self._max_history_points = 100
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "lookback_seconds": 120,        # 2 minute lookback window
            "min_price_change_cents": 5,    # 5 cent minimum move
            "position_size": 10,            # Contracts per trade
            "cooldown_minutes": 3,          # Minutes between trades on same market
            "max_spread_cents": 3,          # Maximum acceptable spread
            "market_types": ["moneyline", "spread", "total"]  # Which markets to trade
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """
        Evaluate game state and generate momentum signals.
        
        First updates price history, then checks for momentum.
        """
        if not self.is_enabled:
            return []
        
        signals = []
        
        # Update price history and check for momentum
        for ticker, market in game_state.markets.items():
            # Update price history
            self._update_price_history(market)
            
            # Check for momentum signal
            signal = self._evaluate_market(game_state, market)
            if signal:
                signals.append(signal)
                self.record_signal(signal)
        
        return signals
    
    def _update_price_history(self, market: MarketState) -> None:
        """Update the price history for a market."""
        if not market.orderbook:
            return
        
        mid_price = market.orderbook.mid_price
        if not mid_price or mid_price <= 0:
            return
        
        ticker = market.ticker
        
        # Initialize history deque if needed
        if ticker not in self._price_history:
            self._price_history[ticker] = deque(maxlen=self._max_history_points)
        
        # Add new price point
        self._price_history[ticker].append(
            PricePoint(price=mid_price, timestamp=datetime.utcnow())
        )
    
    def _get_historical_price(self, ticker: str, seconds_ago: int) -> Optional[Decimal]:
        """
        Get the price from approximately N seconds ago.
        
        Returns the oldest price within the lookback window, or None if
        not enough history exists.
        """
        if ticker not in self._price_history:
            return None
        
        history = self._price_history[ticker]
        if len(history) < 2:
            return None
        
        target_time = datetime.utcnow() - timedelta(seconds=seconds_ago)
        
        # Find the price closest to target_time
        closest_price = None
        closest_diff = None
        
        for point in history:
            diff = abs((point.timestamp - target_time).total_seconds())
            if closest_diff is None or diff < closest_diff:
                closest_diff = diff
                closest_price = point.price
        
        # Only return if we found a price within reasonable range
        # (within 50% of lookback window)
        if closest_diff is not None and closest_diff <= seconds_ago * 0.5:
            return closest_price
        
        return None
    
    def _evaluate_market(
        self, 
        game_state: GameState, 
        market: MarketState
    ) -> Optional[TradeSignal]:
        """
        Evaluate a single market for momentum opportunity.
        """
        # Check if market type is enabled
        if market.market_type not in self.config["market_types"]:
            logger.info(f"DEBUG {market.ticker}: SKIP market_type={market.market_type} not in {self.config['market_types']}")
            return None
        
        # Check cooldown
        if not self.check_cooldown(market.ticker):
            logger.info(f"DEBUG {market.ticker}: SKIP in cooldown")
            return None
        
        # Get orderbook
        if not market.orderbook:
            logger.info(f"DEBUG {market.ticker}: SKIP no orderbook")
            return None
        
        # Get current price (mid price in cents)
        current_price = market.orderbook.mid_price
        if not current_price or current_price <= 0:
            logger.info(f"DEBUG {market.ticker}: SKIP invalid current_price={current_price}")
            return None
        
        # Get historical price
        lookback = self.config["lookback_seconds"]
        historical_price = self._get_historical_price(market.ticker, lookback)
        
        if historical_price is None:
            logger.info(f"DEBUG {market.ticker}: SKIP no historical price (need more data)")
            return None
        
        # Calculate price change (in cents)
        # Prices are stored as decimals 0-1, convert to cents for comparison
        current_cents = float(current_price) * 100
        historical_cents = float(historical_price) * 100
        price_change = current_cents - historical_cents
        
        logger.info(
            f"DEBUG {market.ticker}: current={current_cents:.1f}¢, "
            f"historical={historical_cents:.1f}¢, change={price_change:.1f}¢"
        )
        
        # Check minimum price change threshold
        min_change = self.config["min_price_change_cents"]
        if abs(price_change) < min_change:
            logger.info(
                f"DEBUG {market.ticker}: SKIP price_change {abs(price_change):.1f}¢ < threshold {min_change}¢"
            )
            return None
        
        # Check spread
        spread = self._calculate_spread(market)
        max_spread = self.config["max_spread_cents"]
        if spread is not None and spread > max_spread:
            logger.info(
                f"DEBUG {market.ticker}: SKIP spread {spread:.1f}¢ > max {max_spread}¢"
            )
            return None
        
        # Determine trade direction based on momentum
        if price_change > 0:
            # Price going up, follow momentum -> BUY YES
            side = OrderSide.YES
            entry_price = market.orderbook.yes_ask
        else:
            # Price going down, follow momentum -> BUY NO
            side = OrderSide.NO
            entry_price = market.orderbook.no_ask
        
        if not entry_price or entry_price <= 0:
            logger.info(f"DEBUG {market.ticker}: SKIP invalid entry_price={entry_price}")
            return None
        
        # Record the trade for cooldown
        self.record_trade(market.ticker)
        
        # Calculate confidence based on magnitude of move
        confidence = min(abs(price_change) / 10, 1.0)  # 10¢ move = 100% confidence
        
        # Create signal
        signal = TradeSignal(
            strategy_id=self.strategy_id,
            strategy_name=self.STRATEGY_NAME,
            market_ticker=market.ticker,
            side=side,
            quantity=self.config["position_size"],
            confidence=confidence,
            reason=self._format_reason(market, price_change, lookback),
            metadata={
                "current_price_cents": current_cents,
                "historical_price_cents": historical_cents,
                "price_change_cents": price_change,
                "lookback_seconds": lookback,
                "spread_cents": spread,
                "entry_price": float(entry_price)
            }
        )
        
        logger.info(
            f"Momentum signal: {side.value.upper()} {self.config['position_size']} {market.ticker} "
            f"(change: {price_change:+.1f}¢ over {lookback}s)"
        )
        
        return signal
    
    def _calculate_spread(self, market: MarketState) -> Optional[float]:
        """Calculate the bid-ask spread in cents."""
        if not market.orderbook:
            return None
        
        yes_bid = market.orderbook.yes_bid
        yes_ask = market.orderbook.yes_ask
        
        if yes_bid is None or yes_ask is None:
            return None
        
        # Convert to cents
        spread = (float(yes_ask) - float(yes_bid)) * 100
        return spread
    
    def _format_reason(
        self, 
        market: MarketState, 
        price_change: float, 
        lookback: int
    ) -> str:
        """Format human-readable reason for the signal."""
        direction = "up" if price_change > 0 else "down"
        return (
            f"Price moved {direction} {abs(price_change):.1f}¢ in {lookback} seconds. "
            f"Following momentum."
        )
    
    def get_price_history(self, ticker: str) -> List[Dict]:
        """Get price history for debugging/display."""
        if ticker not in self._price_history:
            return []
        
        return [
            {"price": float(p.price), "timestamp": p.timestamp.isoformat()}
            for p in self._price_history[ticker]
        ]
    
    def clear_price_history(self) -> None:
        """Clear all price history (useful for testing)."""
        self._price_history.clear()
        logger.info(f"Price history cleared for strategy {self.strategy_id}")

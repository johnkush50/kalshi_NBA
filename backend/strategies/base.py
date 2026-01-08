"""
Base Strategy Class.

All trading strategies inherit from this base class which provides:
- Configuration management
- Signal generation interface
- Trade execution hooks
- Performance tracking
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from backend.models.game_state import GameState, MarketState
from backend.models.order import TradeSignal, OrderSide

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Subclasses must implement:
    - evaluate(): Analyze game state and generate signals
    - get_default_config(): Return default configuration
    """
    
    # Strategy metadata (override in subclasses)
    STRATEGY_NAME: str = "base"
    STRATEGY_TYPE: str = "base"
    STRATEGY_DESCRIPTION: str = "Base strategy class"
    
    def __init__(self, strategy_id: str, config: Dict[str, Any] = None):
        """
        Initialize the strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy instance
            config: Strategy configuration (uses defaults if not provided)
        """
        self.strategy_id = strategy_id
        self.config = {**self.get_default_config(), **(config or {})}
        self.is_enabled = False
        
        # Track last trade time per market for cooldown
        self._last_trade_time: Dict[str, datetime] = {}
        
        # Track generated signals for analysis
        self._signal_history: List[TradeSignal] = []
        
        logger.info(f"Strategy initialized: {self.STRATEGY_NAME} ({strategy_id})")
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for this strategy."""
        pass
    
    @abstractmethod
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        """
        Evaluate the current game state and generate trade signals.
        
        Args:
            game_state: Current unified game state
        
        Returns:
            List of TradeSignal objects (empty if no opportunities)
        """
        pass
    
    def enable(self) -> None:
        """Enable the strategy."""
        self.is_enabled = True
        logger.info(f"Strategy enabled: {self.STRATEGY_NAME}")
    
    def disable(self) -> None:
        """Disable the strategy."""
        self.is_enabled = False
        logger.info(f"Strategy disabled: {self.STRATEGY_NAME}")
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update strategy configuration."""
        self.config.update(new_config)
        logger.info(f"Strategy config updated: {self.STRATEGY_NAME}")
    
    def check_cooldown(self, market_ticker: str) -> bool:
        """
        Check if cooldown period has passed for a market.
        
        Args:
            market_ticker: The market to check
        
        Returns:
            True if we can trade (cooldown passed), False otherwise
        """
        cooldown_minutes = self.config.get("cooldown_minutes", 5)
        last_trade = self._last_trade_time.get(market_ticker)
        
        if last_trade is None:
            logger.info(f"Cooldown check {market_ticker}: NO previous trade (strategy_id={self.strategy_id})")
            return True
        
        elapsed = datetime.utcnow() - last_trade
        elapsed_minutes = elapsed.total_seconds() / 60
        can_trade = elapsed >= timedelta(minutes=cooldown_minutes)
        
        if not can_trade:
            logger.info(
                f"Cooldown BLOCKED {market_ticker}: elapsed={elapsed_minutes:.2f}min < cooldown={cooldown_minutes}min"
            )
        return can_trade
    
    def record_trade(self, market_ticker: str) -> None:
        """Record that a trade was made on a market (for cooldown tracking)."""
        now = datetime.utcnow()
        self._last_trade_time[market_ticker] = now
        logger.info(f"Cooldown STARTED for {market_ticker} (strategy_id={self.strategy_id})")
    
    def record_signal(self, signal: TradeSignal) -> None:
        """Record a generated signal for history/analysis."""
        self._signal_history.append(signal)
        # Keep only last 100 signals
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]
    
    def get_signal_history(self) -> List[TradeSignal]:
        """Get recent signal history."""
        return self._signal_history.copy()
    
    def reset_cooldowns(self) -> None:
        """Reset all cooldown timers."""
        self._last_trade_time.clear()
        logger.info(f"Cooldowns reset for strategy: {self.STRATEGY_NAME}")

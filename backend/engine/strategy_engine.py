"""
Strategy Execution Engine.

Manages multiple trading strategies, coordinates signal generation,
and handles trade execution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import uuid

from backend.config.settings import settings
from backend.models.game_state import GameState
from backend.models.order import TradeSignal
from backend.strategies.base import BaseStrategy
from backend.strategies.sharp_line import SharpLineStrategy
from backend.strategies.momentum import MomentumStrategy
from backend.strategies.ev_multibook import EVMultiBookStrategy
from backend.strategies.mean_reversion import MeanReversionStrategy
from backend.strategies.correlation import CorrelationStrategy
from backend.engine.aggregator import get_aggregator

logger = logging.getLogger(__name__)


# Strategy type registry
STRATEGY_REGISTRY: Dict[str, type] = {
    "sharp_line": SharpLineStrategy,
    "momentum": MomentumStrategy,
    "ev_multibook": EVMultiBookStrategy,
    "mean_reversion": MeanReversionStrategy,
    "correlation": CorrelationStrategy,
}


class StrategyEngine:
    """
    Central engine for managing and executing trading strategies.
    
    Responsibilities:
    - Load and manage strategy instances
    - Subscribe to game state updates from DataAggregator
    - Coordinate signal generation across strategies
    - Route signals to execution engine
    - Track strategy performance
    """
    
    def __init__(self):
        """Initialize the strategy engine."""
        # Active strategies (strategy_id -> strategy instance)
        self._strategies: Dict[str, BaseStrategy] = {}
        
        # Signal handlers (callbacks for when signals are generated)
        self._signal_handlers: List[Callable[[TradeSignal], Any]] = []
        
        # Running state
        self._running = False
        self._evaluation_task: Optional[asyncio.Task] = None
        
        logger.info("StrategyEngine initialized")
    
    # =========================================================================
    # Strategy Management
    # =========================================================================
    
    async def load_strategy(
        self, 
        strategy_type: str, 
        strategy_id: str = None,
        config: Dict[str, Any] = None,
        enable: bool = False
    ) -> BaseStrategy:
        """
        Load a strategy instance.
        
        Args:
            strategy_type: Type of strategy (e.g., "sharp_line")
            strategy_id: Optional ID (generated if not provided)
            config: Optional configuration overrides
            enable: Whether to enable immediately
        
        Returns:
            The loaded strategy instance
        """
        if strategy_type not in STRATEGY_REGISTRY:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # Check if a strategy of this type already exists and remove it
        # This prevents duplicate strategies generating duplicate signals
        existing_ids = [
            sid for sid, s in self._strategies.items() 
            if s.STRATEGY_TYPE == strategy_type
        ]
        for existing_id in existing_ids:
            logger.info(f"Replacing existing {strategy_type} strategy: {existing_id}")
            await self.unload_strategy(existing_id)
        
        # Generate ID if not provided
        if not strategy_id:
            strategy_id = str(uuid.uuid4())
        
        # Create strategy instance
        strategy_class = STRATEGY_REGISTRY[strategy_type]
        strategy = strategy_class(strategy_id, config)
        
        # Store in active strategies
        self._strategies[strategy_id] = strategy
        
        if enable:
            strategy.enable()
        
        logger.info(f"Loaded strategy: {strategy.STRATEGY_NAME} ({strategy_id})")
        
        return strategy
    
    async def unload_strategy(self, strategy_id: str) -> None:
        """Unload a strategy."""
        if strategy_id in self._strategies:
            strategy = self._strategies[strategy_id]
            strategy.disable()
            del self._strategies[strategy_id]
            logger.info(f"Unloaded strategy: {strategy_id}")
    
    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        """Get a strategy by ID."""
        return self._strategies.get(strategy_id)
    
    def get_all_strategies(self) -> Dict[str, BaseStrategy]:
        """Get all loaded strategies."""
        return self._strategies.copy()
    
    def get_enabled_strategies(self) -> List[BaseStrategy]:
        """Get all enabled strategies."""
        return [s for s in self._strategies.values() if s.is_enabled]
    
    async def enable_strategy(self, strategy_id: str) -> bool:
        """Enable a strategy."""
        strategy = self._strategies.get(strategy_id)
        if strategy:
            strategy.enable()
            return True
        return False
    
    async def disable_strategy(self, strategy_id: str) -> bool:
        """Disable a strategy."""
        strategy = self._strategies.get(strategy_id)
        if strategy:
            strategy.disable()
            return True
        return False
    
    async def update_strategy_config(
        self, 
        strategy_id: str, 
        config: Dict[str, Any]
    ) -> bool:
        """Update a strategy's configuration."""
        strategy = self._strategies.get(strategy_id)
        if strategy:
            strategy.update_config(config)
            return True
        return False
    
    # =========================================================================
    # Signal Generation
    # =========================================================================
    
    async def evaluate_game(self, game_state: GameState) -> List[TradeSignal]:
        """
        Run all enabled strategies on a game state.
        
        Args:
            game_state: Current game state to evaluate
        
        Returns:
            List of all generated signals
        """
        all_signals = []
        
        for strategy in self.get_enabled_strategies():
            try:
                signals = await strategy.evaluate(game_state)
                all_signals.extend(signals)
                
                # Notify handlers for each signal
                for signal in signals:
                    await self._notify_signal_handlers(signal)
                    
            except Exception as e:
                logger.error(
                    f"Error evaluating strategy {strategy.STRATEGY_NAME}: {e}",
                    exc_info=True
                )
        
        return all_signals
    
    async def evaluate_all_games(self) -> Dict[str, List[TradeSignal]]:
        """
        Evaluate all active games with all enabled strategies.
        
        Returns:
            Dictionary mapping game_id to list of signals
        """
        aggregator = get_aggregator()
        all_signals = {}
        
        for game_id, game_state in aggregator.get_all_game_states().items():
            signals = await self.evaluate_game(game_state)
            if signals:
                all_signals[game_id] = signals
        
        # Log summary if signals were generated
        if all_signals:
            total_signals = sum(len(s) for s in all_signals.values())
            logger.info(f"Strategy evaluation: {total_signals} signals from {len(all_signals)} games")
        
        return all_signals
    
    # =========================================================================
    # Signal Handlers
    # =========================================================================
    
    def add_signal_handler(self, handler: Callable[[TradeSignal], Any]) -> None:
        """Add a handler to be called when signals are generated."""
        self._signal_handlers.append(handler)
    
    def remove_signal_handler(self, handler: Callable[[TradeSignal], Any]) -> None:
        """Remove a signal handler."""
        if handler in self._signal_handlers:
            self._signal_handlers.remove(handler)
    
    async def _notify_signal_handlers(self, signal: TradeSignal) -> None:
        """Notify all handlers of a new signal."""
        for handler in self._signal_handlers:
            try:
                result = handler(signal)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in signal handler: {e}")
    
    # =========================================================================
    # Background Evaluation Loop
    # =========================================================================
    
    async def start(self) -> None:
        """Start the strategy evaluation loop."""
        if self._running:
            return
        
        self._running = True
        
        # Start periodic evaluation task
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        
        logger.info("StrategyEngine started")
    
    async def stop(self) -> None:
        """Stop the strategy evaluation loop."""
        self._running = False
        
        # Cancel evaluation task
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("StrategyEngine stopped")
    
    async def _evaluation_loop(self) -> None:
        """Periodic strategy evaluation loop."""
        while self._running:
            try:
                await asyncio.sleep(settings.strategy_eval_interval)
                
                if self.get_enabled_strategies():
                    await self.evaluate_all_games()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evaluation loop: {e}")
                await asyncio.sleep(5)


# =============================================================================
# Singleton Instance
# =============================================================================

_strategy_engine: Optional[StrategyEngine] = None


def get_strategy_engine() -> StrategyEngine:
    """Get or create the global StrategyEngine instance."""
    global _strategy_engine
    if _strategy_engine is None:
        _strategy_engine = StrategyEngine()
    return _strategy_engine

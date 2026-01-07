"""
Base strategy class for all trading strategies.
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """Base class for all trading strategies."""

    def __init__(self, strategy_id: str, config: Dict[str, Any]):
        self.strategy_id = strategy_id
        self.config = config
        self.is_enabled = False
        logger.info(f"Strategy initialized: {self.__class__.__name__}")

    @abstractmethod
    async def evaluate(self, market_data: dict, nba_data: dict, odds_data: dict) -> Optional[dict]:
        """
        Evaluate market conditions and generate trade signal.

        Returns:
            Optional trade signal dictionary or None.
        """
        pass

    def enable(self):
        """Enable the strategy."""
        self.is_enabled = True
        logger.info(f"Strategy enabled: {self.__class__.__name__}")

    def disable(self):
        """Disable the strategy."""
        self.is_enabled = False
        logger.info(f"Strategy disabled: {self.__class__.__name__}")

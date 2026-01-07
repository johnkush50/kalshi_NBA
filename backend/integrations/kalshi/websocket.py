"""
Kalshi WebSocket client for real-time orderbook data.
"""

import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class KalshiWebSocketClient:
    """Kalshi WebSocket client (skeleton)."""

    def __init__(self):
        self.ws_url = settings.kalshi_ws_url
        logger.info("KalshiWebSocketClient initialized")

    async def connect(self):
        """Connect to Kalshi WebSocket."""
        # TODO: Implement WebSocket connection
        logger.info("Connecting to Kalshi WebSocket")

    async def subscribe_to_markets(self, tickers: list):
        """Subscribe to orderbook updates for markets."""
        # TODO: Implement subscription logic
        logger.info(f"Subscribing to {len(tickers)} markets")

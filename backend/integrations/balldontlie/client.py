"""
balldontlie.io API client for NBA data and odds.
"""

import logging
from typing import Optional, Dict, Any

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class BallDontLieClient:
    """balldontlie.io API client (skeleton)."""

    def __init__(self):
        self.api_url = settings.balldontlie_api_url
        self.api_key = settings.balldontlie_api_key
        logger.info("BallDontLieClient initialized")

    async def get_games(self, date: str) -> Dict[str, Any]:
        """Get NBA games for a specific date."""
        # TODO: Implement API call
        logger.info(f"Getting games for date: {date}")
        return {}

    async def get_live_box_scores(self) -> Dict[str, Any]:
        """Get live box scores for ongoing games."""
        # TODO: Implement API call
        logger.info("Getting live box scores")
        return {}

    async def get_odds(self, game_ids: list) -> Dict[str, Any]:
        """Get betting odds for games."""
        # TODO: Implement API call
        logger.info(f"Getting odds for {len(game_ids)} games")
        return {}

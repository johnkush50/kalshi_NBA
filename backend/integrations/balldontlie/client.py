"""
balldontlie.io API Client.

Provides access to NBA game data, live box scores, and betting odds.
API Documentation: https://www.balldontlie.io/
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config.settings import settings
from backend.integrations.balldontlie.exceptions import (
    BallDontLieError,
    BallDontLieAuthError,
    BallDontLieAPIError,
    BallDontLieNotFoundError,
    BallDontLieRateLimitError,
    GameMatchError
)

logger = logging.getLogger(__name__)


class BallDontLieClient:
    """
    balldontlie.io API client for NBA data.
    
    Provides methods for:
    - Fetching games by date
    - Getting live box scores
    - Fetching betting odds
    - Matching Kalshi games to NBA games
    """
    
    def __init__(self):
        """Initialize the client with API credentials from settings."""
        self.base_url = settings.balldontlie_api_url.rstrip('/')
        self.api_key = settings.balldontlie_api_key
        self._client: Optional[httpx.AsyncClient] = None
        logger.info("BallDontLieClient initialized")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": self.api_key,  # No "Bearer" prefix
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise BallDontLieAuthError("Invalid API key")
        elif response.status_code == 404:
            raise BallDontLieNotFoundError(
                f"Resource not found",
                status_code=404,
                response=response.json() if response.content else None
            )
        elif response.status_code == 429:
            raise BallDontLieRateLimitError(
                "Rate limit exceeded",
                status_code=429,
                response=response.json() if response.content else None
            )
        else:
            raise BallDontLieAPIError(
                f"API request failed with status {response.status_code}",
                status_code=response.status_code,
                response=response.json() if response.content else None
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(BallDontLieRateLimitError)
    )
    async def _request(self, method: str, path: str, params: Dict = None, json: Dict = None) -> Dict[str, Any]:
        """Make an API request with retry logic."""
        client = await self._get_client()
        
        logger.debug(f"BallDontLie API request: {method} {path} params={params}")
        
        response = await client.request(method, path, params=params, json=json)
        
        return await self._handle_response(response)
    
    # =========================================================================
    # Teams API
    # =========================================================================
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all NBA teams.
        
        Returns:
            List of team objects with id, name, abbreviation, etc.
        """
        result = await self._request("GET", "/v1/teams")
        return result.get("data", [])
    
    async def get_team(self, team_id: int) -> Dict[str, Any]:
        """Get a specific team by ID."""
        result = await self._request("GET", f"/v1/teams/{team_id}")
        return result.get("data", {})
    
    # =========================================================================
    # Games API
    # =========================================================================
    
    async def get_games(
        self,
        dates: List[str] = None,
        seasons: List[int] = None,
        team_ids: List[int] = None,
        cursor: int = None,
        per_page: int = 25
    ) -> Dict[str, Any]:
        """
        Get NBA games with optional filters.
        
        Args:
            dates: List of dates in YYYY-MM-DD format
            seasons: List of season years (e.g., [2024, 2025])
            team_ids: Filter by team IDs
            cursor: Pagination cursor
            per_page: Results per page (max 100)
        
        Returns:
            Dict with 'data' (list of games) and 'meta' (pagination info)
        """
        params = {"per_page": per_page}
        
        if dates:
            params["dates[]"] = dates
        if seasons:
            params["seasons[]"] = seasons
        if team_ids:
            params["team_ids[]"] = team_ids
        if cursor:
            params["cursor"] = cursor
        
        return await self._request("GET", "/v1/games", params=params)
    
    async def get_games_for_date(self, game_date: str) -> List[Dict[str, Any]]:
        """
        Get all NBA games for a specific date.
        
        Args:
            game_date: Date in YYYY-MM-DD format
        
        Returns:
            List of game objects
        """
        result = await self.get_games(dates=[game_date], per_page=100)
        return result.get("data", [])
    
    async def get_game(self, game_id: int) -> Dict[str, Any]:
        """Get a specific game by ID."""
        result = await self._request("GET", f"/v1/games/{game_id}")
        return result.get("data", {})
    
    # =========================================================================
    # Box Scores API
    # =========================================================================
    
    async def get_box_scores(
        self,
        game_ids: List[int] = None,
        date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get box scores for games.
        
        Args:
            game_ids: List of game IDs to fetch box scores for
            date: Date in YYYY-MM-DD format (alternative to game_ids)
        
        Returns:
            List of box score objects with player stats
        """
        params = {}
        if game_ids:
            params["game_ids[]"] = game_ids
        if date:
            params["date"] = date
        
        result = await self._request("GET", "/v1/box_scores", params=params)
        return result.get("data", [])
    
    async def get_live_box_scores(self) -> List[Dict[str, Any]]:
        """
        Get box scores for currently live games.
        
        Returns:
            List of box score objects for games in progress
        """
        result = await self._request("GET", "/v1/box_scores/live")
        return result.get("data", [])
    
    # =========================================================================
    # Odds API
    # =========================================================================
    
    async def get_odds(
        self,
        game_ids: List[int] = None,
        date: str = None,
        sportsbooks: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get betting odds for games.
        
        Args:
            game_ids: List of game IDs
            date: Date in YYYY-MM-DD format
            sportsbooks: Filter by sportsbook names (e.g., ["draftkings", "fanduel"])
        
        Returns:
            List of odds objects with moneyline, spread, and total
        """
        params = {}
        if game_ids:
            # Format as repeated params: game_ids[]=123&game_ids[]=456
            for gid in game_ids:
                if "game_ids[]" not in params:
                    params["game_ids[]"] = []
                params["game_ids[]"].append(gid)
        if date:
            params["dates[]"] = [date]
        if sportsbooks:
            params["sportsbooks[]"] = sportsbooks
        
        logger.debug(f"Fetching odds with params: {params}")
        result = await self._request("GET", "/nba/v2/odds", params=params)
        odds_data = result.get("data", [])
        logger.debug(f"Received {len(odds_data)} odds records")
        return odds_data
    
    # =========================================================================
    # Game Matching (Kalshi <-> NBA)
    # =========================================================================
    
    async def find_nba_game(
        self,
        game_date: str,
        away_team_abbr: str,
        home_team_abbr: str
    ) -> Dict[str, Any]:
        """
        Find an NBA game matching the given date and teams.
        
        Used to match Kalshi events to NBA games.
        
        Args:
            game_date: Date in YYYY-MM-DD format
            away_team_abbr: Away team abbreviation (e.g., "DAL")
            home_team_abbr: Home team abbreviation (e.g., "UTA")
        
        Returns:
            NBA game object if found
        
        Raises:
            GameMatchError: If no matching game found
        """
        games = await self.get_games_for_date(game_date)
        
        for game in games:
            visitor_abbr = game.get("visitor_team", {}).get("abbreviation", "")
            home_abbr = game.get("home_team", {}).get("abbreviation", "")
            
            if visitor_abbr.upper() == away_team_abbr.upper() and home_abbr.upper() == home_team_abbr.upper():
                logger.info(f"Matched NBA game: {away_team_abbr} @ {home_team_abbr} -> ID {game['id']}")
                return game
        
        raise GameMatchError(
            f"No NBA game found for {away_team_abbr} @ {home_team_abbr} on {game_date}"
        )
    
    async def match_kalshi_game(self, kalshi_event_ticker: str) -> Dict[str, Any]:
        """
        Match a Kalshi event ticker to an NBA game.
        
        Args:
            kalshi_event_ticker: Kalshi event ticker (e.g., "KXNBAGAME-26JAN08DALUTA")
        
        Returns:
            NBA game object with id, teams, date, etc.
        
        Raises:
            GameMatchError: If parsing fails or no match found
        """
        from backend.utils.ticker_parser import extract_game_info_from_kalshi_ticker
        
        try:
            # Parse the Kalshi ticker
            game_info = extract_game_info_from_kalshi_ticker(kalshi_event_ticker)
            
            # Find the matching NBA game
            return await self.find_nba_game(
                game_date=game_info["date"],
                away_team_abbr=game_info["away_team_abbr"],
                home_team_abbr=game_info["home_team_abbr"]
            )
        except ValueError as e:
            raise GameMatchError(f"Failed to parse Kalshi ticker: {e}")

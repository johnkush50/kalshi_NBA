"""
Kalshi REST API client.

Handles RSA-PSS authentication and requests to Kalshi API.
Implements retry logic with exponential backoff.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import httpx

from backend.config.settings import settings, get_kalshi_private_key
from backend.integrations.kalshi.auth import KalshiAuth
from backend.integrations.kalshi.exceptions import (
    KalshiAPIError,
    KalshiAuthError,
    KalshiNotFoundError,
    KalshiRateLimitError,
)

logger = logging.getLogger(__name__)

# NBA series tickers for different market types
NBA_SERIES_TICKERS = ["KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL"]


class KalshiClient:
    """
    Kalshi REST API client with RSA-PSS authentication.
    
    Provides async methods for interacting with Kalshi's trading API.
    Implements retry logic with exponential backoff for resilience.
    """

    def __init__(self):
        """Initialize the Kalshi client with authentication from settings."""
        self.api_url = settings.kalshi_api_url
        self.api_key = settings.kalshi_api_key
        
        # Load private key and initialize auth
        try:
            private_key = get_kalshi_private_key()
            self.auth = KalshiAuth(self.api_key, private_key)
        except Exception as e:
            logger.error(f"Failed to initialize Kalshi auth: {e}")
            raise KalshiAuthError(f"Failed to initialize authentication: {e}")
        
        # HTTP client configuration
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3
        self.retry_delay = 1.0  # Base delay in seconds
        
        logger.info("KalshiClient initialized with RSA-PSS authentication")

    def _get_path(self, endpoint: str) -> str:
        """Get the full API path for an endpoint."""
        return f"/trade-api/v2{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_body: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the Kalshi API.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., "/markets")
            params: Query parameters
            json_body: JSON body for POST/PUT requests
        
        Returns:
            API response as dictionary
        
        Raises:
            KalshiAPIError: On API errors
            KalshiAuthError: On authentication errors
            KalshiNotFoundError: When resource not found
            KalshiRateLimitError: On rate limit exceeded
        """
        path = self._get_path(endpoint)
        # Use string concatenation instead of urljoin (urljoin replaces last path segment)
        base = self.api_url.rstrip('/')
        url = f"{base}{endpoint}"
        logger.info(f"Request URL: {url}")
        logger.info(f"Signature path: {path}")
        
        # Prepare body string for signature
        body_str = ""
        if json_body:
            body_str = json.dumps(json_body, separators=(',', ':'))
        
        # Get auth headers
        auth_headers = self.auth.get_auth_headers(method, path, body_str)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **auth_headers,
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request {method} {endpoint} (attempt {attempt + 1}/{self.max_retries})")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method == "GET":
                        response = await client.get(url, params=params, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, json=json_body, headers=headers)
                    elif method == "DELETE":
                        response = await client.delete(url, params=params, headers=headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle response
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response content: {response.text[:500]}")
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        logger.error(f"Raw response: {response.text}")
                        raise KalshiAPIError(f"Invalid JSON response: {response.text[:200]}")
                elif response.status_code == 401:
                    raise KalshiAuthError("Authentication failed - check API key and private key")
                elif response.status_code == 404:
                    try:
                        error_body = response.json() if response.content else None
                    except Exception:
                        error_body = {"raw": response.text[:200]}
                    raise KalshiNotFoundError(
                        f"Resource not found: {endpoint}",
                        status_code=404,
                        response=error_body
                    )
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    error_body = response.json() if response.content else {}
                    raise KalshiAPIError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                        response=error_body
                    )
                    
            except (KalshiAuthError, KalshiNotFoundError):
                raise
            except KalshiAPIError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
            except httpx.HTTPError as e:
                last_exception = KalshiAPIError(f"HTTP error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"HTTP error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
        
        raise last_exception or KalshiAPIError("Request failed after all retries")

    async def get_exchange_status(self) -> Dict[str, Any]:
        """
        Get exchange status to test connection and authentication.
        
        Returns:
            Exchange status information
        """
        return await self._request("GET", "/exchange/status")

    async def get_events(
        self,
        series_ticker: Optional[str] = None,
        status: str = "open",
        with_nested_markets: bool = True,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get events with optional filtering.
        
        Args:
            series_ticker: Filter by series ticker (e.g., "KXNBAGAME")
            status: Event status filter ("open", "closed", etc.)
            with_nested_markets: Include market data in response
            limit: Maximum number of events to return
            cursor: Pagination cursor
        
        Returns:
            Events response with pagination
        """
        params = {
            "status": status,
            "with_nested_markets": str(with_nested_markets).lower(),
            "limit": limit,
        }
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor
        
        return await self._request("GET", "/events", params=params)

    async def get_event(
        self,
        event_ticker: str,
        with_nested_markets: bool = True,
    ) -> Dict[str, Any]:
        """
        Get single event by ticker.
        
        Args:
            event_ticker: Event ticker (e.g., "KXNBAGAME-26JAN06DALSAC")
            with_nested_markets: Include market data in response
        
        Returns:
            Event details with optional markets
        """
        params = {"with_nested_markets": str(with_nested_markets).lower()}
        return await self._request("GET", f"/events/{event_ticker}", params=params)

    async def get_markets(
        self,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get markets with optional filtering.
        
        Args:
            event_ticker: Filter by event ticker
            series_ticker: Filter by series ticker
            status: Market status filter
            limit: Maximum number of markets to return
            cursor: Pagination cursor
        
        Returns:
            Markets response with pagination
        """
        params = {"limit": limit}
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        
        return await self._request("GET", "/markets", params=params)

    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """
        Get single market by ticker.
        
        Args:
            ticker: Market ticker
        
        Returns:
            Market details
        """
        response = await self._request("GET", f"/markets/{ticker}")
        return response.get("market", response)

    async def get_market_orderbook(self, ticker: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get orderbook for a market.
        
        Args:
            ticker: Market ticker
            depth: Number of price levels to return
        
        Returns:
            Orderbook with bids and asks
        """
        params = {"depth": depth}
        return await self._request("GET", f"/markets/{ticker}/orderbook", params=params)

    async def get_nba_games_for_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all NBA games/markets for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of games with their markets grouped by event
        
        Example:
            games = await client.get_nba_games_for_date("2026-01-08")
            # Returns: [
            #     {
            #         "event_ticker": "KXNBAGAME-26JAN08LALSAC",
            #         "away_team": "LAL",
            #         "home_team": "SAC",
            #         "game_date": "2026-01-08",
            #         "market_count": 3,
            #         "markets": {...}
            #     }
            # ]
        """
        # Parse date to get components for ticker matching
        try:
            game_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD.")
        
        # Format for ticker matching: YYmmmDD (e.g., "26JAN08")
        date_pattern = game_date.strftime("%y%b%d").upper()
        
        games = {}
        
        # Query each NBA series for events
        for series in NBA_SERIES_TICKERS:
            try:
                response = await self.get_events(
                    series_ticker=series,
                    status="open",
                    with_nested_markets=True,
                )
                
                events = response.get("events", [])
                
                for event in events:
                    event_ticker = event.get("event_ticker", "")
                    
                    # Check if event matches our date pattern
                    if date_pattern in event_ticker.upper():
                        # Extract team info from ticker
                        # Format: KXNBAGAME-26JAN08LALSAC
                        ticker_parts = event_ticker.upper().split("-")
                        if len(ticker_parts) >= 2:
                            date_teams = ticker_parts[1]
                            # Remove date portion to get teams
                            teams_str = date_teams.replace(date_pattern, "")
                            
                            if len(teams_str) >= 6:
                                away_team = teams_str[:3]
                                home_team = teams_str[3:6]
                                
                                # Create unique game key based on teams
                                game_key = f"{away_team}@{home_team}"
                                
                                if game_key not in games:
                                    games[game_key] = {
                                        "event_ticker": event_ticker,
                                        "away_team": away_team,
                                        "home_team": home_team,
                                        "game_date": date,
                                        "title": event.get("title", ""),
                                        "markets": {},
                                        "market_count": 0,
                                    }
                                
                                # Categorize markets by type
                                market_type = self._get_market_type_from_series(series)
                                markets = event.get("markets", [])
                                
                                games[game_key]["markets"][market_type] = {
                                    "event_ticker": event_ticker,
                                    "markets": markets,
                                }
                                games[game_key]["market_count"] += len(markets)
                
            except KalshiAPIError as e:
                logger.warning(f"Failed to fetch {series} events: {e}")
                continue
        
        return list(games.values())

    def _get_market_type_from_series(self, series: str) -> str:
        """Map series ticker to market type."""
        mapping = {
            "KXNBAGAME": "moneyline",
            "KXNBASPREAD": "spread",
            "KXNBATOTAL": "total",
        }
        return mapping.get(series, "unknown")

    async def close(self):
        """Close the client (for cleanup)."""
        logger.info("KalshiClient closed")

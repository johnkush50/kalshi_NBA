"""
Data Aggregator for the Kalshi NBA Paper Trading system.

Manages unified game state by combining data from:
- Kalshi REST API and WebSocket (orderbook data)
- balldontlie.io API (NBA live data and betting odds)

Provides background polling and event subscription for strategies.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Callable, List, Awaitable, Any
from enum import Enum

from backend.config.settings import settings
from backend.config.supabase import get_supabase_client
from backend.models.game_state import (
    GameState, GamePhase, MarketState, OrderbookState,
    NBAGameState, OddsState, ConsensusOdds
)
from backend.utils.odds_calculator import (
    american_to_implied_probability,
    kalshi_price_to_probability,
    calculate_consensus_probability,
    remove_vig
)
from backend.database import helpers as db

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events that subscribers can listen for."""
    ORDERBOOK_UPDATE = "orderbook_update"
    NBA_UPDATE = "nba_update"
    ODDS_UPDATE = "odds_update"
    STATE_CHANGE = "state_change"
    GAME_LOADED = "game_loaded"
    GAME_UNLOADED = "game_unloaded"


# Type alias for subscriber callbacks
SubscriberCallback = Callable[[str, GameState, EventType], Awaitable[None]]


class DataAggregator:
    """
    Central data aggregator that maintains unified game state.
    
    Responsibilities:
    - Load games from database and initialize GameState
    - Poll NBA live data and betting odds on intervals
    - Receive Kalshi orderbook updates via WebSocket
    - Notify subscribers when data changes
    - Provide unified state access for strategies
    """
    
    def __init__(self):
        """Initialize the data aggregator."""
        self._game_states: Dict[str, GameState] = {}
        self._ticker_to_game: Dict[str, str] = {}  # market_ticker -> game_id
        self._subscribers: List[SubscriberCallback] = []
        
        # Background task references
        self._polling_task: Optional[asyncio.Task] = None
        self._websocket_task: Optional[asyncio.Task] = None
        self._running: bool = False
        
        # Clients (lazy initialization)
        self._kalshi_client = None
        self._kalshi_ws = None
        self._bdl_client = None
        
        logger.debug("DataAggregator initialized")
    
    # =========================================================================
    # Client Initialization
    # =========================================================================
    
    def _get_kalshi_client(self):
        """Get or create Kalshi REST client."""
        if self._kalshi_client is None:
            from backend.integrations.kalshi.client import KalshiClient
            self._kalshi_client = KalshiClient()
        return self._kalshi_client
    
    def _get_kalshi_ws(self):
        """Get or create Kalshi WebSocket client."""
        if self._kalshi_ws is None:
            from backend.integrations.kalshi.websocket import KalshiWebSocketClient
            self._kalshi_ws = KalshiWebSocketClient()
        return self._kalshi_ws
    
    def _get_bdl_client(self):
        """Get or create balldontlie.io client."""
        if self._bdl_client is None:
            from backend.integrations.balldontlie.client import BallDontLieClient
            self._bdl_client = BallDontLieClient()
        return self._bdl_client
    
    # =========================================================================
    # Game Management
    # =========================================================================
    
    async def load_game(self, game_id: str) -> Optional[GameState]:
        """
        Load a game into the aggregator.
        
        Fetches game data from database, initializes GameState,
        and starts tracking orderbooks.
        
        Args:
            game_id: UUID of the game to load
            
        Returns:
            GameState if successful, None if game not found
        """
        logger.info(f"Loading game: {game_id}")
        
        try:
            # Fetch game from database
            game_data = await db.get_game_by_id(game_id)
            if not game_data:
                logger.error(f"Game not found: {game_id}")
                return None
            
            # Parse game date
            game_date = game_data.get("game_date")
            if isinstance(game_date, str):
                try:
                    game_date = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                except ValueError:
                    game_date = datetime.utcnow()
            elif game_date is None:
                game_date = datetime.utcnow()
            
            # Determine game phase
            status = game_data.get("status", "scheduled")
            phase = self._status_to_phase(status)
            
            # Create initial GameState
            game_state = GameState(
                game_id=game_id,
                event_ticker=game_data.get("kalshi_event_ticker", ""),
                home_team=game_data.get("home_team", ""),
                away_team=game_data.get("away_team", ""),
                game_date=game_date,
                phase=phase,
                is_active=game_data.get("is_active", True)
            )
            
            # Initialize NBA state if we have NBA game ID
            nba_game_id = game_data.get("nba_game_id")
            if nba_game_id:
                game_state.nba_state = NBAGameState(
                    nba_game_id=nba_game_id,
                    home_team=game_data.get("home_team", ""),
                    away_team=game_data.get("away_team", ""),
                    home_team_id=game_data.get("home_team_id"),
                    away_team_id=game_data.get("away_team_id")
                )
            
            # Fetch markets for this game
            markets = await db.get_markets_for_game(game_id)
            for market in markets:
                market_state = MarketState(
                    id=market.get("id", ""),
                    ticker=market.get("ticker", ""),
                    market_type=market.get("market_type", ""),
                    strike_value=Decimal(str(market.get("strike_value", 0))) if market.get("strike_value") else None,
                    team=market.get("side")
                )
                game_state.markets[market_state.ticker] = market_state
                self._ticker_to_game[market_state.ticker] = game_id
            
            # Store game state
            self._game_states[game_id] = game_state
            
            # Refresh data
            await self._refresh_kalshi_orderbooks(game_id)
            if game_state.has_nba_data:
                await self._refresh_nba_data(game_id)
                await self._refresh_odds(game_id)
            
            # Notify subscribers
            await self._notify_subscribers(game_id, game_state, EventType.GAME_LOADED)
            
            logger.info(f"Game loaded successfully: {game_id} ({game_state.away_team} @ {game_state.home_team})")
            return game_state
            
        except Exception as e:
            logger.error(f"Error loading game {game_id}: {e}", exc_info=True)
            return None
    
    async def unload_game(self, game_id: str) -> bool:
        """
        Stop tracking a game and remove from aggregator.
        
        Args:
            game_id: UUID of the game to unload
            
        Returns:
            True if game was unloaded, False if not found
        """
        if game_id not in self._game_states:
            logger.warning(f"Game not loaded: {game_id}")
            return False
        
        game_state = self._game_states[game_id]
        
        # Remove ticker mappings
        for ticker in game_state.markets.keys():
            self._ticker_to_game.pop(ticker, None)
        
        # Remove game state
        del self._game_states[game_id]
        
        # Notify subscribers
        await self._notify_subscribers(game_id, game_state, EventType.GAME_UNLOADED)
        
        logger.info(f"Game unloaded: {game_id}")
        return True
    
    def get_game_state(self, game_id: str) -> Optional[GameState]:
        """Get current state for a game."""
        return self._game_states.get(game_id)
    
    def get_all_game_states(self) -> Dict[str, GameState]:
        """Get all active game states."""
        return self._game_states.copy()
    
    def get_game_ids(self) -> List[str]:
        """Get list of all loaded game IDs."""
        return list(self._game_states.keys())
    
    # =========================================================================
    # Data Refresh Methods
    # =========================================================================
    
    async def _refresh_kalshi_orderbooks(self, game_id: str) -> None:
        """Refresh orderbook data for all markets in a game."""
        game_state = self._game_states.get(game_id)
        if not game_state:
            return
        
        client = self._get_kalshi_client()
        updated = False
        
        for ticker, market in game_state.markets.items():
            try:
                # Fetch market data from Kalshi
                market_data = await client.get_market(ticker)
                if market_data:
                    # Update orderbook
                    market.orderbook = OrderbookState(
                        ticker=ticker,
                        yes_bid=Decimal(str(market_data.get("yes_bid", 0))) if market_data.get("yes_bid") else None,
                        yes_ask=Decimal(str(market_data.get("yes_ask", 0))) if market_data.get("yes_ask") else None,
                        no_bid=Decimal(str(market_data.get("no_bid", 0))) if market_data.get("no_bid") else None,
                        no_ask=Decimal(str(market_data.get("no_ask", 0))) if market_data.get("no_ask") else None,
                        last_updated=datetime.utcnow()
                    )
                    
                    # Calculate implied probability from Kalshi price
                    if market.orderbook.mid_price is not None:
                        game_state.kalshi_probabilities[ticker] = kalshi_price_to_probability(
                            market.orderbook.mid_price
                        )
                    
                    updated = True
                    
            except Exception as e:
                logger.warning(f"Error fetching orderbook for {ticker}: {e}")
                continue
        
        if updated:
            game_state.last_updated = datetime.utcnow()
            await self._notify_subscribers(game_id, game_state, EventType.ORDERBOOK_UPDATE)
    
    async def _refresh_nba_data(self, game_id: str) -> None:
        """Refresh NBA live data for a game."""
        game_state = self._game_states.get(game_id)
        if not game_state or not game_state.nba_state:
            return
        
        nba_game_id = game_state.nba_state.nba_game_id
        if not nba_game_id:
            return
        
        try:
            client = self._get_bdl_client()
            
            # Try to get live box score first
            live_data = await client.get_live_box_scores()
            game_data = None
            
            for game in live_data:
                if game.get("game", {}).get("id") == nba_game_id:
                    game_data = game
                    break
            
            if game_data:
                game_info = game_data.get("game", {})
                game_state.nba_state.status = game_info.get("status", "scheduled")
                game_state.nba_state.period = game_info.get("period", 0)
                game_state.nba_state.time_remaining = game_info.get("time", "")
                game_state.nba_state.home_score = game_info.get("home_team_score", 0)
                game_state.nba_state.away_score = game_info.get("visitor_team_score", 0)
                game_state.nba_state.last_updated = datetime.utcnow()
                
                # Update game phase
                game_state.phase = self._status_to_phase(game_state.nba_state.status)
                
                # Store in database
                await db.store_nba_live_data(game_id, {
                    "period": game_state.nba_state.period,
                    "time_remaining": game_state.nba_state.time_remaining,
                    "home_score": game_state.nba_state.home_score,
                    "away_score": game_state.nba_state.away_score,
                    "game_status": game_state.nba_state.status,
                    "raw_data": game_data
                })
                
                game_state.last_updated = datetime.utcnow()
                await self._notify_subscribers(game_id, game_state, EventType.NBA_UPDATE)
            else:
                # Game not live, try to get scheduled game data
                game_info = await client.get_game(nba_game_id)
                if game_info:
                    game_state.nba_state.status = game_info.get("status", "scheduled")
                    game_state.phase = self._status_to_phase(game_state.nba_state.status)
                    
        except Exception as e:
            logger.warning(f"Error refreshing NBA data for game {game_id}: {e}")
    
    async def _refresh_odds(self, game_id: str) -> None:
        """Refresh betting odds for a game."""
        game_state = self._game_states.get(game_id)
        if not game_state or not game_state.nba_state:
            logger.debug(f"Skipping odds refresh - no game state or NBA state for {game_id}")
            return
        
        nba_game_id = game_state.nba_state.nba_game_id
        if not nba_game_id:
            logger.debug(f"Skipping odds refresh - no NBA game ID for {game_id}")
            return
        
        try:
            logger.info(f"Fetching odds for NBA game ID: {nba_game_id}")
            client = self._get_bdl_client()
            odds_data = await client.get_odds(game_ids=[nba_game_id])
            
            logger.info(f"Odds API returned {len(odds_data) if odds_data else 0} records")
            
            if not odds_data:
                logger.info(f"No odds data returned from API for game {nba_game_id}")
                return
            
            # API returns flat records: one per vendor with direct fields
            # Structure: {game_id, vendor, moneyline_home_odds, spread_home_value, ...}
            home_ml_odds = []
            away_ml_odds = []
            
            for item in odds_data:
                item_game_id = item.get("game_id")
                if item_game_id != nba_game_id:
                    continue
                
                vendor = item.get("vendor", "unknown")
                
                odds_state = OddsState(
                    vendor=vendor,
                    timestamp=datetime.utcnow(),
                    moneyline_home=item.get("moneyline_home_odds"),
                    moneyline_away=item.get("moneyline_away_odds"),
                    spread_home_value=Decimal(str(item.get("spread_home_value"))) if item.get("spread_home_value") else None,
                    spread_home_odds=item.get("spread_home_odds"),
                    spread_away_value=Decimal(str(item.get("spread_away_value"))) if item.get("spread_away_value") else None,
                    spread_away_odds=item.get("spread_away_odds"),
                    total_value=Decimal(str(item.get("total_value"))) if item.get("total_value") else None,
                    total_over_odds=item.get("total_over_odds"),
                    total_under_odds=item.get("total_under_odds")
                )
                
                game_state.odds[vendor] = odds_state
                
                # Collect moneyline odds for consensus
                if odds_state.moneyline_home:
                    home_ml_odds.append(odds_state.moneyline_home)
                if odds_state.moneyline_away:
                    away_ml_odds.append(odds_state.moneyline_away)
            
            # Calculate consensus
            if home_ml_odds and away_ml_odds:
                game_state.consensus = self._calculate_consensus(home_ml_odds, away_ml_odds, odds_data)
            
            # Store in database (pass the raw odds data)
            await db.store_betting_odds(game_id, {"data": odds_data})
            
            game_state.last_updated = datetime.utcnow()
            await self._notify_subscribers(game_id, game_state, EventType.ODDS_UPDATE)
            
            logger.info(f"Loaded odds from {len(game_state.odds)} sportsbooks for game {game_id}")
            
        except Exception as e:
            logger.error(f"Error refreshing odds for game {game_id}: {e}", exc_info=True)
    
    def _calculate_consensus(
        self, 
        home_ml_odds: List[int], 
        away_ml_odds: List[int],
        odds_data: list
    ) -> ConsensusOdds:
        """Calculate consensus odds from multiple sportsbooks."""
        consensus = ConsensusOdds(
            num_sportsbooks=len(home_ml_odds),
            last_updated=datetime.utcnow()
        )
        
        # Calculate consensus moneyline probabilities
        home_prob = calculate_consensus_probability(home_ml_odds, "median")
        away_prob = calculate_consensus_probability(away_ml_odds, "median")
        
        if home_prob and away_prob:
            # Normalize to sum to 1 (remove vig)
            total = home_prob + away_prob
            consensus.home_win_probability = home_prob / total
            consensus.away_win_probability = away_prob / total
        
        # Get median spread and total lines from flat records
        spreads = []
        totals = []
        
        for item in odds_data:
            if item.get("spread_home_value"):
                try:
                    spreads.append(float(item["spread_home_value"]))
                except (ValueError, TypeError):
                    pass
            if item.get("total_value"):
                try:
                    totals.append(float(item["total_value"]))
                except (ValueError, TypeError):
                    pass
        
        if spreads:
            spreads.sort()
            mid = len(spreads) // 2
            consensus.spread_line = Decimal(str(spreads[mid]))
        
        if totals:
            totals.sort()
            mid = len(totals) // 2
            consensus.total_line = Decimal(str(totals[mid]))
        
        return consensus
    
    def _status_to_phase(self, status: str) -> GamePhase:
        """Convert NBA game status to GamePhase."""
        status_lower = status.lower() if status else ""
        
        if status_lower in ("scheduled", ""):
            return GamePhase.SCHEDULED
        elif status_lower in ("in_progress", "live", "1st qtr", "2nd qtr", "3rd qtr", "4th qtr"):
            return GamePhase.LIVE
        elif status_lower == "halftime":
            return GamePhase.HALFTIME
        elif status_lower in ("final", "finished"):
            return GamePhase.FINISHED
        elif status_lower in ("cancelled", "postponed"):
            return GamePhase.CANCELLED
        else:
            return GamePhase.SCHEDULED
    
    # =========================================================================
    # Background Tasks
    # =========================================================================
    
    async def start(self) -> None:
        """Start background polling and WebSocket tasks."""
        if self._running:
            logger.warning("Aggregator already running")
            return
        
        self._running = True
        
        # Start polling loop
        self._polling_task = asyncio.create_task(self._polling_loop())
        
        # Start WebSocket loop (optional, may not be needed if using REST)
        # self._websocket_task = asyncio.create_task(self._websocket_loop())
        
        logger.info("Data aggregator started")
    
    async def stop(self) -> None:
        """Stop all background tasks and cleanup."""
        self._running = False
        
        # Cancel polling task
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None
        
        # Cancel WebSocket task
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass
            self._websocket_task = None
        
        # Close clients
        if self._bdl_client:
            await self._bdl_client.close()
            self._bdl_client = None
        
        if self._kalshi_ws:
            await self._kalshi_ws.disconnect()
            self._kalshi_ws = None
        
        if self._kalshi_client:
            await self._kalshi_client.close()
            self._kalshi_client = None
        
        logger.info("Data aggregator stopped")
    
    async def _polling_loop(self) -> None:
        """Background loop for polling NBA data and odds."""
        nba_counter = 0
        odds_counter = 0
        
        while self._running:
            try:
                # Get current game IDs (copy to avoid modification during iteration)
                game_ids = self.get_game_ids()
                
                for game_id in game_ids:
                    game_state = self._game_states.get(game_id)
                    if not game_state:
                        continue
                    
                    # Only poll live games
                    if game_state.phase in (GamePhase.LIVE, GamePhase.HALFTIME):
                        # Refresh NBA data every nba_poll_interval
                        if nba_counter >= settings.nba_poll_interval:
                            await self._refresh_nba_data(game_id)
                        
                        # Refresh odds every betting_odds_poll_interval
                        if odds_counter >= settings.betting_odds_poll_interval:
                            await self._refresh_odds(game_id)
                        
                        # Always refresh orderbooks for live games
                        await self._refresh_kalshi_orderbooks(game_id)
                    
                    elif game_state.phase == GamePhase.SCHEDULED:
                        # Check periodically if game has started
                        if nba_counter >= settings.nba_poll_interval * 6:  # Every 30 seconds
                            await self._refresh_nba_data(game_id)
                
                # Increment counters
                nba_counter += 1
                odds_counter += 1
                
                # Reset counters
                if nba_counter >= settings.nba_poll_interval:
                    nba_counter = 0
                if odds_counter >= settings.betting_odds_poll_interval:
                    odds_counter = 0
                
                # Sleep for 1 second between iterations
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _websocket_loop(self) -> None:
        """Background loop for WebSocket connection."""
        while self._running:
            try:
                ws = self._get_kalshi_ws()
                
                # Connect if not connected
                if not ws.is_connected:
                    await ws.connect()
                
                # Subscribe to all market tickers
                tickers = list(self._ticker_to_game.keys())
                if tickers:
                    await ws.subscribe(tickers, ["ticker", "orderbook_delta"])
                
                # Process messages
                async for message in ws.listen():
                    if not self._running:
                        break
                    
                    await self._handle_ws_message(message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
    
    async def _handle_ws_message(self, message: dict) -> None:
        """Handle incoming WebSocket message."""
        msg_type = message.get("type")
        
        if msg_type == "ticker":
            ticker = message.get("market_ticker")
            game_id = self._ticker_to_game.get(ticker)
            
            if game_id and game_id in self._game_states:
                game_state = self._game_states[game_id]
                market = game_state.markets.get(ticker)
                
                if market:
                    data = message.get("data", {})
                    market.orderbook = OrderbookState(
                        ticker=ticker,
                        yes_bid=Decimal(str(data.get("yes_bid"))) if data.get("yes_bid") else None,
                        yes_ask=Decimal(str(data.get("yes_ask"))) if data.get("yes_ask") else None,
                        no_bid=Decimal(str(data.get("no_bid"))) if data.get("no_bid") else None,
                        no_ask=Decimal(str(data.get("no_ask"))) if data.get("no_ask") else None,
                        last_updated=datetime.utcnow()
                    )
                    
                    game_state.last_updated = datetime.utcnow()
                    await self._notify_subscribers(game_id, game_state, EventType.ORDERBOOK_UPDATE)
    
    # =========================================================================
    # Event Subscription
    # =========================================================================
    
    def subscribe(self, callback: SubscriberCallback) -> None:
        """Subscribe to game state updates."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.debug(f"Subscriber added, total: {len(self._subscribers)}")
    
    def unsubscribe(self, callback: SubscriberCallback) -> None:
        """Unsubscribe from game state updates."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"Subscriber removed, total: {len(self._subscribers)}")
    
    async def _notify_subscribers(
        self, 
        game_id: str, 
        game_state: GameState, 
        event_type: EventType
    ) -> None:
        """Notify all subscribers of a state change."""
        for callback in self._subscribers:
            try:
                await callback(game_id, game_state, event_type)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")


# Singleton instance
_aggregator: Optional[DataAggregator] = None


def get_aggregator() -> DataAggregator:
    """Get the singleton DataAggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = DataAggregator()
    return _aggregator

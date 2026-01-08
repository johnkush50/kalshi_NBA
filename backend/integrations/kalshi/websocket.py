"""
Kalshi WebSocket client for real-time orderbook data.

Provides async WebSocket connection with automatic reconnection,
subscription management, and orderbook state tracking.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Set
from enum import Enum

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from backend.config.settings import settings, get_kalshi_private_key
from backend.integrations.kalshi.auth import KalshiAuth
from backend.integrations.kalshi.exceptions import KalshiWebSocketError, KalshiAuthError

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class KalshiWebSocketClient:
    """
    Kalshi WebSocket client for real-time market data.
    
    Features:
    - RSA-PSS authentication via headers
    - Automatic reconnection with exponential backoff
    - Subscription state tracking
    - Orderbook snapshot and delta handling
    - Async message generator
    """

    def __init__(self):
        """Initialize the WebSocket client with authentication from settings."""
        self.ws_url = settings.kalshi_ws_url
        self.api_key = settings.kalshi_api_key
        
        # Initialize auth
        try:
            private_key = get_kalshi_private_key()
            self.auth = KalshiAuth(self.api_key, private_key)
        except Exception as e:
            logger.error(f"Failed to initialize Kalshi WebSocket auth: {e}")
            raise KalshiAuthError(f"Failed to initialize authentication: {e}")
        
        # Connection state
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        
        # Subscription tracking
        self.subscribed_tickers: Set[str] = set()
        self.subscribed_channels: Set[str] = set()
        
        # Orderbook state (ticker -> orderbook data)
        self.orderbooks: Dict[str, Dict[str, Any]] = {}
        
        # Message queue for async processing
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Reconnection settings
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0  # Base delay in seconds
        self.reconnect_attempts = 0
        
        # Background tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("KalshiWebSocketClient initialized")

    async def connect(self) -> None:
        """
        Establish WebSocket connection with authentication headers.
        
        Raises:
            KalshiWebSocketError: On connection failure
        """
        if self.state == ConnectionState.CONNECTED:
            logger.warning("Already connected to WebSocket")
            return
        
        self.state = ConnectionState.CONNECTING
        
        try:
            # Get authentication headers
            auth_headers = self.auth.get_ws_auth_headers()
            
            # Connect with auth headers
            self.ws = await websockets.connect(
                self.ws_url,
                extra_headers=auth_headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            
            self.state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0
            self._running = True
            
            # Start background receive task
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            logger.info(f"Connected to Kalshi WebSocket at {self.ws_url}")
            
        except Exception as e:
            self.state = ConnectionState.DISCONNECTED
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise KalshiWebSocketError(f"Connection failed: {e}")

    async def disconnect(self) -> None:
        """Clean disconnect from WebSocket."""
        self._running = False
        
        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        # Close WebSocket
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self.ws = None
        
        self.state = ConnectionState.DISCONNECTED
        self.subscribed_tickers.clear()
        self.subscribed_channels.clear()
        
        logger.info("Disconnected from Kalshi WebSocket")

    async def subscribe(
        self,
        market_tickers: List[str],
        channels: List[str] = None,
    ) -> None:
        """
        Subscribe to market data channels.
        
        Args:
            market_tickers: List of market tickers to subscribe to
            channels: List of channels (e.g., ["ticker", "orderbook_delta"])
                     Default: ["ticker", "orderbook_delta"]
        
        Raises:
            KalshiWebSocketError: If not connected
        """
        if self.state != ConnectionState.CONNECTED or not self.ws:
            raise KalshiWebSocketError("Not connected to WebSocket")
        
        if channels is None:
            channels = ["ticker", "orderbook_delta"]
        
        # Build subscription command
        subscribe_cmd = {
            "id": 1,
            "cmd": "subscribe",
            "params": {
                "channels": channels,
                "market_tickers": market_tickers,
            }
        }
        
        try:
            await self.ws.send(json.dumps(subscribe_cmd))
            
            # Track subscriptions
            self.subscribed_tickers.update(market_tickers)
            self.subscribed_channels.update(channels)
            
            logger.info(f"Subscribed to {len(market_tickers)} markets: {channels}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            raise KalshiWebSocketError(f"Subscription failed: {e}")

    async def unsubscribe(self, market_tickers: List[str]) -> None:
        """
        Unsubscribe from market data.
        
        Args:
            market_tickers: List of market tickers to unsubscribe from
        """
        if self.state != ConnectionState.CONNECTED or not self.ws:
            logger.warning("Not connected, cannot unsubscribe")
            return
        
        unsubscribe_cmd = {
            "id": 2,
            "cmd": "unsubscribe",
            "params": {
                "channels": list(self.subscribed_channels),
                "market_tickers": market_tickers,
            }
        }
        
        try:
            await self.ws.send(json.dumps(unsubscribe_cmd))
            
            # Update tracking
            self.subscribed_tickers.difference_update(market_tickers)
            
            # Clean up orderbook state
            for ticker in market_tickers:
                self.orderbooks.pop(ticker, None)
            
            logger.info(f"Unsubscribed from {len(market_tickers)} markets")
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")

    async def _receive_messages(self) -> None:
        """Background task to receive and queue messages."""
        while self._running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Process message and add to queue
                processed = self._process_message(data)
                if processed:
                    await self.message_queue.put(processed)
                    
            except ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                if self._running:
                    await self._handle_reconnect()
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse WebSocket message: {e}")
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                if self._running:
                    await self._handle_reconnect()
                break

    def _process_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming WebSocket message.
        
        Args:
            data: Raw message data
        
        Returns:
            Processed message or None if should be filtered
        """
        msg_type = data.get("type", "")
        
        if msg_type == "subscribed":
            logger.debug(f"Subscription confirmed: {data}")
            return {"type": "subscribed", "data": data}
        
        elif msg_type == "ticker":
            # Price/volume update
            return {"type": "ticker", "data": data}
        
        elif msg_type == "orderbook_snapshot":
            # Full orderbook state
            ticker = data.get("market_ticker", "")
            if ticker:
                self.orderbooks[ticker] = {
                    "yes": data.get("yes", []),
                    "no": data.get("no", []),
                    "timestamp": data.get("ts", ""),
                }
            return {"type": "orderbook_snapshot", "data": data}
        
        elif msg_type == "orderbook_delta":
            # Incremental orderbook update
            ticker = data.get("market_ticker", "")
            if ticker and ticker in self.orderbooks:
                self._apply_orderbook_delta(ticker, data)
            return {"type": "orderbook_delta", "data": data}
        
        elif msg_type == "error":
            logger.error(f"WebSocket error message: {data}")
            return {"type": "error", "data": data}
        
        else:
            # Pass through unknown message types
            return {"type": msg_type or "unknown", "data": data}

    def _apply_orderbook_delta(self, ticker: str, delta: Dict[str, Any]) -> None:
        """
        Apply orderbook delta to current state.
        
        Args:
            ticker: Market ticker
            delta: Delta update data
        """
        if ticker not in self.orderbooks:
            return
        
        orderbook = self.orderbooks[ticker]
        
        # Apply yes side changes
        if "yes" in delta:
            for update in delta["yes"]:
                price = update.get("price")
                quantity = update.get("delta", 0)
                self._update_orderbook_level(orderbook["yes"], price, quantity)
        
        # Apply no side changes
        if "no" in delta:
            for update in delta["no"]:
                price = update.get("price")
                quantity = update.get("delta", 0)
                self._update_orderbook_level(orderbook["no"], price, quantity)
        
        orderbook["timestamp"] = delta.get("ts", orderbook.get("timestamp", ""))

    def _update_orderbook_level(
        self,
        levels: List[Dict],
        price: float,
        quantity_delta: int,
    ) -> None:
        """Update a single orderbook level."""
        for level in levels:
            if level.get("price") == price:
                new_qty = level.get("quantity", 0) + quantity_delta
                if new_qty <= 0:
                    levels.remove(level)
                else:
                    level["quantity"] = new_qty
                return
        
        # New price level
        if quantity_delta > 0:
            levels.append({"price": price, "quantity": quantity_delta})
            levels.sort(key=lambda x: x.get("price", 0), reverse=True)

    async def _handle_reconnect(self) -> None:
        """Handle automatic reconnection with exponential backoff."""
        if not self._running:
            return
        
        self.state = ConnectionState.RECONNECTING
        
        while self.reconnect_attempts < self.max_reconnect_attempts and self._running:
            self.reconnect_attempts += 1
            delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
            
            logger.info(
                f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
                f"in {delay:.1f}s"
            )
            
            await asyncio.sleep(delay)
            
            if not self._running:
                break
            
            try:
                # Close existing connection
                if self.ws:
                    try:
                        await self.ws.close()
                    except Exception:
                        pass
                    self.ws = None
                
                # Reconnect
                auth_headers = self.auth.get_ws_auth_headers()
                self.ws = await websockets.connect(
                    self.ws_url,
                    extra_headers=auth_headers,
                    ping_interval=30,
                    ping_timeout=10,
                )
                
                self.state = ConnectionState.CONNECTED
                self.reconnect_attempts = 0
                
                # Resubscribe to previous subscriptions
                if self.subscribed_tickers:
                    await self.subscribe(
                        list(self.subscribed_tickers),
                        list(self.subscribed_channels),
                    )
                
                # Restart receive task
                self._receive_task = asyncio.create_task(self._receive_messages())
                
                logger.info("Successfully reconnected to WebSocket")
                return
                
            except Exception as e:
                logger.warning(f"Reconnection attempt failed: {e}")
        
        self.state = ConnectionState.DISCONNECTED
        logger.error("Failed to reconnect after all attempts")

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator that yields incoming messages.
        
        Yields:
            Processed messages from the WebSocket
        
        Example:
            async for message in ws_client.listen():
                if message["type"] == "ticker":
                    process_ticker(message["data"])
        """
        while self._running or not self.message_queue.empty():
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                yield message
            except asyncio.TimeoutError:
                # Check if still running
                if not self._running and self.message_queue.empty():
                    break
                continue
            except Exception as e:
                logger.error(f"Error in listen generator: {e}")
                break

    def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current orderbook state for a ticker.
        
        Args:
            ticker: Market ticker
        
        Returns:
            Current orderbook state or None if not tracked
        """
        return self.orderbooks.get(ticker)

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self.state == ConnectionState.CONNECTED and self.ws is not None

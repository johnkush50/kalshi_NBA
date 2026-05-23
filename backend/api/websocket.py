"""
WebSocket endpoint for real-time frontend updates.

Provides real-time streaming of:
- Trading signals
- Order executions
- P&L updates
- Market data updates
"""

import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Connected clients
connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")


# Global connection manager
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Query params:
        channels: Comma-separated list of channels to subscribe to
                  (all, signals, orders, pnl, markets)

    Message format:
        {
            "type": "signal" | "order_filled" | "order_rejected" | "pnl_update" | "market_update",
            "data": { ... }
        }
    """
    await manager.connect(websocket)

    # Get requested channels from query params
    channels_param = websocket.query_params.get("channels", "all")
    channels = set(channels_param.split(","))

    logger.info(f"Client subscribed to channels: {channels}")

    # Send initial connection confirmation
    await manager.send_personal(websocket, {
        "type": "connected",
        "data": {
            "message": "Connected to Kalshi NBA Paper Trading WebSocket",
            "channels": list(channels)
        }
    })

    try:
        while True:
            # Keep connection alive and handle incoming messages
            try:
                # Wait for messages from client (like ping/pong or commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for ping
                )

                # Handle client messages
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_personal(websocket, {"type": "pong"})
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await manager.send_personal(websocket, {"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Helper functions for broadcasting from other parts of the application

async def broadcast_signal(signal_data: dict):
    """Broadcast a new trading signal."""
    await manager.broadcast({
        "type": "signal",
        "data": signal_data
    })


async def broadcast_order(order_data: dict, status: str = "filled"):
    """Broadcast an order execution."""
    await manager.broadcast({
        "type": f"order_{status}",
        "data": order_data
    })


async def broadcast_pnl_update(pnl_data: dict):
    """Broadcast a P&L update."""
    await manager.broadcast({
        "type": "pnl_update",
        "data": pnl_data
    })


async def broadcast_market_update(market_data: dict):
    """Broadcast a market data update."""
    await manager.broadcast({
        "type": "market_update",
        "data": market_data
    })

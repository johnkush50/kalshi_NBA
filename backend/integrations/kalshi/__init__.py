"""
Kalshi API integration module.

Provides REST and WebSocket clients for interacting with Kalshi's trading API.
Uses RSA-PSS authentication (NOT HMAC).
"""

from backend.integrations.kalshi.auth import KalshiAuth
from backend.integrations.kalshi.client import KalshiClient
from backend.integrations.kalshi.websocket import KalshiWebSocketClient
from backend.integrations.kalshi.exceptions import (
    KalshiError,
    KalshiAPIError,
    KalshiAuthError,
    KalshiNotFoundError,
    KalshiRateLimitError,
    KalshiWebSocketError,
)

__all__ = [
    "KalshiAuth",
    "KalshiClient",
    "KalshiWebSocketClient",
    "KalshiError",
    "KalshiAPIError",
    "KalshiAuthError",
    "KalshiNotFoundError",
    "KalshiRateLimitError",
    "KalshiWebSocketError",
]
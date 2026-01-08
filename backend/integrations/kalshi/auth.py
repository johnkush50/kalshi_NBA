"""
Kalshi API Authentication Module.

Handles RSA-PSS signature generation for REST API and WebSocket authentication.
Kalshi requires RSA-PSS with SHA256, not HMAC.
"""

import base64
import time
import logging
from typing import Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class KalshiAuth:
    """
    Handles Kalshi API authentication using RSA-PSS signatures.
    
    Kalshi requires:
    - KALSHI-ACCESS-KEY: Your API key ID
    - KALSHI-ACCESS-SIGNATURE: RSA-PSS signature (base64 encoded)
    - KALSHI-ACCESS-TIMESTAMP: Current timestamp in milliseconds
    """
    
    def __init__(self, api_key: str, private_key_pem: str):
        """
        Initialize authentication handler.
        
        Args:
            api_key: Kalshi API key ID
            private_key_pem: RSA private key in PEM format (with actual newlines)
        """
        self.api_key = api_key
        self._load_private_key(private_key_pem)
    
    def _load_private_key(self, private_key_pem: str) -> None:
        """Load and parse the RSA private key."""
        try:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            logger.info("RSA private key loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise ValueError(f"Invalid private key: {e}")
    
    def generate_signature(self, timestamp_ms: int, method: str, path: str, body: str = "") -> str:
        """
        Generate RSA-PSS signature for Kalshi API request.
        
        Args:
            timestamp_ms: Current timestamp in milliseconds
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path (e.g., "/trade-api/v2/markets")
            body: Request body for POST/PUT requests (empty string for GET)
        
        Returns:
            Base64-encoded RSA-PSS signature
        """
        # Build message to sign: {timestamp}{method}{path}{body}
        message = f"{timestamp_ms}{method}{path}{body}"
        message_bytes = message.encode('utf-8')
        
        # Sign with RSA-PSS
        signature = self.private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')
    
    def get_auth_headers(self, method: str, path: str, body: str = "") -> dict:
        """
        Generate authentication headers for Kalshi API request.
        
        Args:
            method: HTTP method
            path: API path
            body: Request body (empty for GET)
        
        Returns:
            Dictionary of authentication headers
        """
        timestamp_ms = int(time.time() * 1000)
        signature = self.generate_signature(timestamp_ms, method, path, body)
        
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms)
        }
    
    def get_ws_auth_headers(self) -> dict:
        """
        Generate authentication headers for WebSocket connection.
        
        WebSocket auth uses the same headers but for a specific path.
        
        Returns:
            Dictionary of authentication headers for WebSocket
        """
        return self.get_auth_headers("GET", "/trade-api/ws/v2")

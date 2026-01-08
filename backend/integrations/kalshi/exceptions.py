"""
Custom exceptions for Kalshi API integration.
"""


class KalshiError(Exception):
    """Base exception for Kalshi API errors."""
    pass


class KalshiAuthError(KalshiError):
    """Authentication failed (invalid credentials, signature error)."""
    pass


class KalshiAPIError(KalshiError):
    """API request failed."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class KalshiNotFoundError(KalshiAPIError):
    """Resource not found (404)."""
    pass


class KalshiRateLimitError(KalshiAPIError):
    """Rate limit exceeded (429)."""
    pass


class KalshiWebSocketError(KalshiError):
    """WebSocket connection or communication error."""
    pass

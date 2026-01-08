"""
Custom exceptions for balldontlie.io API integration.
"""


class BallDontLieError(Exception):
    """Base exception for balldontlie.io API errors."""
    pass


class BallDontLieAuthError(BallDontLieError):
    """Authentication failed (invalid API key)."""
    pass


class BallDontLieAPIError(BallDontLieError):
    """API request failed."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BallDontLieNotFoundError(BallDontLieAPIError):
    """Resource not found (404)."""
    pass


class BallDontLieRateLimitError(BallDontLieAPIError):
    """Rate limit exceeded (429)."""
    pass


class GameMatchError(BallDontLieError):
    """Could not match Kalshi game to NBA game."""
    pass

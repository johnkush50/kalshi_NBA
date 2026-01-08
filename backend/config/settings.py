"""
Configuration settings for Kalshi NBA Paper Trading Application.

Uses Pydantic BaseSettings to load environment variables from .env file.
All sensitive values (API keys, database credentials) are loaded from environment.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Environment variables should be defined in .env file (see .env.example).
    """

    # ========================================================================
    # Kalshi API Configuration
    # ========================================================================
    kalshi_api_url: str = "https://api.elections.kalshi.com/trade-api/v2"
    kalshi_ws_url: str = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    kalshi_api_key: str
    kalshi_api_secret: str
    kalshi_api_secret_file: Optional[str] = None  # Path to .pem file for private key

    # ========================================================================
    # balldontlie.io API Configuration
    # ========================================================================
    balldontlie_api_url: str = "https://api.balldontlie.io"
    balldontlie_api_key: str

    # ========================================================================
    # Supabase Database Configuration
    # ========================================================================
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    redis_url: str = "redis://localhost:6379"

    # ========================================================================
    # Application Configuration
    # ========================================================================
    environment: str = "development"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # ========================================================================
    # Data Polling Configuration (in seconds)
    # ========================================================================
    nba_poll_interval: int = 5
    betting_odds_poll_interval: int = 10
    strategy_eval_interval: int = 2
    pnl_calc_interval: int = 5

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# ============================================================================
# Global Settings Instance
# ============================================================================

# Singleton settings instance - import this in other modules
settings = Settings()


# ============================================================================
# Helper Functions
# ============================================================================

def get_settings() -> Settings:
    """
    Get the application settings.

    Returns:
        Settings: The application settings instance.
    """
    return settings


def is_production() -> bool:
    """
    Check if the application is running in production mode.

    Returns:
        bool: True if in production, False otherwise.
    """
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """
    Check if the application is running in development mode.

    Returns:
        bool: True if in development, False otherwise.
    """
    return settings.environment.lower() == "development"


def get_kalshi_private_key() -> str:
    """
    Get the Kalshi private key for RSA-PSS authentication.
    
    Loads from file if kalshi_api_secret_file is set and exists,
    otherwise uses kalshi_api_secret from environment.
    
    CRITICAL: Replaces literal "\\n" with actual newlines for PEM format.
    
    Returns:
        str: Private key in PEM format ready for cryptography library.
    
    Raises:
        ValueError: If no private key is available.
    """
    private_key_pem = None
    
    # Try loading from file first
    if settings.kalshi_api_secret_file:
        file_path = Path(settings.kalshi_api_secret_file)
        if file_path.exists():
            private_key_pem = file_path.read_text(encoding='utf-8')
    
    # Fall back to environment variable
    if not private_key_pem:
        private_key_pem = settings.kalshi_api_secret
    
    if not private_key_pem:
        raise ValueError("No Kalshi private key available. Set KALSHI_API_SECRET or KALSHI_API_SECRET_FILE.")
    
    # CRITICAL: Replace literal "\n" strings with actual newlines
    # Environment variables often have escaped newlines
    private_key_pem = private_key_pem.replace('\\n', '\n')
    
    return private_key_pem

"""
Unit tests for application settings.

Tests configuration loading and validation.
"""

import pytest
import os
from backend.config.settings import settings, get_settings, is_production, is_development


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_instance_exists(self):
        """Test that settings instance is created."""
        assert settings is not None

    def test_get_settings_returns_instance(self):
        """Test get_settings function."""
        result = get_settings()
        assert result is not None
        assert result == settings

    def test_default_values(self):
        """Test default configuration values."""
        assert settings.kalshi_api_url == "https://api.elections.kalshi.com/trade-api/v2"
        assert settings.kalshi_ws_url == "wss://api.elections.kalshi.com/trade-api/ws/v2"
        assert settings.balldontlie_api_url == "https://api.balldontlie.io"
        assert settings.redis_url == "redis://localhost:6379"
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.frontend_url == "http://localhost:3000"
        assert settings.backend_url == "http://localhost:8000"

    def test_poll_intervals(self):
        """Test data polling interval defaults."""
        assert settings.nba_poll_interval == 5
        assert settings.betting_odds_poll_interval == 10
        assert settings.strategy_eval_interval == 2
        assert settings.pnl_calc_interval == 5


class TestEnvironmentHelpers:
    """Tests for environment helper functions."""

    def test_is_development_default(self):
        """Test is_development function."""
        # Default environment is development
        assert is_development() is True

    def test_is_production_default(self):
        """Test is_production function."""
        # Default environment is development, not production
        assert is_production() is False

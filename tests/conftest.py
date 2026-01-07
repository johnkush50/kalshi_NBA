"""
Pytest configuration and fixtures.

Provides shared test fixtures and configuration for all tests.
"""

import pytest
import os
import sys

# Add backend directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_settings():
    """Fixture providing mock settings for testing."""
    return {
        "kalshi_api_key": "test_api_key",
        "kalshi_api_secret": "test_api_secret",
        "balldontlie_api_key": "test_nba_key",
        "supabase_url": "https://test.supabase.co",
        "supabase_service_key": "test_service_key"
    }


@pytest.fixture
def sample_ticker():
    """Fixture providing a sample Kalshi ticker for testing."""
    return "kxnbagame-26jan06dalsac"


@pytest.fixture
def sample_game_info():
    """Fixture providing sample parsed game information."""
    return {
        "date": "2026-01-06",
        "away_team_abbr": "DAL",
        "home_team_abbr": "SAC"
    }

"""
Unit tests for Kalshi ticker parser.

Tests extraction of date and team information from Kalshi market tickers.
"""

import pytest
from datetime import datetime

from backend.utils.ticker_parser import (
    extract_game_info_from_kalshi_ticker,
    validate_team_abbreviation,
    format_ticker_for_display,
    normalize_team_abbreviation
)


class TestExtractGameInfo:
    """Tests for extract_game_info_from_kalshi_ticker function."""

    def test_valid_ticker_parsing(self):
        """Test parsing a valid Kalshi ticker."""
        result = extract_game_info_from_kalshi_ticker("kxnbagame-26jan06dalsac")

        assert result["date"] == "2026-01-06"
        assert result["away_team_abbr"] == "DAL"
        assert result["home_team_abbr"] == "SAC"

    def test_valid_ticker_different_teams(self):
        """Test parsing with different teams."""
        # Format: YYmmmDD - 25dec15 means year=2025, month=Dec, day=15
        result = extract_game_info_from_kalshi_ticker("kxnbagame-25dec15lalgsc")

        assert result["date"] == "2025-12-15"
        assert result["away_team_abbr"] == "LAL"
        assert result["home_team_abbr"] == "GSC"

    def test_valid_ticker_february(self):
        """Test parsing with February date."""
        # Format: YYmmmDD - 26feb14 means year=2026, month=Feb, day=14
        result = extract_game_info_from_kalshi_ticker("kxnbagame-26feb14boscle")

        assert result["date"] == "2026-02-14"
        assert result["away_team_abbr"] == "BOS"
        assert result["home_team_abbr"] == "CLE"

    def test_valid_ticker_different_format(self):
        """Test parsing ticker without kx prefix."""
        # Format: YYmmmDD - 26mar20 means year=2026, month=Mar, day=20
        result = extract_game_info_from_kalshi_ticker("nbagame-26mar20miaatl")

        assert result["date"] == "2026-03-20"
        assert result["away_team_abbr"] == "MIA"
        assert result["home_team_abbr"] == "ATL"

    def test_invalid_ticker_no_date(self):
        """Test that invalid ticker raises ValueError."""
        with pytest.raises(ValueError, match="Could not find date pattern"):
            extract_game_info_from_kalshi_ticker("kxnbagame-invalid")

    def test_invalid_ticker_too_short(self):
        """Test that ticker with insufficient team characters raises ValueError."""
        with pytest.raises(ValueError, match="Invalid team codes"):
            extract_game_info_from_kalshi_ticker("kxnbagame-26jan06dal")

    def test_invalid_ticker_bad_month(self):
        """Test that ticker with invalid month raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date"):
            extract_game_info_from_kalshi_ticker("kxnbagame-26xyz06dalsac")


class TestValidateTeamAbbreviation:
    """Tests for validate_team_abbreviation function."""

    def test_valid_abbreviation(self):
        """Test valid 3-letter uppercase abbreviation."""
        assert validate_team_abbreviation("LAL") is True
        assert validate_team_abbreviation("GSW") is True
        assert validate_team_abbreviation("BOS") is True

    def test_invalid_length(self):
        """Test abbreviations with wrong length."""
        assert validate_team_abbreviation("LA") is False
        assert validate_team_abbreviation("LAKERS") is False

    def test_invalid_case(self):
        """Test lowercase abbreviations."""
        assert validate_team_abbreviation("lal") is False
        assert validate_team_abbreviation("Lal") is False

    def test_invalid_characters(self):
        """Test abbreviations with non-alphabetic characters."""
        assert validate_team_abbreviation("LA1") is False
        assert validate_team_abbreviation("L A") is False


class TestFormatTickerForDisplay:
    """Tests for format_ticker_for_display function."""

    def test_format_valid_ticker(self):
        """Test formatting a valid ticker."""
        result = format_ticker_for_display("kxnbagame-26jan06dalsac")
        assert result == "DAL @ SAC - Jan 06, 2026"

    def test_format_different_month(self):
        """Test formatting with different month."""
        # Format: YYmmmDD - 25dec15 means year=2025, month=Dec, day=15
        result = format_ticker_for_display("kxnbagame-25dec15lalgsc")
        assert result == "LAL @ GSC - Dec 15, 2025"

    def test_format_invalid_ticker(self):
        """Test formatting invalid ticker returns original."""
        invalid_ticker = "invalid_ticker"
        result = format_ticker_for_display(invalid_ticker)
        assert result == invalid_ticker


class TestNormalizeTeamAbbreviation:
    """Tests for normalize_team_abbreviation function."""

    def test_normalize_gsc_to_gsw(self):
        """Test normalizing GSC to GSW."""
        assert normalize_team_abbreviation("GSC") == "GSW"

    def test_normalize_lowercase(self):
        """Test normalizing lowercase to uppercase."""
        assert normalize_team_abbreviation("lal") == "LAL"

    def test_no_normalization_needed(self):
        """Test abbreviations that don't need normalization."""
        assert normalize_team_abbreviation("LAL") == "LAL"
        assert normalize_team_abbreviation("BOS") == "BOS"

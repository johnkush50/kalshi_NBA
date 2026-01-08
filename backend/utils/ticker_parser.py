"""
Kalshi ticker parsing utilities.

Extracts game information (date, teams) from Kalshi market tickers.
Example: "kxnbagame-26jan06dalsac" → {date: "2026-01-06", away: "DAL", home: "SAC"}
"""

import re
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Ticker Parsing Functions
# ============================================================================

def extract_game_info_from_kalshi_ticker(ticker: str) -> Dict[str, str]:
    """
    Parse Kalshi market ticker to extract date and team information.

    The ticker format is typically: "kxnbagame-YYmmmDDTEAM1TEAM2"
    Example: "kxnbagame-26jan06dalsac" → Date: 2026-01-06, Away: DAL, Home: SAC

    Args:
        ticker: Kalshi market ticker string.

    Returns:
        Dictionary containing:
            - date: Game date in YYYY-MM-DD format
            - away_team_abbr: Away team abbreviation (3 letters)
            - home_team_abbr: Home team abbreviation (3 letters)

    Raises:
        ValueError: If ticker format is invalid or cannot be parsed.

    Examples:
        >>> extract_game_info_from_kalshi_ticker("kxnbagame-26jan06dalsac")
        {'date': '2026-01-06', 'away_team_abbr': 'DAL', 'home_team_abbr': 'SAC'}

        >>> extract_game_info_from_kalshi_ticker("kxnbagame-15dec25lalgsc")
        {'date': '2025-12-15', 'away_team_abbr': 'LAL', 'home_team_abbr': 'GSC'}
    """
    try:
        # Convert to lowercase for consistent parsing
        ticker_lower = ticker.lower()

        # Remove common prefixes
        ticker_clean = ticker_lower.replace("kxnbagame-", "").replace("kx", "")

        # Extract date portion using regex pattern: YYmmmDD
        # Example: "26jan06" from "26jan06dalsac" means 2026-Jan-06
        date_pattern = r'(\d{2})([a-z]{3})(\d{2})'
        match = re.search(date_pattern, ticker_clean, re.IGNORECASE)

        if not match:
            raise ValueError(f"Could not find date pattern in ticker: {ticker}")

        year = "20" + match.group(1)  # First 2 digits are year (20XX century)
        month = match.group(2).capitalize()
        day = match.group(3)  # Last 2 digits are day

        # Convert month abbreviation to date
        try:
            date_str = f"{day}-{month}-{year}"
            game_date = datetime.strptime(date_str, "%d-%b-%Y")
        except ValueError as e:
            raise ValueError(f"Invalid date in ticker {ticker}: {e}")

        # Extract team codes (remaining characters after date)
        teams_portion = ticker_clean[match.end():]

        # Teams are typically 3 characters each (6 total)
        # First 3 = away team, Last 3 = home team
        if len(teams_portion) < 6:
            raise ValueError(
                f"Invalid team codes in ticker {ticker}. "
                f"Expected 6 characters, got {len(teams_portion)}"
            )

        away_team = teams_portion[:3].upper()
        home_team = teams_portion[3:6].upper()

        result = {
            "date": game_date.strftime("%Y-%m-%d"),
            "away_team_abbr": away_team,
            "home_team_abbr": home_team
        }

        logger.debug(f"Parsed ticker {ticker}: {result}")

        return result

    except Exception as e:
        logger.error(f"Failed to parse ticker {ticker}: {e}", exc_info=True)
        raise ValueError(f"Could not parse Kalshi ticker '{ticker}': {e}")


def validate_team_abbreviation(abbr: str) -> bool:
    """
    Validate that a team abbreviation is in correct format.

    Args:
        abbr: Team abbreviation (should be 3 uppercase letters).

    Returns:
        True if valid, False otherwise.

    Examples:
        >>> validate_team_abbreviation("LAL")
        True
        >>> validate_team_abbreviation("GSW")
        True
        >>> validate_team_abbreviation("XX")
        False
    """
    return len(abbr) == 3 and abbr.isalpha() and abbr.isupper()


def format_ticker_for_display(ticker: str) -> str:
    """
    Format a Kalshi ticker for human-readable display.

    Args:
        ticker: Kalshi market ticker.

    Returns:
        Formatted string (e.g., "DAL @ SAC - Jan 06, 2026").

    Examples:
        >>> format_ticker_for_display("kxnbagame-26jan06dalsac")
        'DAL @ SAC - Jan 06, 2026'
    """
    try:
        info = extract_game_info_from_kalshi_ticker(ticker)
        game_date = datetime.strptime(info["date"], "%Y-%m-%d")
        date_str = game_date.strftime("%b %d, %Y")

        return f"{info['away_team_abbr']} @ {info['home_team_abbr']} - {date_str}"
    except Exception as e:
        logger.warning(f"Could not format ticker {ticker}: {e}")
        return ticker


# ============================================================================
# Team Mapping (Optional Enhancement)
# ============================================================================

# Common NBA team abbreviation variations
TEAM_ABBREVIATION_MAPPING = {
    "GSC": "GSW",  # Golden State Warriors
    "PHO": "PHX",  # Phoenix Suns
    "SAS": "SAC",  # Sometimes confused
    # Add more mappings as needed
}


def normalize_team_abbreviation(abbr: str) -> str:
    """
    Normalize team abbreviation to standard format.

    Args:
        abbr: Team abbreviation.

    Returns:
        Normalized abbreviation.

    Examples:
        >>> normalize_team_abbreviation("GSC")
        'GSW'
        >>> normalize_team_abbreviation("LAL")
        'LAL'
    """
    return TEAM_ABBREVIATION_MAPPING.get(abbr.upper(), abbr.upper())

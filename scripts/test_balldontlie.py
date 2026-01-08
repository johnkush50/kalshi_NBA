"""
Test script for balldontlie.io API integration.

Usage:
    python scripts/test_balldontlie.py --test-auth
    python scripts/test_balldontlie.py --list-games --date 2026-01-08
    python scripts/test_balldontlie.py --match-kalshi --ticker KXNBAGAME-26JAN08DALUTA
    python scripts/test_balldontlie.py --get-odds --date 2026-01-08
"""

import asyncio
import argparse
import sys
sys.path.insert(0, '.')

from backend.integrations.balldontlie.client import BallDontLieClient


async def test_auth():
    """Test authentication by fetching teams."""
    print("Testing balldontlie.io authentication...")
    client = BallDontLieClient()
    try:
        teams = await client.get_teams()
        print(f"✓ Authentication successful!")
        print(f"  Found {len(teams)} NBA teams")
        
        # Show first few teams
        if teams:
            print("\n  Sample teams:")
            for team in teams[:5]:
                print(f"    - {team.get('full_name', 'Unknown')} ({team.get('abbreviation', '???')})")
        
        await client.close()
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        await client.close()
        return False


async def list_games(date: str):
    """List all NBA games for a date."""
    print(f"Fetching NBA games for {date}...")
    client = BallDontLieClient()
    try:
        games = await client.get_games_for_date(date)
        if not games:
            print("No games found for this date.")
            await client.close()
            return
        
        print(f"\n✓ Found {len(games)} games:\n")
        for game in games:
            visitor = game.get("visitor_team", {})
            home = game.get("home_team", {})
            status = game.get("status", "unknown")
            
            print(f"  ID: {game['id']}")
            print(f"  {visitor.get('abbreviation', '???')} @ {home.get('abbreviation', '???')}")
            print(f"  {visitor.get('full_name', 'Unknown')} at {home.get('full_name', 'Unknown')}")
            print(f"  Status: {status}")
            if game.get("home_team_score") is not None:
                print(f"  Score: {game.get('visitor_team_score', 0)} - {game.get('home_team_score', 0)}")
            print()
        
        await client.close()
        return games
    except Exception as e:
        print(f"✗ Failed to fetch games: {e}")
        await client.close()
        return None


async def match_kalshi_game(ticker: str):
    """Match a Kalshi ticker to an NBA game."""
    print(f"Matching Kalshi ticker: {ticker}")
    client = BallDontLieClient()
    try:
        game = await client.match_kalshi_game(ticker)
        
        print(f"\n✓ Match found!")
        print(f"  NBA Game ID: {game['id']}")
        print(f"  {game['visitor_team']['full_name']} @ {game['home_team']['full_name']}")
        print(f"  Date: {game.get('date', 'Unknown')}")
        print(f"  Status: {game.get('status', 'Unknown')}")
        
        await client.close()
        return game
    except Exception as e:
        print(f"✗ Match failed: {e}")
        await client.close()
        return None


async def get_odds(date: str):
    """Get betting odds for games on a date."""
    print(f"Fetching betting odds for {date}...")
    client = BallDontLieClient()
    try:
        odds_data = await client.get_odds(date=date)
        
        if not odds_data:
            print("No odds data found for this date.")
            await client.close()
            return
        
        # Group odds by game_id since API returns one row per sportsbook
        games_odds = {}
        for odds in odds_data:
            game_id = odds.get("game_id")
            if game_id not in games_odds:
                games_odds[game_id] = []
            games_odds[game_id].append(odds)
        
        print(f"\n✓ Found odds for {len(games_odds)} games ({len(odds_data)} sportsbook entries):\n")
        
        for game_id, odds_list in games_odds.items():
            print(f"  Game ID: {game_id}")
            
            for odds in odds_list:
                vendor = odds.get("vendor", "Unknown")
                ml_home = odds.get("moneyline_home_odds", "N/A")
                ml_away = odds.get("moneyline_away_odds", "N/A")
                spread_home = odds.get("spread_home_value", "N/A")
                spread_odds = odds.get("spread_home_odds", "N/A")
                total = odds.get("total_value", "N/A")
                over = odds.get("total_over_odds", "N/A")
                under = odds.get("total_under_odds", "N/A")
                
                print(f"    {vendor}:")
                print(f"      ML: Home {ml_home} / Away {ml_away}")
                print(f"      Spread: {spread_home} ({spread_odds})")
                print(f"      Total: {total} (O: {over} / U: {under})")
            print()
        
        await client.close()
        return odds_data
    except Exception as e:
        print(f"✗ Failed to fetch odds: {e}")
        await client.close()
        return None


async def list_teams():
    """List all NBA teams."""
    print("Fetching all NBA teams...")
    client = BallDontLieClient()
    try:
        teams = await client.get_teams()
        
        print(f"\n✓ Found {len(teams)} teams:\n")
        for team in teams:
            print(f"  {team.get('abbreviation', '???'):3} - {team.get('full_name', 'Unknown')}")
        
        await client.close()
        return teams
    except Exception as e:
        print(f"✗ Failed to fetch teams: {e}")
        await client.close()
        return None


def main():
    parser = argparse.ArgumentParser(description="Test balldontlie.io API integration")
    parser.add_argument("--test-auth", action="store_true", help="Test authentication")
    parser.add_argument("--list-games", action="store_true", help="List NBA games for a date")
    parser.add_argument("--list-teams", action="store_true", help="List all NBA teams")
    parser.add_argument("--match-kalshi", action="store_true", help="Match Kalshi ticker to NBA game")
    parser.add_argument("--get-odds", action="store_true", help="Get betting odds for a date")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    parser.add_argument("--ticker", type=str, help="Kalshi event ticker")
    
    args = parser.parse_args()
    
    if args.test_auth:
        asyncio.run(test_auth())
    elif args.list_teams:
        asyncio.run(list_teams())
    elif args.list_games:
        if not args.date:
            print("Error: --date required for --list-games")
            sys.exit(1)
        asyncio.run(list_games(args.date))
    elif args.match_kalshi:
        if not args.ticker:
            print("Error: --ticker required for --match-kalshi")
            sys.exit(1)
        asyncio.run(match_kalshi_game(args.ticker))
    elif args.get_odds:
        if not args.date:
            print("Error: --date required for --get-odds")
            sys.exit(1)
        asyncio.run(get_odds(args.date))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

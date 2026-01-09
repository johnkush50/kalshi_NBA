#!/usr/bin/env python
"""
Test script for the Data Aggregator.

Usage:
    python scripts/test_aggregator.py --load-game --date 2026-01-08 --index 0
    python scripts/test_aggregator.py --show-state --game-id <UUID>
    python scripts/test_aggregator.py --list-states
    python scripts/test_aggregator.py --monitor --game-id <UUID>

NOTE: This script uses the API endpoints to interact with the running FastAPI server.
      Make sure the server is running: uvicorn backend.main:app --reload
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings


BASE_URL = "http://localhost:8000"


async def load_game_flow(date: str, index: int) -> None:
    """
    Full flow to load a game via API:
    1. List available games from API
    2. Load selected game via API
    3. Verify game is loaded in server's aggregator
    """
    print(f"\n{'='*60}")
    print(f"Loading game for date: {date}, index: {index}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: List available NBA games via API
        print("Step 1: Fetching available NBA games via API...")
        try:
            response = await client.get(f"{BASE_URL}/api/games/available", params={"date": date})
            response.raise_for_status()
            data = response.json()
            games = data.get("games", [])
        except httpx.ConnectError:
            print(f"\n❌ Error: Cannot connect to server at {BASE_URL}")
            print("   Make sure the server is running: uvicorn backend.main:app --reload")
            return
        except Exception as e:
            print(f"Error fetching games: {e}")
            return
        
        if not games:
            print(f"No NBA games found on Kalshi for {date}")
            return
        
        print(f"Found {len(games)} games:")
        for i, game in enumerate(games):
            print(f"  [{i}] {game.get('away_team', 'TBD')} @ {game.get('home_team', 'TBD')}")
            print(f"      Event: {game.get('event_ticker', 'N/A')}")
        
        if index >= len(games):
            print(f"\nError: Index {index} out of range (0-{len(games)-1})")
            return
        
        selected = games[index]
        event_ticker = selected.get('event_ticker')
        print(f"\nSelected: {selected.get('away_team')} @ {selected.get('home_team')}")
        
        # Step 2: Load game via API (this creates DB record and loads into server's aggregator)
        print("\nStep 2: Loading game via API...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/games/load",
                json={"event_ticker": event_ticker}
            )
            response.raise_for_status()
            game_data = response.json()
            game_id = game_data.get("game_id")  # API returns "game_id" not "id"
            print(f"Game loaded: {game_id}")
        except httpx.HTTPStatusError as e:
            print(f"Error loading game: {e.response.text}")
            return
        
        # Step 3: Load into server's aggregator via API
        print("\nStep 3: Loading into server's aggregator...")
        try:
            response = await client.post(f"{BASE_URL}/api/aggregator/load/{game_id}")
            response.raise_for_status()
            state_data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error loading into aggregator: {e.response.text}")
            return
        
        # Step 4: Verify by fetching state
        print("\nStep 4: Verifying game state...")
        try:
            response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
            response.raise_for_status()
            state = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching state: {e.response.text}")
            return
        
        print(f"\n{'='*60}")
        print("GAME LOADED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"Game ID: {state.get('game_id')}")
        print(f"Event Ticker: {state.get('event_ticker')}")
        print(f"Teams: {state.get('away_team')} @ {state.get('home_team')}")
        print(f"Phase: {state.get('phase')}")
        print(f"Markets: {len(state.get('markets', {}))}")
        print(f"Has NBA Data: {state.get('has_nba_data')}")
        print(f"Has Odds Data: {state.get('has_odds_data')}")
        
        nba_state = state.get('nba_state')
        if nba_state:
            print(f"\nNBA State:")
            print(f"  NBA Game ID: {nba_state.get('nba_game_id')}")
            print(f"  Status: {nba_state.get('status')}")
            print(f"  Score: {nba_state.get('away_score')} - {nba_state.get('home_score')}")
        
        consensus = state.get('consensus')
        if consensus:
            print(f"\nConsensus Odds:")
            print(f"  Sportsbooks: {consensus.get('num_sportsbooks')}")
            home_prob = consensus.get('home_win_probability')
            away_prob = consensus.get('away_win_probability')
            if home_prob:
                print(f"  Home Win: {float(home_prob)*100:.1f}%")
            if away_prob:
                print(f"  Away Win: {float(away_prob)*100:.1f}%")


async def show_state(game_id: str) -> None:
    """Display current GameState for a loaded game via API."""
    print(f"\n{'='*60}")
    print(f"Game State: {game_id}")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
            response.raise_for_status()
            state = response.json()
        except httpx.ConnectError:
            print(f"\n❌ Error: Cannot connect to server at {BASE_URL}")
            print("   Make sure the server is running: uvicorn backend.main:app --reload")
            return
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Game not loaded: {game_id}")
                # Try to list loaded games
                try:
                    resp = await client.get(f"{BASE_URL}/api/aggregator/states")
                    if resp.status_code == 200:
                        states = resp.json().get("states", [])
                        if states:
                            print("\nLoaded games:")
                            for s in states:
                                print(f"  {s.get('game_id')}: {s.get('away_team')} @ {s.get('home_team')}")
                        else:
                            print("\nNo games currently loaded in aggregator.")
                except:
                    pass
            else:
                print(f"Error: {e.response.text}")
            return
    
    print(f"Event Ticker: {state.get('event_ticker')}")
    print(f"Teams: {state.get('away_team')} @ {state.get('home_team')}")
    print(f"Date: {state.get('game_date')}")
    print(f"Phase: {state.get('phase')}")
    print(f"Active: {state.get('is_active')}")
    print(f"Last Updated: {state.get('last_updated')}")
    
    markets = state.get('markets', {})
    print(f"\n--- Markets ({len(markets)}) ---")
    for ticker, market in markets.items():
        print(f"\n{ticker}:")
        print(f"  Type: {market.get('market_type')}")
        if market.get('strike_value'):
            print(f"  Strike: {market.get('strike_value')}")
        ob = market.get('orderbook')
        if ob:
            print(f"  Yes Bid/Ask: {ob.get('yes_bid')}/{ob.get('yes_ask')}")
            if ob.get('mid_price'):
                print(f"  Mid Price: {ob.get('mid_price')}")
            if ob.get('spread'):
                print(f"  Spread: {ob.get('spread')}")
    
    nba = state.get('nba_state')
    if nba:
        print(f"\n--- NBA State ---")
        print(f"NBA Game ID: {nba.get('nba_game_id')}")
        print(f"Status: {nba.get('status')}")
        print(f"Period: {nba.get('period')}")
        print(f"Time: {nba.get('time_remaining')}")
        print(f"Score: {nba.get('away_score')} - {nba.get('home_score')} (Away - Home)")
        print(f"Total: {nba.get('total_score')}")
        diff = nba.get('score_differential', 0)
        print(f"Differential: {diff:+d}")
    
    odds = state.get('odds', {})
    if odds:
        print(f"\n--- Betting Odds ({len(odds)} sportsbooks) ---")
        for vendor, odd in odds.items():
            print(f"\n{vendor}:")
            if odd.get('moneyline_home'):
                print(f"  ML: Home {odd.get('moneyline_home'):+d} / Away {odd.get('moneyline_away'):+d}")
            if odd.get('spread_home_value'):
                print(f"  Spread: {odd.get('spread_home_value')} ({odd.get('spread_home_odds'):+d})")
            if odd.get('total_value'):
                print(f"  Total: {odd.get('total_value')} (O {odd.get('total_over_odds'):+d} / U {odd.get('total_under_odds'):+d})")
    
    consensus = state.get('consensus')
    if consensus:
        print(f"\n--- Consensus ---")
        print(f"Sportsbooks: {consensus.get('num_sportsbooks')}")
        home_prob = consensus.get('home_win_probability')
        away_prob = consensus.get('away_win_probability')
        if home_prob:
            print(f"Home Win Prob: {float(home_prob)*100:.1f}%")
        if away_prob:
            print(f"Away Win Prob: {float(away_prob)*100:.1f}%")
        if consensus.get('spread_line'):
            print(f"Spread Line: {consensus.get('spread_line')}")
        if consensus.get('total_line'):
            print(f"Total Line: {consensus.get('total_line')}")


async def list_states() -> None:
    """List all loaded game states via API."""
    print(f"\n{'='*60}")
    print("Loaded Game States")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/aggregator/states")
            response.raise_for_status()
            data = response.json()
            states = data.get("states", [])
        except httpx.ConnectError:
            print(f"\n❌ Error: Cannot connect to server at {BASE_URL}")
            print("   Make sure the server is running: uvicorn backend.main:app --reload")
            return
        except Exception as e:
            print(f"Error: {e}")
            return
    
    if not states:
        print("No games currently loaded")
        return
    
    print(f"Total: {len(states)} games\n")
    
    for state in states:
        print(f"{state.get('game_id')}")
        print(f"  {state.get('away_team')} @ {state.get('home_team')}")
        print(f"  Phase: {state.get('phase')}")
        print(f"  Markets: {len(state.get('markets', {}))}")
        nba = state.get('nba_state')
        if nba:
            print(f"  Score: {nba.get('away_score')} - {nba.get('home_score')}")
        print()


async def monitor_game(game_id: str) -> None:
    """Poll for updates and print them (API-based monitoring)."""
    print(f"\n{'='*60}")
    print(f"Monitoring Game: {game_id}")
    print("Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Initial fetch
        try:
            response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
            response.raise_for_status()
            state = response.json()
        except httpx.ConnectError:
            print(f"\n❌ Error: Cannot connect to server at {BASE_URL}")
            print("   Make sure the server is running: uvicorn backend.main:app --reload")
            return
        except httpx.HTTPStatusError:
            print(f"Game not loaded: {game_id}")
            return
        
        print(f"Watching: {state.get('away_team')} @ {state.get('home_team')}\n")
        
        last_nba_score = None
        last_consensus = None
        
        try:
            while True:
                await asyncio.sleep(2)  # Poll every 2 seconds
                
                try:
                    response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
                    response.raise_for_status()
                    state = response.json()
                except:
                    continue
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Check NBA score changes
                nba = state.get('nba_state')
                if nba:
                    current_score = (nba.get('home_score'), nba.get('away_score'))
                    if current_score != last_nba_score:
                        print(f"[{timestamp}] NBA Update")
                        print(f"  Score: {nba.get('away_score')} - {nba.get('home_score')}")
                        print(f"  Period: {nba.get('period')}, Time: {nba.get('time_remaining')}")
                        last_nba_score = current_score
                
                # Check consensus changes
                consensus = state.get('consensus')
                if consensus:
                    home_prob = consensus.get('home_win_probability')
                    if home_prob != last_consensus:
                        print(f"[{timestamp}] Odds Update")
                        print(f"  Consensus: Home {float(home_prob or 0)*100:.1f}%")
                        last_consensus = home_prob
                
        except KeyboardInterrupt:
            print("\nStopping monitor...")


def main():
    parser = argparse.ArgumentParser(description="Test the Data Aggregator")
    
    parser.add_argument("--load-game", action="store_true", help="Load a game into aggregator")
    parser.add_argument("--date", type=str, help="Date for game selection (YYYY-MM-DD)")
    parser.add_argument("--index", type=int, default=0, help="Index of game to select")
    
    parser.add_argument("--show-state", action="store_true", help="Show state for a game")
    parser.add_argument("--game-id", type=str, help="Game UUID")
    
    parser.add_argument("--list-states", action="store_true", help="List all loaded states")
    
    parser.add_argument("--monitor", action="store_true", help="Monitor a game in real-time")
    
    args = parser.parse_args()
    
    if args.load_game:
        if not args.date:
            print("Error: --date required for --load-game")
            sys.exit(1)
        asyncio.run(load_game_flow(args.date, args.index))
    
    elif args.show_state:
        if not args.game_id:
            print("Error: --game-id required for --show-state")
            sys.exit(1)
        asyncio.run(show_state(args.game_id))
    
    elif args.list_states:
        asyncio.run(list_states())
    
    elif args.monitor:
        if not args.game_id:
            print("Error: --game-id required for --monitor")
            sys.exit(1)
        asyncio.run(monitor_game(args.game_id))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

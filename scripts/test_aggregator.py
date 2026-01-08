#!/usr/bin/env python
"""
Test script for the Data Aggregator.

Usage:
    python scripts/test_aggregator.py --load-game --date 2026-01-08 --index 0
    python scripts/test_aggregator.py --show-state --game-id <UUID>
    python scripts/test_aggregator.py --list-states
    python scripts/test_aggregator.py --monitor --game-id <UUID>
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings
from backend.engine.aggregator import get_aggregator, EventType
from backend.models.game_state import GameState


async def load_game_flow(date: str, index: int) -> None:
    """
    Full flow to load a game:
    1. List available games on Kalshi for the date
    2. Select game by index
    3. Match to NBA game
    4. Store in database
    5. Load into aggregator
    """
    print(f"\n{'='*60}")
    print(f"Loading game for date: {date}, index: {index}")
    print(f"{'='*60}\n")
    
    # Import clients
    from backend.integrations.kalshi.client import KalshiClient
    from backend.integrations.balldontlie.client import BallDontLieClient
    from backend.database import helpers as db
    
    kalshi = KalshiClient()
    bdl = BallDontLieClient()
    
    try:
        # Step 1: List available NBA games on Kalshi
        print("Step 1: Fetching available NBA games from Kalshi...")
        games = await kalshi.get_nba_games_for_date(date)
        
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
        print(f"\nSelected: {selected.get('away_team')} @ {selected.get('home_team')}")
        
        # Step 2: Match to NBA game
        print("\nStep 2: Matching to NBA game...")
        event_ticker = selected.get('event_ticker')
        
        try:
            nba_game = await bdl.match_kalshi_game(event_ticker)
            print(f"Matched to NBA game ID: {nba_game.get('id')}")
            print(f"  {nba_game.get('visitor_team', {}).get('full_name')} @ {nba_game.get('home_team', {}).get('full_name')}")
        except Exception as e:
            print(f"Could not match NBA game: {e}")
            nba_game = None
        
        # Step 3: Check if game exists in database
        print("\nStep 3: Checking database...")
        from backend.config.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        existing = supabase.table("games").select("*").eq(
            "kalshi_event_ticker", event_ticker
        ).execute()
        
        if existing.data:
            game_record = existing.data[0]
            print(f"Game already in database: {game_record['id']}")
        else:
            # Create new game record
            print("Creating new game record...")
            
            game_date_str = selected.get('game_date', date)
            if isinstance(game_date_str, str):
                try:
                    game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                except ValueError:
                    game_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                game_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Extract markets from nested dict structure
            # Structure: {"moneyline": {"markets": [...]}, "spread": {...}, ...}
            markets_dict = selected.get('markets', {})
            all_markets = []
            first_market_ticker = event_ticker
            
            for market_type, market_data in markets_dict.items():
                if isinstance(market_data, dict):
                    market_list = market_data.get('markets', [])
                    for m in market_list:
                        m['type'] = market_type  # Add type to each market
                        all_markets.append(m)
                        # Get first market ticker
                        if first_market_ticker == event_ticker and m.get('ticker'):
                            first_market_ticker = m.get('ticker')
            
            new_game = {
                "kalshi_event_ticker": event_ticker,
                "kalshi_market_ticker_seed": first_market_ticker,
                "home_team": selected.get('home_team', ''),
                "away_team": selected.get('away_team', ''),
                "game_date": game_date.isoformat(),
                "status": "scheduled",
                "is_active": True
            }
            
            if nba_game:
                new_game["nba_game_id"] = nba_game.get("id")
                new_game["home_team_id"] = nba_game.get("home_team", {}).get("id")
                new_game["away_team_id"] = nba_game.get("visitor_team", {}).get("id")
            
            result = supabase.table("games").insert(new_game).execute()
            game_record = result.data[0]
            print(f"Created game: {game_record['id']}")
            
            # Store markets
            print(f"Storing {len(all_markets)} markets...")
            for market in all_markets:
                market_record = {
                    "game_id": game_record['id'],
                    "ticker": market.get('ticker', ''),
                    "market_type": market.get('type', 'unknown'),
                    "strike_value": market.get('strike_value'),
                    "side": market.get('side'),
                    "status": market.get('status', 'open')
                }
                try:
                    supabase.table("kalshi_markets").insert(market_record).execute()
                except Exception as e:
                    print(f"  Warning: Could not store market {market.get('ticker')}: {e}")
        
        # Step 4: Load into aggregator
        print("\nStep 4: Loading into aggregator...")
        aggregator = get_aggregator()
        
        game_id = game_record['id']
        state = await aggregator.load_game(game_id)
        
        if state:
            print(f"\n{'='*60}")
            print("GAME LOADED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"Game ID: {state.game_id}")
            print(f"Event Ticker: {state.event_ticker}")
            print(f"Teams: {state.away_team} @ {state.home_team}")
            print(f"Phase: {state.phase}")
            print(f"Markets: {len(state.markets)}")
            print(f"Has NBA Data: {state.has_nba_data}")
            print(f"Has Odds Data: {state.has_odds_data}")
            
            if state.nba_state:
                print(f"\nNBA State:")
                print(f"  NBA Game ID: {state.nba_state.nba_game_id}")
                print(f"  Status: {state.nba_state.status}")
                print(f"  Score: {state.nba_state.away_score} - {state.nba_state.home_score}")
            
            if state.consensus:
                print(f"\nConsensus Odds:")
                print(f"  Sportsbooks: {state.consensus.num_sportsbooks}")
                if state.consensus.home_win_probability:
                    print(f"  Home Win: {float(state.consensus.home_win_probability)*100:.1f}%")
                if state.consensus.away_win_probability:
                    print(f"  Away Win: {float(state.consensus.away_win_probability)*100:.1f}%")
        else:
            print("Failed to load game into aggregator")
        
    finally:
        await kalshi.close()
        await bdl.close()


async def show_state(game_id: str) -> None:
    """Display current GameState for a loaded game."""
    print(f"\n{'='*60}")
    print(f"Game State: {game_id}")
    print(f"{'='*60}\n")
    
    aggregator = get_aggregator()
    state = aggregator.get_game_state(game_id)
    
    if not state:
        print(f"Game not loaded: {game_id}")
        print("\nLoaded games:")
        for gid in aggregator.get_game_ids():
            s = aggregator.get_game_state(gid)
            if s:
                print(f"  {gid}: {s.away_team} @ {s.home_team}")
        return
    
    print(f"Event Ticker: {state.event_ticker}")
    print(f"Teams: {state.away_team} @ {state.home_team}")
    print(f"Date: {state.game_date}")
    print(f"Phase: {state.phase}")
    print(f"Active: {state.is_active}")
    print(f"Last Updated: {state.last_updated}")
    
    print(f"\n--- Markets ({len(state.markets)}) ---")
    for ticker, market in state.markets.items():
        print(f"\n{ticker}:")
        print(f"  Type: {market.market_type}")
        if market.strike_value:
            print(f"  Strike: {market.strike_value}")
        if market.orderbook:
            ob = market.orderbook
            print(f"  Yes Bid/Ask: {ob.yes_bid}/{ob.yes_ask}")
            if ob.mid_price:
                print(f"  Mid Price: {ob.mid_price}")
            if ob.spread:
                print(f"  Spread: {ob.spread}")
    
    if state.nba_state:
        print(f"\n--- NBA State ---")
        nba = state.nba_state
        print(f"NBA Game ID: {nba.nba_game_id}")
        print(f"Status: {nba.status}")
        print(f"Period: {nba.period}")
        print(f"Time: {nba.time_remaining}")
        print(f"Score: {nba.away_score} - {nba.home_score} (Away - Home)")
        print(f"Total: {nba.total_score}")
        print(f"Differential: {nba.score_differential:+d}")
    
    if state.odds:
        print(f"\n--- Betting Odds ({len(state.odds)} sportsbooks) ---")
        for vendor, odds in state.odds.items():
            print(f"\n{vendor}:")
            if odds.moneyline_home:
                print(f"  ML: Home {odds.moneyline_home:+d} / Away {odds.moneyline_away:+d}")
            if odds.spread_home_value:
                print(f"  Spread: {odds.spread_home_value} ({odds.spread_home_odds:+d})")
            if odds.total_value:
                print(f"  Total: {odds.total_value} (O {odds.total_over_odds:+d} / U {odds.total_under_odds:+d})")
    
    if state.consensus:
        print(f"\n--- Consensus ---")
        c = state.consensus
        print(f"Sportsbooks: {c.num_sportsbooks}")
        if c.home_win_probability:
            print(f"Home Win Prob: {float(c.home_win_probability)*100:.1f}%")
        if c.away_win_probability:
            print(f"Away Win Prob: {float(c.away_win_probability)*100:.1f}%")
        if c.spread_line:
            print(f"Spread Line: {c.spread_line}")
        if c.total_line:
            print(f"Total Line: {c.total_line}")


async def list_states() -> None:
    """List all loaded game states."""
    print(f"\n{'='*60}")
    print("Loaded Game States")
    print(f"{'='*60}\n")
    
    aggregator = get_aggregator()
    states = aggregator.get_all_game_states()
    
    if not states:
        print("No games currently loaded")
        return
    
    print(f"Total: {len(states)} games\n")
    
    for game_id, state in states.items():
        print(f"{game_id}")
        print(f"  {state.away_team} @ {state.home_team}")
        print(f"  Phase: {state.phase}")
        print(f"  Markets: {len(state.markets)}")
        if state.nba_state:
            print(f"  Score: {state.nba_state.away_score} - {state.nba_state.home_score}")
        print()


async def monitor_game(game_id: str) -> None:
    """Subscribe to updates and print them in real-time."""
    print(f"\n{'='*60}")
    print(f"Monitoring Game: {game_id}")
    print("Press Ctrl+C to stop")
    print(f"{'='*60}\n")
    
    aggregator = get_aggregator()
    state = aggregator.get_game_state(game_id)
    
    if not state:
        print(f"Game not loaded: {game_id}")
        return
    
    print(f"Watching: {state.away_team} @ {state.home_team}\n")
    
    async def on_update(gid: str, gs: GameState, event_type: EventType):
        if gid != game_id:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event_type.value}")
        
        if event_type == EventType.NBA_UPDATE and gs.nba_state:
            print(f"  Score: {gs.nba_state.away_score} - {gs.nba_state.home_score}")
            print(f"  Period: {gs.nba_state.period}, Time: {gs.nba_state.time_remaining}")
        
        elif event_type == EventType.ORDERBOOK_UPDATE:
            for ticker, market in gs.markets.items():
                if market.orderbook and market.orderbook.mid_price:
                    print(f"  {ticker}: {market.orderbook.mid_price}")
        
        elif event_type == EventType.ODDS_UPDATE:
            if gs.consensus:
                print(f"  Consensus: Home {float(gs.consensus.home_win_probability or 0)*100:.1f}%")
    
    aggregator.subscribe(on_update)
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        aggregator.unsubscribe(on_update)


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

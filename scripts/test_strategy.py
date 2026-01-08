"""
Test script for Sharp Line Detection strategy.

Usage:
    python scripts/test_strategy.py --list-types
    python scripts/test_strategy.py --load-and-test --game-id <UUID>
    python scripts/test_strategy.py --evaluate --game-id <UUID>
"""

import asyncio
import argparse
import sys
import time
sys.path.insert(0, '.')

import httpx


BASE_URL = "http://localhost:8000"


async def list_strategy_types():
    """List available strategy types."""
    print("\n" + "="*60)
    print("Available Strategy Types")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/strategies/types")
        data = response.json()
        
        for strategy in data["strategy_types"]:
            print(f"\n  Type: {strategy['type']}")
            print(f"  Name: {strategy['name']}")
            print(f"  Description: {strategy['description']}")
            print(f"  Default Config:")
            for key, value in strategy['default_config'].items():
                print(f"    {key}: {value}")


async def load_and_test(game_id: str):
    """Load Sharp Line strategy and test it on a game."""
    print("\n" + "="*60)
    print("Sharp Line Strategy Test")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Load the strategy
        print("\n1. Loading Sharp Line strategy...")
        response = await client.post(
            f"{BASE_URL}/api/strategies/load",
            json={
                "strategy_type": "sharp_line",
                "enable": True,
                "config": {
                    "threshold_percent": 0.3,  # Lower threshold for testing
                    "min_sample_sportsbooks": 1,  # Lower for testing
                    "min_ev_percent": 0.1,  # Lower for testing
                    "cooldown_minutes": 0.1,  # Short cooldown for testing
                    "position_size": 10
                }
            }
        )
        
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return
        
        strategy_data = response.json()
        strategy_id = strategy_data["strategy_id"]
        print(f"   ✓ Strategy loaded: {strategy_id}")
        print(f"   Name: {strategy_data['strategy_name']}")
        print(f"   Enabled: {strategy_data['is_enabled']}")
        
        # Step 2: Make sure game is loaded in aggregator
        print(f"\n2. Checking game {game_id}...")
        response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
        
        if response.status_code == 404:
            print("   Game not loaded in aggregator. Loading now...")
            response = await client.post(f"{BASE_URL}/api/aggregator/load/{game_id}")
            if response.status_code != 200:
                print(f"   Error loading game: {response.text}")
                return
            print("   ✓ Game loaded")
            
            # Wait a moment for data to be fetched
            print("   Waiting for data refresh...")
            await asyncio.sleep(2)
        else:
            print("   ✓ Game already loaded")
        
        # Step 3: Evaluate the strategy
        print(f"\n3. Evaluating strategy on game...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/strategies/{strategy_id}/evaluate",
                params={"game_id": game_id}
            )
        except Exception as e:
            print(f"   Request error: {e}")
            return
        
        if response.status_code != 200:
            print(f"   Error ({response.status_code}): {response.text}")
            # Try to parse JSON for more details
            try:
                error_detail = response.json()
                print(f"   Detail: {error_detail.get('detail', 'No detail')}")
            except:
                pass
            return
        
        eval_data = response.json()
        print(f"   ✓ Evaluation complete")
        print(f"   Signals generated: {eval_data['signals_generated']}")
        
        if eval_data['signals']:
            print("\n   Generated Signals:")
            for signal in eval_data['signals']:
                print(f"\n   Market: {signal['market_ticker']}")
                print(f"   Side: {signal['side'].upper()}")
                print(f"   Quantity: {signal['quantity']}")
                print(f"   Confidence: {signal['confidence']:.2f}")
                print(f"   Reason: {signal['reason']}")
        else:
            print("\n   No signals generated. This could mean:")
            print("   - No divergence above threshold")
            print("   - Insufficient sportsbook sources")
            print("   - No consensus odds available")
        
        # Step 4: Show strategy status
        print(f"\n4. Strategy status...")
        response = await client.get(f"{BASE_URL}/api/strategies/{strategy_id}")
        status = response.json()
        print(f"   Recent signals: {len(status.get('recent_signals', []))}")


async def evaluate_all(game_id: str = None):
    """Run all enabled strategies."""
    print("\n" + "="*60)
    print("Evaluate All Strategies")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # List current strategies
        response = await client.get(f"{BASE_URL}/api/strategies/")
        strategies = response.json()
        
        print(f"\nLoaded strategies: {strategies['count']}")
        for s in strategies['strategies']:
            status = "✓ enabled" if s['is_enabled'] else "✗ disabled"
            print(f"  - {s['strategy_name']} ({s['strategy_id'][:8]}...): {status}")
        
        if strategies['count'] == 0:
            print("\nNo strategies loaded. Load one first with --load-and-test")
            return
        
        # Run evaluation
        print("\nRunning evaluation...")
        response = await client.post(f"{BASE_URL}/api/strategies/evaluate-all")
        results = response.json()
        
        print(f"\nResults:")
        print(f"  Games evaluated: {results['games_evaluated']}")
        print(f"  Total signals: {results['total_signals']}")
        
        for gid, signals in results['signals_by_game'].items():
            print(f"\n  Game {gid[:8]}...:")
            for signal in signals:
                print(f"    {signal['side'].upper()} {signal['quantity']} {signal['market_ticker']}")
                print(f"    Reason: {signal['reason']}")


async def test_momentum(game_id: str):
    """Test momentum strategy by building price history over time."""
    print("\n" + "="*60)
    print("Momentum Scalping Strategy Test")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Load momentum strategy with test config
        print("\n1. Loading Momentum strategy...")
        response = await client.post(
            f"{BASE_URL}/api/strategies/load",
            json={
                "strategy_type": "momentum",
                "enable": True,
                "config": {
                    "lookback_seconds": 30,      # Short lookback for testing
                    "min_price_change_cents": 1,  # Low threshold for testing
                    "cooldown_minutes": 0.1,      # 6 second cooldown for testing
                    "max_spread_cents": 10        # Higher spread tolerance for testing
                }
            }
        )
        
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return
        
        strategy_data = response.json()
        strategy_id = strategy_data["strategy_id"]
        print(f"   ✓ Strategy loaded: {strategy_id}")
        
        # Load game
        print(f"\n2. Loading game {game_id}...")
        response = await client.post(f"{BASE_URL}/api/aggregator/load/{game_id}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return
        print("   ✓ Game loaded")
        
        # Evaluate multiple times to build price history
        print("\n3. Building price history (evaluating every 5 seconds)...")
        
        for i in range(6):
            print(f"   Evaluation {i+1}/6...")
            response = await client.post(
                f"{BASE_URL}/api/strategies/{strategy_id}/evaluate",
                params={"game_id": game_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["signals_generated"] > 0:
                    print(f"   ✓ Signal generated!")
                    for signal in data["signals"]:
                        print(f"      {signal['side'].upper()} {signal['quantity']} {signal['market_ticker']}")
                        print(f"      Reason: {signal['reason']}")
            
            if i < 5:
                time.sleep(5)
        
        # Final status
        print(f"\n4. Strategy status...")
        response = await client.get(f"{BASE_URL}/api/strategies/{strategy_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"   Recent signals: {len(status.get('recent_signals', []))}")


async def show_game_state(game_id: str):
    """Show the current game state for debugging."""
    print("\n" + "="*60)
    print(f"Game State: {game_id}")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/api/aggregator/state/{game_id}")
        
        if response.status_code == 404:
            print("Game not loaded.")
            return
        
        state = response.json()
        
        print(f"\n  Home: {state.get('home_team')}")
        print(f"  Away: {state.get('away_team')}")
        print(f"  Phase: {state.get('phase')}")
        
        # Consensus odds
        consensus = state.get('consensus')
        if consensus:
            print(f"\n  Consensus Odds ({consensus.get('num_sportsbooks', 0)} sportsbooks):")
            if consensus.get('home_win_probability'):
                print(f"    Home Win: {float(consensus['home_win_probability'])*100:.1f}%")
            if consensus.get('away_win_probability'):
                print(f"    Away Win: {float(consensus['away_win_probability'])*100:.1f}%")
        else:
            print("\n  No consensus odds available")
        
        # Markets
        markets = state.get('markets', {})
        print(f"\n  Markets ({len(markets)}):")
        for ticker, market in markets.items():
            orderbook = market.get('orderbook')
            if orderbook:
                mid = orderbook.get('mid_price')
                print(f"    {ticker}: mid={mid}")
            else:
                print(f"    {ticker}: no orderbook")


def main():
    parser = argparse.ArgumentParser(description="Test trading strategies")
    parser.add_argument("--list-types", action="store_true", help="List available strategy types")
    parser.add_argument("--load-and-test", action="store_true", help="Load Sharp Line strategy and test on a game")
    parser.add_argument("--test-momentum", action="store_true", help="Test momentum strategy")
    parser.add_argument("--evaluate", action="store_true", help="Run all enabled strategies")
    parser.add_argument("--show-state", action="store_true", help="Show game state for debugging")
    parser.add_argument("--game-id", type=str, help="Game UUID")
    
    args = parser.parse_args()
    
    if args.list_types:
        asyncio.run(list_strategy_types())
    elif args.load_and_test:
        if not args.game_id:
            print("Error: --game-id required")
            sys.exit(1)
        asyncio.run(load_and_test(args.game_id))
    elif args.test_momentum:
        if not args.game_id:
            print("Error: --game-id required")
            sys.exit(1)
        asyncio.run(test_momentum(args.game_id))
    elif args.evaluate:
        asyncio.run(evaluate_all(args.game_id))
    elif args.show_state:
        if not args.game_id:
            print("Error: --game-id required")
            sys.exit(1)
        asyncio.run(show_game_state(args.game_id))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

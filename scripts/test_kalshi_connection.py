"""
Test script for Kalshi API integration.

Usage:
    python scripts/test_kalshi_connection.py --test-auth
    python scripts/test_kalshi_connection.py --list-games --date 2026-01-08
    python scripts/test_kalshi_connection.py --test-websocket --ticker KXNBAGAME-26JAN08LALSAC
"""

import asyncio
import argparse
import sys
from datetime import date

# Add project root to path
sys.path.insert(0, '.')

from backend.integrations.kalshi.client import KalshiClient
from backend.integrations.kalshi.websocket import KalshiWebSocketClient
from backend.integrations.kalshi.exceptions import KalshiError


async def test_auth():
    """Test authentication by calling exchange status."""
    print("=" * 60)
    print("Testing Kalshi Authentication")
    print("=" * 60)
    
    try:
        client = KalshiClient()
        print("✓ Client initialized with RSA-PSS authentication")
        
        print("\nFetching exchange status...")
        status = await client.get_exchange_status()
        
        print(f"\n✓ Authentication successful!")
        print(f"\nExchange Status:")
        print(f"  - Trading Active: {status.get('trading_active', 'N/A')}")
        print(f"  - Exchange Active: {status.get('exchange_active', 'N/A')}")
        
        return True
        
    except KalshiError as e:
        print(f"\n✗ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def list_games(target_date: str):
    """List all NBA games for a date."""
    print("=" * 60)
    print(f"Fetching NBA Games for {target_date}")
    print("=" * 60)
    
    try:
        client = KalshiClient()
        games = await client.get_nba_games_for_date(target_date)
        
        if not games:
            print(f"\nNo games found for {target_date}")
            print("\nTips:")
            print("  - Make sure there are NBA games scheduled for this date")
            print("  - Try a different date with known games")
            return None
        
        print(f"\n✓ Found {len(games)} games:\n")
        
        for i, game in enumerate(games):
            print(f"  [{i}] {game['away_team']} @ {game['home_team']}")
            print(f"      Event: {game['event_ticker']}")
            print(f"      Title: {game.get('title', 'N/A')}")
            print(f"      Markets: {game['market_count']} available")
            
            # Show market types
            market_types = list(game.get('markets', {}).keys())
            if market_types:
                print(f"      Types: {', '.join(market_types)}")
            print()
        
        return games
        
    except KalshiError as e:
        print(f"\n✗ Failed to fetch games: {e}")
        return None
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_market_details(ticker: str):
    """Get details for a specific market."""
    print("=" * 60)
    print(f"Fetching Market Details: {ticker}")
    print("=" * 60)
    
    try:
        client = KalshiClient()
        
        print("\nFetching market info...")
        market = await client.get_market(ticker)
        
        print(f"\n✓ Market found!\n")
        print(f"  Ticker: {market.get('ticker')}")
        print(f"  Title: {market.get('title', 'N/A')}")
        print(f"  Status: {market.get('status', 'N/A')}")
        print(f"  Yes Bid: {market.get('yes_bid', 'N/A')}")
        print(f"  Yes Ask: {market.get('yes_ask', 'N/A')}")
        print(f"  Volume: {market.get('volume', 'N/A')}")
        
        print("\nFetching orderbook...")
        orderbook = await client.get_market_orderbook(ticker, depth=5)
        
        print(f"\n✓ Orderbook:\n")
        print("  YES side:")
        for level in orderbook.get('yes', [])[:5]:
            print(f"    Price: {level.get('price')} | Qty: {level.get('quantity')}")
        
        print("\n  NO side:")
        for level in orderbook.get('no', [])[:5]:
            print(f"    Price: {level.get('price')} | Qty: {level.get('quantity')}")
        
        return market
        
    except KalshiError as e:
        print(f"\n✗ Failed to fetch market: {e}")
        return None
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return None


async def test_websocket(ticker: str):
    """Test WebSocket connection and subscription."""
    print("=" * 60)
    print(f"Testing WebSocket Connection")
    print(f"Ticker: {ticker}")
    print("=" * 60)
    
    ws_client = None
    try:
        ws_client = KalshiWebSocketClient()
        print("✓ WebSocket client initialized")
        
        print("\nConnecting to WebSocket...")
        await ws_client.connect()
        print(f"✓ Connected to {ws_client.ws_url}")
        
        print(f"\nSubscribing to {ticker}...")
        await ws_client.subscribe([ticker], ["ticker", "orderbook_delta"])
        print("✓ Subscribed!")
        
        print("\nListening for messages (Ctrl+C to stop)...\n")
        print("-" * 60)
        
        message_count = 0
        async for message in ws_client.listen():
            message_count += 1
            msg_type = message.get('type', 'unknown')
            data = message.get('data', {})
            
            if msg_type == 'ticker':
                print(f"[{message_count}] TICKER:")
                print(f"    Market: {data.get('market_ticker', 'N/A')}")
                print(f"    Yes Bid: {data.get('yes_bid', 'N/A')} | Yes Ask: {data.get('yes_ask', 'N/A')}")
            elif msg_type == 'orderbook_snapshot':
                print(f"[{message_count}] ORDERBOOK SNAPSHOT:")
                print(f"    Market: {data.get('market_ticker', 'N/A')}")
                yes_levels = len(data.get('yes', []))
                no_levels = len(data.get('no', []))
                print(f"    Levels: {yes_levels} yes, {no_levels} no")
            elif msg_type == 'orderbook_delta':
                print(f"[{message_count}] ORDERBOOK DELTA:")
                print(f"    Market: {data.get('market_ticker', 'N/A')}")
            elif msg_type == 'subscribed':
                print(f"[{message_count}] SUBSCRIBED: Confirmation received")
            elif msg_type == 'error':
                print(f"[{message_count}] ERROR: {data}")
            else:
                print(f"[{message_count}] {msg_type}: {data}")
            
            # Stop after 10 messages for demo
            if message_count >= 10:
                print("\n" + "-" * 60)
                print("(Stopping after 10 messages)")
                break
        
        print("\n✓ WebSocket test complete!")
        return True
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return True
    except KalshiError as e:
        print(f"\n✗ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if ws_client and ws_client.is_connected:
            print("\nDisconnecting...")
            await ws_client.disconnect()
            print("✓ Disconnected")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Kalshi API integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Test authentication:
    python scripts/test_kalshi_connection.py --test-auth
    
  List games for today:
    python scripts/test_kalshi_connection.py --list-games --date 2026-01-08
    
  Get market details:
    python scripts/test_kalshi_connection.py --market KXNBAGAME-26JAN08LALSAC-Y
    
  Test WebSocket:
    python scripts/test_kalshi_connection.py --test-websocket --ticker KXNBAGAME-26JAN08LALSAC-Y
        """
    )
    
    parser.add_argument(
        "--test-auth", 
        action="store_true", 
        help="Test authentication with Kalshi API"
    )
    parser.add_argument(
        "--list-games", 
        action="store_true", 
        help="List available NBA games for a date"
    )
    parser.add_argument(
        "--date", 
        type=str, 
        default=str(date.today()),
        help="Date for game listing (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--market",
        type=str,
        help="Get details for a specific market ticker"
    )
    parser.add_argument(
        "--test-websocket", 
        action="store_true", 
        help="Test WebSocket connection and subscription"
    )
    parser.add_argument(
        "--ticker", 
        type=str, 
        help="Market ticker for WebSocket test"
    )
    
    args = parser.parse_args()
    
    # Determine which test to run
    if args.test_auth:
        success = asyncio.run(test_auth())
        sys.exit(0 if success else 1)
        
    elif args.list_games:
        games = asyncio.run(list_games(args.date))
        sys.exit(0 if games is not None else 1)
        
    elif args.market:
        market = asyncio.run(get_market_details(args.market))
        sys.exit(0 if market is not None else 1)
        
    elif args.test_websocket:
        if not args.ticker:
            print("Error: --ticker required for --test-websocket")
            print("Example: --test-websocket --ticker KXNBAGAME-26JAN08LALSAC-Y")
            sys.exit(1)
        success = asyncio.run(test_websocket(args.ticker))
        sys.exit(0 if success else 1)
        
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("  1. Test auth:   python scripts/test_kalshi_connection.py --test-auth")
        print("  2. List games:  python scripts/test_kalshi_connection.py --list-games --date 2026-01-08")
        print("=" * 60)


if __name__ == "__main__":
    main()

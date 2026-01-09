"""
Test script for Order Execution Engine.

Usage:
    python scripts/test_execution.py --stats
    python scripts/test_execution.py --manual-order --game-id <UUID> --market <TICKER> --side yes --quantity 10
    python scripts/test_execution.py --execute-strategy --strategy-id <UUID> --game-id <UUID>
    python scripts/test_execution.py --view-orders
    python scripts/test_execution.py --view-positions
    python scripts/test_execution.py --pnl
    python scripts/test_execution.py --refresh-pnl
    python scripts/test_execution.py --close-position <TICKER>
    python scripts/test_execution.py --performance
"""

import asyncio
import argparse
import sys
sys.path.insert(0, '.')

import httpx


BASE_URL = "http://localhost:8000"


async def get_stats():
    """Get execution engine statistics."""
    print("\n" + "="*60)
    print("Execution Engine Statistics")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/execution/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"\n   Running: {stats['running']}")
            print(f"   Daily orders: {stats['daily_order_count']}/{stats['max_daily_orders']}")
            print(f"   Open positions: {stats['open_positions_count']}")
            print(f"   Max position size: {stats['max_position_size']}")
        else:
            print(f"   Error: {response.text}")


async def manual_order(game_id: str, market: str, side: str, quantity: int):
    """Place a manual order."""
    print("\n" + "="*60)
    print("Manual Order Execution")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n   Game: {game_id}")
        print(f"   Market: {market}")
        print(f"   Side: {side.upper()}")
        print(f"   Quantity: {quantity}")
        
        response = await client.post(
            f"{BASE_URL}/api/execution/execute/manual",
            json={
                "game_id": game_id,
                "market_ticker": market,
                "side": side,
                "quantity": quantity,
                "reason": "Test manual order"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n   ✓ Order filled!")
            print(f"   Order ID: {result['order_id']}")
            print(f"   Fill price: {result['fill_price']}¢")
            if result.get('position'):
                print(f"   Position: {result['position']['quantity']} @ {result['position']['avg_price']:.1f}¢")
        else:
            # Handle non-JSON error responses
            try:
                error_detail = response.json().get('detail', response.text)
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            print(f"\n   ✗ Order failed: {error_detail}")


async def execute_strategy(strategy_id: str, game_id: str):
    """Execute a strategy and place orders for any signals."""
    print("\n" + "="*60)
    print("Strategy Execution")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n   Strategy: {strategy_id}")
        print(f"   Game: {game_id}")
        
        response = await client.post(
            f"{BASE_URL}/api/execution/execute/strategy/{strategy_id}",
            params={"game_id": game_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n   Signals generated: {result['signals_generated']}")
            print(f"   Orders executed: {result['orders_executed']}")
            print(f"   Orders rejected: {result['orders_rejected']}")
            
            if result.get('orders'):
                print("\n   Orders:")
                for order in result['orders']:
                    print(f"      {order['side'].upper()} {order['quantity']} {order['market']}")
                    print(f"         Fill: {order['fill_price']}¢, Status: {order['status']}")
            
            if result.get('rejections'):
                print("\n   Rejections:")
                for reason in result['rejections']:
                    print(f"      - {reason}")
        else:
            print(f"\n   Error: {response.json().get('detail', response.text)}")


async def view_orders(limit: int = 20):
    """View recent orders."""
    print("\n" + "="*60)
    print("Recent Orders")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/execution/orders",
            params={"limit": limit}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Total: {data['count']} orders")
            
            if data['orders']:
                for order in data['orders'][:limit]:
                    status = "✓" if order['status'] == 'filled' else "✗"
                    print(f"\n   {status} {order['side'].upper()} {order['quantity']} {order['market_ticker']}")
                    print(f"      Status: {order['status']}")
                    if order.get('filled_price'):
                        print(f"      Fill: {order['filled_price']}¢")
                    strategy_id = order.get('strategy_id') or 'manual'
                    print(f"      Strategy: {strategy_id[:8]}...")
                    print(f"      Time: {order.get('placed_at', order.get('created_at', 'unknown'))}")
            else:
                print("\n   No orders found")
        else:
            print(f"   Error: {response.text}")


async def view_positions():
    """View current positions."""
    print("\n" + "="*60)
    print("Current Positions")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/execution/positions/open")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Open positions: {data['count']}")
            
            if data['positions']:
                for pos in data['positions']:
                    print(f"\n   {pos['side'].upper()} {pos['quantity']} {pos['market_ticker']}")
                    print(f"      Avg entry: {pos['avg_entry_price']:.1f}¢")
                    print(f"      Total cost: {pos['total_cost']:.1f}¢")
            else:
                print("\n   No open positions")
        else:
            print(f"   Error: {response.text}")


async def get_pnl():
    """Get portfolio P&L summary."""
    print("\n" + "="*60)
    print("Portfolio P&L Summary")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/execution/pnl")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Open positions: {data['open_positions']}")
            print(f"   Total cost: {data['total_cost']:.1f}¢")
            print(f"   Unrealized P&L: {data['total_unrealized_pnl']:.1f}¢")
            print(f"   Realized P&L: {data['total_realized_pnl']:.1f}¢")
            print(f"   Total P&L: {data['total_pnl']:.1f}¢")
            
            if data.get('positions'):
                print("\n   Positions:")
                for pos in data['positions']:
                    pnl_str = f"+{pos['unrealized_pnl']:.1f}" if pos['unrealized_pnl'] >= 0 else f"{pos['unrealized_pnl']:.1f}"
                    print(f"      {pos['side'].upper()} {pos['quantity']} {pos['ticker']}")
                    print(f"         Entry: {pos['avg_entry']:.1f}¢, P&L: {pnl_str}¢")
        else:
            print(f"   Error: {response.text}")


async def refresh_pnl():
    """Refresh P&L based on current prices."""
    print("\n" + "="*60)
    print("Refreshing P&L")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/execution/pnl/refresh")
        
        if response.status_code == 200:
            data = response.json()
            portfolio = data.get('portfolio', {})
            print(f"\n   ✓ P&L refreshed")
            print(f"   Total unrealized: {portfolio.get('total_unrealized_pnl', 0):.1f}¢")
            print(f"   Positions updated: {portfolio.get('position_count', 0)}")
        else:
            print(f"   Error: {response.text}")


async def close_position_cmd(market_ticker: str, exit_price: float = None):
    """Close a position."""
    print("\n" + "="*60)
    print(f"Closing Position: {market_ticker}")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        params = {}
        if exit_price:
            params["exit_price"] = exit_price
        
        response = await client.post(
            f"{BASE_URL}/api/execution/positions/{market_ticker}/close",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ✓ Position closed")
            print(f"   Realized P&L: {data['realized_pnl']:.1f}¢")
        else:
            try:
                error_detail = response.json().get('detail', response.text)
            except:
                error_detail = response.text
            print(f"   Error: {error_detail}")


async def get_performance():
    """Get overall performance metrics."""
    print("\n" + "="*60)
    print("Trading Performance")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/execution/performance")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('order_stats', {})
            portfolio = data.get('portfolio', {})
            
            print(f"\n   Order Statistics:")
            print(f"      Total orders: {stats.get('total_orders', 0)}")
            print(f"      Filled: {stats.get('filled_orders', 0)}")
            print(f"      Rejected: {stats.get('rejected_orders', 0)}")
            print(f"      Fill rate: {stats.get('fill_rate', 0):.1f}%")
            print(f"      Avg fill price: {stats.get('avg_fill_price', 0):.1f}¢")
            
            print(f"\n   Portfolio:")
            print(f"      Open positions: {portfolio.get('open_positions', 0)}")
            print(f"      Total P&L: {portfolio.get('total_pnl', 0):.1f}¢")
        else:
            print(f"   Error: {response.text}")


def main():
    parser = argparse.ArgumentParser(description="Test Order Execution Engine")
    parser.add_argument("--stats", action="store_true", help="Get execution stats")
    parser.add_argument("--manual-order", action="store_true", help="Place manual order")
    parser.add_argument("--execute-strategy", action="store_true", help="Execute strategy signals")
    parser.add_argument("--view-orders", action="store_true", help="View recent orders")
    parser.add_argument("--view-positions", action="store_true", help="View current positions")
    parser.add_argument("--pnl", action="store_true", help="Get portfolio P&L")
    parser.add_argument("--refresh-pnl", action="store_true", help="Refresh P&L from market prices")
    parser.add_argument("--close-position", type=str, help="Close a position by market ticker")
    parser.add_argument("--exit-price", type=float, help="Exit price for closing position")
    parser.add_argument("--performance", action="store_true", help="Get trading performance metrics")
    parser.add_argument("--game-id", type=str, help="Game UUID")
    parser.add_argument("--market", type=str, help="Market ticker")
    parser.add_argument("--side", type=str, choices=["yes", "no"], help="Order side")
    parser.add_argument("--quantity", type=int, default=10, help="Order quantity")
    parser.add_argument("--strategy-id", type=str, help="Strategy UUID")
    parser.add_argument("--limit", type=int, default=20, help="Limit for queries")
    
    args = parser.parse_args()
    
    if args.stats:
        asyncio.run(get_stats())
    elif args.manual_order:
        if not all([args.game_id, args.market, args.side]):
            print("Error: --game-id, --market, and --side required for manual order")
            sys.exit(1)
        asyncio.run(manual_order(args.game_id, args.market, args.side, args.quantity))
    elif args.execute_strategy:
        if not all([args.strategy_id, args.game_id]):
            print("Error: --strategy-id and --game-id required")
            sys.exit(1)
        asyncio.run(execute_strategy(args.strategy_id, args.game_id))
    elif args.view_orders:
        asyncio.run(view_orders(args.limit))
    elif args.view_positions:
        asyncio.run(view_positions())
    elif args.pnl:
        asyncio.run(get_pnl())
    elif args.refresh_pnl:
        asyncio.run(refresh_pnl())
    elif args.close_position:
        asyncio.run(close_position_cmd(args.close_position, args.exit_price))
    elif args.performance:
        asyncio.run(get_performance())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Test script for Risk Management System.

Usage:
    python scripts/test_risk.py --status
    python scripts/test_risk.py --limits
    python scripts/test_risk.py --set-limit <type> <value>
    python scripts/test_risk.py --check --game-id <UUID> --market <TICKER> --side yes --quantity 10
    python scripts/test_risk.py --disable
    python scripts/test_risk.py --enable
    python scripts/test_risk.py --reset
"""

import asyncio
import argparse
import sys
sys.path.insert(0, '.')

import httpx


BASE_URL = "http://localhost:8000"


async def get_status():
    """Get risk management status."""
    print("\n" + "="*60)
    print("Risk Management Status")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/risk/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"\n   Enabled: {status['enabled']}")
            print(f"\n   Daily Loss: {status['daily_loss']:.1f}¢")
            print(f"   Weekly Loss: {status['weekly_loss']:.1f}¢")
            print(f"   Consecutive Losses: {status['consecutive_losses']}")
            print(f"   Cooldown Active: {status['cooldown_active']}")
            print(f"\n   Orders Today: {status['orders_today']}")
            print(f"   Orders This Hour: {status['orders_this_hour']}")
            print(f"   Total Exposure: {status['total_exposure']:.1f}¢")
            print(f"   Total Contracts: {status['total_contracts']}")
        else:
            print(f"   Error: {response.text}")


async def get_limits():
    """Get all risk limits."""
    print("\n" + "="*60)
    print("Risk Limits")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/risk/limits")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Enabled: {data['enabled']}")
            print("\n   Limits:")
            for limit_type, value in sorted(data['limits'].items()):
                # Format nicely
                if 'loss' in limit_type or 'exposure' in limit_type or 'risk' in limit_type:
                    print(f"      {limit_type}: {value:.0f}¢")
                else:
                    print(f"      {limit_type}: {value:.0f}")
        else:
            print(f"   Error: {response.text}")


async def set_limit(limit_type: str, value: float):
    """Set a risk limit."""
    print("\n" + "="*60)
    print(f"Setting Risk Limit: {limit_type}")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{BASE_URL}/api/risk/limits",
            json={"limit_type": limit_type, "value": value}
        )
        
        if response.status_code == 200:
            print(f"\n   ✓ Limit updated: {limit_type} = {value}")
        else:
            print(f"   Error: {response.json().get('detail', response.text)}")


async def check_order(game_id: str, market: str, side: str, quantity: int):
    """Check if an order would pass risk checks."""
    print("\n" + "="*60)
    print("Risk Check (Hypothetical Order)")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/risk/check",
            params={
                "game_id": game_id,
                "market_ticker": market,
                "side": side,
                "quantity": quantity
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            status = "✓ APPROVED" if result['would_approve'] else "✗ REJECTED"
            print(f"\n   {status}")
            print(f"   Reason: {result['reason']}")
            if result.get('limit_type'):
                print(f"   Limit: {result['limit_type']}")
                print(f"   Current: {result['current_value']}, Max: {result['limit_value']}")
        else:
            print(f"   Error: {response.text}")


async def enable_risk():
    """Enable risk management."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/risk/enable")
        if response.status_code == 200:
            print("\n   ✓ Risk management ENABLED")
        else:
            print(f"   Error: {response.text}")


async def disable_risk():
    """Disable risk management."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/risk/disable")
        if response.status_code == 200:
            data = response.json()
            print(f"\n   ⚠ Risk management DISABLED")
            print(f"   Warning: {data.get('warning')}")
        else:
            print(f"   Error: {response.text}")


async def reset_risk():
    """Reset risk counters."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/risk/reset")
        if response.status_code == 200:
            print("\n   ✓ Risk counters reset")
        else:
            print(f"   Error: {response.text}")


def main():
    parser = argparse.ArgumentParser(description="Test Risk Management System")
    parser.add_argument("--status", action="store_true", help="Get risk status")
    parser.add_argument("--limits", action="store_true", help="Get risk limits")
    parser.add_argument("--set-limit", nargs=2, metavar=("TYPE", "VALUE"), help="Set a risk limit")
    parser.add_argument("--check", action="store_true", help="Check hypothetical order")
    parser.add_argument("--enable", action="store_true", help="Enable risk management")
    parser.add_argument("--disable", action="store_true", help="Disable risk management")
    parser.add_argument("--reset", action="store_true", help="Reset risk counters")
    parser.add_argument("--game-id", type=str, help="Game UUID for check")
    parser.add_argument("--market", type=str, help="Market ticker for check")
    parser.add_argument("--side", type=str, choices=["yes", "no"], help="Order side")
    parser.add_argument("--quantity", type=int, default=10, help="Order quantity")
    
    args = parser.parse_args()
    
    if args.status:
        asyncio.run(get_status())
    elif args.limits:
        asyncio.run(get_limits())
    elif args.set_limit:
        limit_type, value = args.set_limit
        asyncio.run(set_limit(limit_type, float(value)))
    elif args.check:
        if not all([args.game_id, args.market, args.side]):
            print("Error: --game-id, --market, and --side required for check")
            sys.exit(1)
        asyncio.run(check_order(args.game_id, args.market, args.side, args.quantity))
    elif args.enable:
        asyncio.run(enable_risk())
    elif args.disable:
        asyncio.run(disable_risk())
    elif args.reset:
        asyncio.run(reset_risk())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""Debug script to check Kalshi API responses."""
import asyncio
import sys
sys.path.insert(0, ".")

from backend.integrations.kalshi.client import KalshiClient

async def main():
    client = KalshiClient()
    
    ticker = "KXNBAGAME-26JAN08DALUTA-DAL"
    print(f"Fetching market data for: {ticker}")
    
    try:
        market_data = await client.get_market(ticker)
        print(f"\nMarket data keys: {market_data.keys()}")
        print(f"\nKey fields:")
        print(f"  yes_bid: {market_data.get('yes_bid')}")
        print(f"  yes_ask: {market_data.get('yes_ask')}")
        print(f"  no_bid: {market_data.get('no_bid')}")
        print(f"  no_ask: {market_data.get('no_ask')}")
        print(f"  last_price: {market_data.get('last_price')}")
        print(f"  volume: {market_data.get('volume')}")
        print(f"  status: {market_data.get('status')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

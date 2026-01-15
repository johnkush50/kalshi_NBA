# System Architecture - Current State

**Last Updated:** January 15, 2026
**Project Phase:** Phase 5 - Frontend UI (Iteration 14 Complete)

---

## 🎯 Project Overview

Full-stack web application for paper trading multiple NBA strategies on Kalshi prediction markets. Integrates live Kalshi orderbook data with comprehensive NBA game data to execute automated trading strategies and track simulated performance.

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│              [Status: Not Started - Phase 4]                 │
│  • Dashboard for monitoring trades and performance           │
│  • Real-time data updates via WebSocket                      │
│  • Strategy configuration UI                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket + REST API
┌──────────────────────┴──────────────────────────────────────┐
│                Backend (Python FastAPI)                      │
│           [Status: Skeleton Complete - Iteration 1]          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Strategy Execution Engine                    │ │
│  │  • Sharp Line Detection                                │ │
│  │  • Momentum Scalping                                   │ │
│  │  • EV Multi-Source                                     │ │
│  │  • Mean Reversion                                      │ │
│  │  • Correlation Play                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Aggregator  │  Order Execution Engine            │ │
│  │  • Kalshi WS      │  • Simulated fills at best bid/ask │ │
│  │  • NBA live data  │  • Position tracking               │ │
│  │  • Betting odds   │  • Real-time P&L calculation       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│              External APIs & Database                        │
│  • Kalshi WebSocket (orderbook streaming)                   │
│  • balldontlie.io REST API (NBA data & odds)                │
│  • Supabase PostgreSQL (data storage)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ What's Implemented

### Documentation (Complete)
**Location:** Root directory  
**Status:** ✅ Complete

- ✅ `kalshi_nba_paper_trading_prd.md` - Full product requirements (68 pages)
- ✅ `kalshi_openapi.yaml` - Kalshi API specification
- ✅ `sports_openapi.yaml` - balldontlie.io API specification
- ✅ `CLAUDE.md` - Development instructions for Claude Code
- ✅ `PROGRESS.md` - Iteration tracking
- ✅ `ARCHITECTURE.md` - This file

**Key Specifications:**
- 11 database tables fully defined
- 5 trading strategies with complete logic
- All API endpoints specified
- Frontend UI mockups included

---

### Backend Infrastructure (Iteration 1)
**Location:** `backend/` directory
**Status:** ✅ Complete

**What's Implemented:**
- ✅ Complete project structure with proper organization
- ✅ FastAPI application with CORS middleware
- ✅ Supabase PostgreSQL schema (11 tables with indexes)
- ✅ Configuration management with Pydantic Settings
- ✅ Environment variables system (.env.example provided)
- ✅ Database migration files
- ✅ Structured logging (JSON format support)
- ✅ Health check endpoints (live, ready, health)
- ✅ Comprehensive Pydantic models for all entities
- ✅ Ticker parser utility with unit tests
- ✅ Skeleton files for all integrations and strategies

**How to Use:**

```python
# Import settings
from backend.config.settings import settings

# Access configuration
print(settings.kalshi_api_key)
print(settings.environment)

# Get Supabase client
from backend.config.supabase import get_supabase_client
client = get_supabase_client()

# Parse Kalshi ticker (⚠️ HAS DATE FORMAT BUG)
from backend.utils.ticker_parser import extract_game_info_from_kalshi_ticker
game_info = extract_game_info_from_kalshi_ticker("kxnbagame-26jan06dalsac")
# Currently returns: {'date': '2006-01-26', ...}  # ❌ Wrong
# Should return: {'date': '2026-01-06', ...}      # ✅ Correct (to be fixed in Iteration 2)

# Run FastAPI application
# uvicorn backend.main:app --reload
```

**Database Tables:**
1. ✅ `games` - Game tracking (UUID, tickers, teams, dates)
2. ✅ `kalshi_markets` - Market metadata (ticker, type, strike)
3. ✅ `orderbook_snapshots` - Real-time bid/ask data
4. ✅ `nba_live_data` - Live game statistics (JSONB)
5. ✅ `betting_odds` - Sportsbook odds aggregation
6. ✅ `strategies` - Strategy configs (JSONB parameters)
7. ✅ `simulated_orders` - Order history
8. ✅ `positions` - Position tracking with P&L
9. ✅ `strategy_performance` - Performance metrics
10. ✅ `risk_limits` - Risk management rules
11. ✅ `system_logs` - Application logs

**Testing:**
- ✅ 15 of 17 unit tests pass for ticker parser (2 fail due to date format bug)
- ✅ Configuration tests for settings
- ✅ All files compile without syntax errors
- ✅ FastAPI application runs successfully
- ✅ Supabase connection works

---

## 📋 Testing Status

### Unit Tests
- **Total:** 17 tests
- **Passing:** 15 (88%)
- **Failing:** 2 (12%)
- **Reason:** Ticker parser date format bug

### Integration Tests
- ✅ FastAPI server starts without errors
- ✅ Health endpoints respond
- ✅ Supabase connection works
- ✅ All database tables accessible
- ✅ API documentation generated

### Manual Testing Completed
- ✅ Virtual environment setup (Python 3.11)
- ✅ Dependency installation (fixed conflicts)
- ✅ Database schema execution in Supabase
- ✅ Environment configuration (.env setup)
- ✅ FastAPI server launch
- ✅ Supabase query test (all 11 tables)

---

## ✅ Kalshi Integration (Iteration 2)

**Location:** `backend/integrations/kalshi/`
**Status:** ✅ Complete

### Architecture Overview

```
backend/integrations/kalshi/
├── __init__.py
├── auth.py          # RSA-PSS signature generation
├── exceptions.py    # Custom exception classes
├── client.py        # REST API client with retry logic
└── websocket.py     # WebSocket client with reconnection
```

### Authentication Flow (RSA-PSS)

Kalshi uses RSA-PSS signatures, NOT HMAC. The flow:

1. Load private key from `.env` (with `\n` → newline conversion)
2. Build message: `{timestamp_ms}{METHOD}{path}{body}`
3. Sign with RSA-PSS (SHA256, MAX_LENGTH salt)
4. Base64 encode signature
5. Include headers: `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-SIGNATURE`, `KALSHI-ACCESS-TIMESTAMP`

### Code Examples

**Testing Authentication:**
```bash
python scripts/test_kalshi_connection.py --test-auth
```

**Listing Games for a Date:**
```python
from backend.integrations.kalshi.client import KalshiClient

async def list_games():
    client = KalshiClient()
    games = await client.get_nba_games_for_date("2026-01-08")
    for game in games:
        print(f"{game['away_team']} @ {game['home_team']}")
```

**Loading a Game via API:**
```bash
curl -X POST http://localhost:8000/api/games/load \
  -H "Content-Type: application/json" \
  -d '{"event_ticker": "KXNBAGAME-26JAN08LALSAC"}'
```

**WebSocket Subscription:**
```python
from backend.integrations.kalshi.websocket import KalshiWebSocketClient

async def stream_orderbook():
    ws = KalshiWebSocketClient()
    await ws.connect()
    await ws.subscribe(["KXNBAGAME-26JAN08LALSAC-Y"], ["ticker", "orderbook_delta"])
    
    async for message in ws.listen():
        if message["type"] == "ticker":
            print(f"Price update: {message['data']}")
```

### API Endpoints

- `GET /api/games/available?date=YYYY-MM-DD` - List available NBA games
- `POST /api/games/load` - Load a game by ticker or date+index
- `GET /api/games/{game_id}` - Get game with markets
- `GET /api/games/` - List all loaded games
- `DELETE /api/games/{game_id}` - Delete a game

---

## ✅ balldontlie.io Integration (Iteration 3)

**Location:** `backend/integrations/balldontlie/`
**Status:** ✅ Complete

### Architecture Overview

```
backend/integrations/balldontlie/
├── __init__.py
├── exceptions.py     # Custom exception classes
└── client.py         # REST API client with retry logic
```

### Authentication

balldontlie.io uses simple API key authentication:
- API key goes in `Authorization` header
- **NO "Bearer" prefix** - just the raw API key
- Rate limiting handled with tenacity retry logic

### API Path Structure

**Important:** NBA endpoints use sport-specific prefixes:
- Teams/Games/Box Scores: `/v1/teams`, `/v1/games`, `/v1/box_scores`
- Odds: `/nba/v2/odds` (note the `/nba` prefix for v2 endpoints)
- Date parameters use array format: `dates[]=2026-01-08`

### Game Matching Flow

```
Kalshi Event Ticker (e.g., "KXNBAGAME-26JAN08DALUTA")
        ↓
    ticker_parser.py
        ↓
{date: "2026-01-08", away: "DAL", home: "UTA"}
        ↓
    balldontlie.io /v1/games?dates[]=2026-01-08
        ↓
    Match by team abbreviations
        ↓
    NBA Game ID stored in database
```

### Code Examples

**Testing Authentication:**
```bash
python scripts/test_balldontlie.py --test-auth
```

**Listing Games for a Date:**
```python
from backend.integrations.balldontlie.client import BallDontLieClient

async def list_games():
    client = BallDontLieClient()
    games = await client.get_games_for_date("2026-01-08")
    for game in games:
        visitor = game["visitor_team"]["abbreviation"]
        home = game["home_team"]["abbreviation"]
        print(f"{visitor} @ {home}")
    await client.close()
```

**Matching Kalshi Game to NBA Game:**
```python
from backend.integrations.balldontlie.client import BallDontLieClient

async def match_game():
    client = BallDontLieClient()
    nba_game = await client.match_kalshi_game("KXNBAGAME-26JAN08DALUTA")
    print(f"NBA Game ID: {nba_game['id']}")
    await client.close()
```

**Fetching Betting Odds:**
```python
async def get_odds():
    client = BallDontLieClient()
    odds = await client.get_odds(date="2026-01-08")
    for item in odds:
        for book in item.get("sportsbooks", []):
            print(f"{book['name']}: {book['odds']}")
    await client.close()
```

### API Endpoints Used

| Endpoint | Purpose |
|----------|----------|
| GET /v1/teams | Get all NBA teams |
| GET /v1/games | Get games by date |
| GET /v1/games/{id} | Get specific game |
| GET /v1/box_scores | Get box scores |
| GET /v1/box_scores/live | Get live box scores |
| GET /v2/odds | Get betting odds |

### Database Helpers

**Location:** `backend/database/helpers.py`

Async helper functions for:
- `create_game()`, `get_game_by_id()`, `update_game()`
- `create_kalshi_market()`, `get_markets_for_game()`
- `store_nba_live_data()`, `get_latest_nba_data()`
- `store_betting_odds()`, `get_latest_odds()`
- `store_orderbook_snapshot()`, `get_latest_orderbook()`

### New API Endpoints

- `POST /api/games/{game_id}/refresh-nba` - Fetch latest NBA data
- `POST /api/games/{game_id}/refresh-odds` - Fetch latest betting odds

---

## ✅ Data Aggregation Layer (Iteration 4)

**Location:** `backend/models/game_state.py`, `backend/utils/odds_calculator.py`, `backend/engine/aggregator.py`, `backend/api/routes/aggregator.py`
**Status:** ✅ Complete

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Aggregator                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Kalshi WS    │  │ NBA Poller   │  │ Odds Poller  │      │
│  │ (real-time)  │  │ (5 seconds)  │  │ (10 seconds) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              GameState Cache                          │  │
│  │  • orderbooks: Dict[ticker, OrderbookState]          │  │
│  │  • nba_state: NBALiveState                           │  │
│  │  • odds: Dict[vendor, OddsState]                     │  │
│  │  • implied_probabilities: Dict[ticker, Decimal]      │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │           Event Subscription System                   │  │
│  │  • on_orderbook_update(callback)                     │  │
│  │  • on_nba_update(callback)                           │  │
│  │  • on_odds_update(callback)                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### GameState Model Documentation

The `GameState` model provides a unified view of all game-related data:

```python
from backend.models.game_state import GameState, OrderbookState, NBALiveState, OddsState

# GameState contains:
# - game_id: str - UUID of the game
# - event_ticker: str - Kalshi event ticker
# - home_team, away_team: str - Team names
# - status: str - 'scheduled', 'live', 'finished'
# - orderbooks: Dict[str, OrderbookState] - Market orderbooks by ticker
# - nba_state: Optional[NBALiveState] - Live NBA game data
# - odds: Dict[str, OddsState] - Betting odds by vendor
# - implied_probabilities: Dict[str, Decimal] - Calculated probabilities
# - last_updated: datetime
```

### DataAggregator Responsibilities

1. **Game State Management** - Maintains in-memory cache of `GameState` objects
2. **Background Polling** - Coordinates NBA data (5s) and odds (10s) polling tasks
3. **WebSocket Integration** - Receives Kalshi orderbook updates in real-time
4. **Event Subscription** - Notifies strategies when data changes
5. **Odds Calculation** - Converts American odds to implied probabilities using `Decimal`

### Background Task Management

```python
from backend.engine.aggregator import DataAggregator

aggregator = DataAggregator()

# Background tasks are managed per-game:
# - NBA polling task: Fetches live box scores every 5 seconds
# - Odds polling task: Fetches betting odds every 10 seconds
# - Tasks automatically stop when game is unloaded or finished

# Lifecycle hooks in FastAPI:
@app.on_event("startup")
async def startup():
    await aggregator.start()  # Logs "Data aggregator started"

@app.on_event("shutdown")
async def shutdown():
    await aggregator.stop()  # Cancels all background tasks
```

### Code Examples

**Loading a Game:**
```python
from backend.engine.aggregator import get_aggregator

aggregator = get_aggregator()

# Load game by ID (fetches from database and starts polling)
game_state = await aggregator.load_game(game_id="uuid-here")

# Or load from date selection
game_state = await aggregator.load_game_by_date(date="2026-01-08", index=0)
```

**Subscribing to Updates:**
```python
from backend.engine.aggregator import get_aggregator, EventType

aggregator = get_aggregator()

# Define callback for orderbook updates
async def on_orderbook_change(game_id: str, state: GameState):
    print(f"Game {game_id} orderbook updated")
    for ticker, ob in state.orderbooks.items():
        print(f"  {ticker}: bid={ob.yes_bid}, ask={ob.yes_ask}")

# Subscribe
aggregator.subscribe(EventType.ORDERBOOK_UPDATE, on_orderbook_change)

# Unsubscribe when done
aggregator.unsubscribe(EventType.ORDERBOOK_UPDATE, on_orderbook_change)
```

**Accessing Unified State:**
```python
from backend.engine.aggregator import get_aggregator

aggregator = get_aggregator()

# Get current state for a game
state = aggregator.get_state(game_id)

if state:
    # Access NBA data
    if state.nba_state:
        print(f"Score: {state.nba_state.home_score} - {state.nba_state.away_score}")
        print(f"Period: {state.nba_state.period}, Time: {state.nba_state.time_remaining}")
    
    # Access orderbooks
    for ticker, ob in state.orderbooks.items():
        print(f"{ticker}: Yes bid/ask = {ob.yes_bid}/{ob.yes_ask}")
    
    # Access odds from multiple sportsbooks
    for vendor, odds in state.odds.items():
        print(f"{vendor}: ML Home={odds.moneyline_home}, Away={odds.moneyline_away}")
    
    # Access calculated implied probabilities
    for ticker, prob in state.implied_probabilities.items():
        print(f"{ticker}: {prob:.2%} implied probability")
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/aggregator/states` | GET | List all active game states |
| `POST /api/aggregator/load/{game_id}` | POST | Load a game into the aggregator |
| `GET /api/aggregator/state/{game_id}` | GET | Get unified state for a game |
| `DELETE /api/aggregator/unload/{game_id}` | DELETE | Stop tracking a game |

### Odds Calculator Utilities

```python
from backend.utils.odds_calculator import (
    american_to_probability,
    probability_to_american,
    calculate_implied_probability,
    calculate_expected_value
)
from decimal import Decimal

# Convert American odds to implied probability
prob = american_to_probability(-150)  # Returns Decimal("0.6")
prob = american_to_probability(+200)  # Returns Decimal("0.333...")

# Calculate EV
ev = calculate_expected_value(
    true_probability=Decimal("0.55"),
    kalshi_price=Decimal("0.48")
)  # Returns positive EV if profitable
```

---

## ✅ Trading Strategies (Iteration 5)

**Location:** `backend/strategies/`, `backend/engine/strategy_engine.py`
**Status:** ✅ Sharp Line Detection Complete

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Strategy Engine                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Strategy Registry                        │  │
│  │  • sharp_line -> SharpLineStrategy                   │  │
│  │  • momentum -> MomentumStrategy (future)             │  │
│  │  • ev_multi -> EVMultiStrategy (future)              │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │           Active Strategies                           │  │
│  │  {strategy_id: BaseStrategy instance}                │  │
│  │  • load_strategy(type, config)                       │  │
│  │  • enable_strategy(id)                               │  │
│  │  • evaluate_game(game_state)                         │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │           Background Evaluation Loop                  │  │
│  │  • Runs every strategy_eval_interval (2 seconds)     │  │
│  │  • Evaluates all enabled strategies on all games     │  │
│  │  • Notifies signal handlers when signals generated   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Base Strategy Class

All strategies inherit from `BaseStrategy`:

```python
from backend.strategies.base import BaseStrategy
from backend.models.game_state import GameState
from backend.models.order import TradeSignal

class MyStrategy(BaseStrategy):
    STRATEGY_NAME = "My Strategy"
    STRATEGY_TYPE = "my_strategy"
    STRATEGY_DESCRIPTION = "Description of my strategy"
    
    def get_default_config(self) -> Dict[str, Any]:
        return {
            "threshold_percent": 5.0,
            "position_size": 10,
            "cooldown_minutes": 5
        }
    
    async def evaluate(self, game_state: GameState) -> List[TradeSignal]:
        # Analyze game_state and return signals
        signals = []
        # ... strategy logic ...
        return signals
```

### Sharp Line Detection Strategy

**Purpose:** Compare Kalshi prices to sportsbook consensus and trade on divergences.

**Configuration:**
```python
{
    "threshold_percent": 5.0,       # Min % divergence to trigger
    "min_sample_sportsbooks": 3,    # Min sportsbooks for valid consensus
    "position_size": 10,            # Contracts per trade
    "cooldown_minutes": 5,          # Minutes between trades on same market
    "min_ev_percent": 2.0,          # Minimum expected value
    "market_types": ["moneyline"],  # Which market types to trade
    "use_kelly_sizing": False,      # Use Kelly criterion
    "kelly_fraction": 0.25          # Fraction of Kelly to use
}
```

**Signal Logic:**
1. Get Kalshi mid-price for market (implied probability)
2. Get consensus probability from sportsbooks
3. Calculate divergence = |kalshi_prob - consensus_prob|
4. If divergence > threshold AND sufficient sources:
   - kalshi_prob < consensus_prob → BUY YES (undervalued)
   - kalshi_prob > consensus_prob → BUY NO (overvalued)
5. Check cooldown period
6. Calculate EV, check minimum
7. Generate TradeSignal

### Code Examples

**Loading a Strategy:**
```python
from backend.engine.strategy_engine import get_strategy_engine

engine = get_strategy_engine()

# Load with custom config
strategy = await engine.load_strategy(
    strategy_type="sharp_line",
    config={
        "threshold_percent": 3.0,
        "min_sample_sportsbooks": 1
    },
    enable=True
)

print(f"Loaded: {strategy.strategy_id}")
```

**Manual Evaluation:**
```python
from backend.engine.aggregator import get_aggregator
from backend.engine.strategy_engine import get_strategy_engine

aggregator = get_aggregator()
engine = get_strategy_engine()

# Get game state
game_state = aggregator.get_game_state(game_id)

# Evaluate all enabled strategies
signals = await engine.evaluate_game(game_state)

for signal in signals:
    print(f"{signal.side.value.upper()} {signal.quantity} {signal.market_ticker}")
    print(f"Reason: {signal.reason}")
```

**Adding a Signal Handler:**
```python
async def on_signal(signal: TradeSignal):
    print(f"New signal: {signal.side} {signal.market_ticker}")
    # Route to order execution engine (future)

engine = get_strategy_engine()
engine.add_signal_handler(on_signal)
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategies/types` | GET | List available strategy types |
| `/api/strategies/` | GET | List loaded strategies |
| `/api/strategies/load` | POST | Load a new strategy instance |
| `/api/strategies/{id}` | GET | Get strategy details |
| `/api/strategies/{id}` | DELETE | Unload a strategy |
| `/api/strategies/{id}/enable` | POST | Enable a strategy |
| `/api/strategies/{id}/disable` | POST | Disable a strategy |
| `/api/strategies/{id}/config` | PUT | Update configuration |
| `/api/strategies/{id}/evaluate` | POST | Manual evaluation on a game |
| `/api/strategies/evaluate-all` | POST | Evaluate all enabled strategies |
| `/api/strategies/{id}/signals` | GET | Get recent signals |

### Test Script

```bash
# List available strategy types
python scripts/test_strategy.py --list-types

# Load and test on a game
python scripts/test_strategy.py --load-and-test --game-id <UUID>

# Run all enabled strategies
python scripts/test_strategy.py --evaluate

# Debug game state
python scripts/test_strategy.py --show-state --game-id <UUID>
```

---

## ✅ Momentum Scalping Strategy (Iteration 6)

**Location:** `backend/strategies/momentum.py`
**Status:** ✅ Complete

### Strategy Description

The Momentum Scalping strategy detects rapid price movements in Kalshi markets and trades in the direction of momentum. The assumption is that significant price moves indicate informed trading or market sentiment shifts.

**Example:**
- Lakers YES was 45¢ 2 minutes ago
- Lakers YES is now 52¢ (7¢ move in 2 minutes)
- Momentum detected → BUY YES (follow the move)

### Price History Tracking

The strategy maintains a rolling window of price observations for each market:

```python
class PricePoint:
    """A single price observation with timestamp."""
    def __init__(self, price: Decimal, timestamp: datetime):
        self.price = price
        self.timestamp = timestamp

# Price history stored as: ticker -> deque of PricePoint
# Uses deque with maxlen=100 for automatic old data removal
```

### Signal Generation Logic

1. **Update Price History** - Record current mid-price with timestamp
2. **Get Historical Price** - Find price from `lookback_seconds` ago
3. **Calculate Change** - `price_change = current - historical` (in cents)
4. **Check Threshold** - If `abs(price_change) >= min_price_change_cents`:
   - `price_change > 0` → BUY YES (price going up)
   - `price_change < 0` → BUY NO (price going down)
5. **Check Spread** - Ensure spread ≤ `max_spread_cents`
6. **Check Cooldown** - Ensure cooldown period passed
7. **Generate Signal** - Create TradeSignal with confidence based on move magnitude

### Configuration Parameters

```python
{
    "lookback_seconds": 120,        # Time window to measure momentum (default: 2 min)
    "min_price_change_cents": 5,    # Minimum price change to trigger (default: 5¢)
    "position_size": 10,            # Contracts per trade (default: 10)
    "cooldown_minutes": 3,          # Time between trades on same market (default: 3)
    "max_spread_cents": 3,          # Maximum acceptable spread (default: 3¢)
    "market_types": ["moneyline", "spread", "total"]  # Which markets to trade
}
```

### Code Examples

**Loading the Strategy:**
```python
from backend.engine.strategy_engine import get_strategy_engine

engine = get_strategy_engine()

strategy = await engine.load_strategy(
    strategy_type="momentum",
    config={
        "lookback_seconds": 60,
        "min_price_change_cents": 3
    },
    enable=True
)
```

**Testing via CLI:**
```bash
# Test momentum strategy (builds price history over time)
python scripts/test_strategy.py --test-momentum --game-id <UUID>
```

### Important Notes

1. **Requires Time to Build History** - First few evaluations will show "no historical price" until enough data is collected
2. **Stable Markets = No Signals** - Strategy only fires when prices actually move significantly
3. **Testing vs Production** - Use lower thresholds for testing (1¢ change, 30s lookback), higher for production (5¢, 120s)
4. **In-Memory History** - Price history is stored per strategy instance; reloading clears history

---

## ✅ EV Multi-Book Arbitrage Strategy (Iteration 7)

**Location:** `backend/strategies/ev_multibook.py`
**Status:** ✅ Complete

### Strategy Description

The EV Multi-Book Arbitrage strategy finds positive expected value opportunities by comparing Kalshi prices against individual sportsbook odds (not just consensus). Unlike Sharp Line which uses consensus, this strategy evaluates each sportsbook individually.

**Example:**
- Kalshi: Lakers YES @ 45¢
- FanDuel: Lakers -150 (60% implied) → EV = +15%
- DraftKings: Lakers -140 (58% implied) → EV = +13%
- BetMGM: Lakers -160 (62% implied) → EV = +17% ← BEST

Trade when multiple sportsbooks show +EV above threshold.

### How It Differs From Sharp Line

| Aspect | Sharp Line | EV Multi-Book |
|--------|------------|---------------|
| Odds comparison | Consensus of all books | Each book individually |
| Signal trigger | Divergence from consensus | Multiple books showing +EV |
| Confidence | Based on divergence % | Based on # agreeing books |
| Best for | Finding mispriced markets | Finding value vs specific books |

### Signal Generation Logic

1. **Get Kalshi Price** - Current ask price for YES and NO sides
2. **For Each Sportsbook:**
   - Get implied probability from American odds
   - Calculate EV for YES side: `(true_prob - kalshi_prob) / kalshi_prob`
   - Calculate EV for NO side similarly
   - Record books showing +EV above threshold
3. **Check Agreement** - Count books showing +EV for each side
4. **Generate Signal** - If `count >= min_sportsbooks_agreeing`:
   - Pick side with more agreeing books
   - Include best book and EV in metadata

### Configuration Parameters

```python
{
    "min_ev_percent": 3.0,           # Minimum EV percentage to consider (default: 3%)
    "min_sportsbooks_agreeing": 2,   # Minimum books showing +EV (default: 2)
    "position_size": 10,             # Contracts per trade (default: 10)
    "cooldown_minutes": 5,           # Cooldown between trades (default: 5)
    "preferred_books": [],           # Empty = use all books
    "market_types": ["moneyline"],   # Market types to evaluate
    "exclude_books": []              # Books to ignore
}
```

### Code Examples

**Loading the Strategy:**
```python
from backend.engine.strategy_engine import get_strategy_engine

engine = get_strategy_engine()

strategy = await engine.load_strategy(
    strategy_type="ev_multibook",
    config={
        "min_ev_percent": 2.0,
        "min_sportsbooks_agreeing": 2
    },
    enable=True
)
```

**Testing via CLI:**
```bash
# Test EV multi-book strategy
python scripts/test_strategy.py --test-ev-multibook --game-id <UUID>
```

### Signal Metadata

Generated signals include rich metadata:
```python
{
    "best_book": "fanduel",
    "best_ev_percent": 15.2,
    "best_implied_prob": 0.60,
    "agreeing_books": 3,
    "all_ev_books": [("fanduel", 15.2, 0.60), ("draftkings", 13.1, 0.58), ...],
    "entry_price": 45.0,
    "is_home_market": True
}
```

### Important Notes

1. **Requires Odds Data** - Strategy needs sportsbook odds in GameState.odds
2. **More Conservative** - Requiring multiple books to agree reduces false signals
3. **Book Selection** - Use `preferred_books` to only trust certain sportsbooks
4. **Different from Sharp Line** - This looks at individual books, not consensus

---

## ✅ Live Mean Reversion Strategy (Iteration 8)

**File:** `backend/strategies/mean_reversion.py`  
**Status:** ✅ Complete

### Strategy Concept

During live NBA games, odds often overreact to scoring runs, foul trouble, or momentum shifts. This strategy detects when odds have moved significantly from their pre-game levels and bets on mean reversion back toward the original odds.

**Example Scenario:**
- Pre-game: Lakers @ 60% to win
- Live (Q2): Lakers down 10, odds drop to 40%
- Strategy detects 20% swing → BUY YES Lakers (expect reversion)

The idea: Short-term game events cause overreaction. Unless fundamentally game-changing (key injury, blowout), odds tend to revert.

### How It Works

1. **Store Pre-Game Prices** - When a game first goes live, store current prices as baseline
2. **Compare to Current** - Calculate swing = current_price - pregame_price
3. **Check Tradeable Range** - Swing must be between min and max thresholds
4. **Bet on Reversion** - If price dropped, BUY YES (expect recovery). If increased, BUY NO.
5. **Time Check** - Only trade when enough game time remains for reversion

### Configuration Parameters

```python
{
    "min_reversion_percent": 15.0,    # Min % swing to trigger (default: 15%)
    "max_reversion_percent": 40.0,    # Max % swing (beyond = real shift)
    "min_time_remaining_pct": 25.0,   # Min % of game remaining
    "position_size": 10,              # Contracts per trade
    "cooldown_minutes": 10,           # Longer cooldown for live trades
    "only_first_half": True,          # Only trade in Q1/Q2 for NBA
    "market_types": ["moneyline"],    # Which markets to trade
    "max_score_deficit": 20           # Don't trade if blowout (>20 pt deficit)
}
```

### Code Examples

**Loading the Strategy:**
```python
from backend.engine.strategy_engine import get_strategy_engine

engine = get_strategy_engine()

strategy = await engine.load_strategy(
    strategy_type="mean_reversion",
    config={
        "min_reversion_percent": 10.0,
        "only_first_half": False
    },
    enable=True
)
```

**Simulating Pre-Game Prices (for testing):**
```python
# Via API endpoint
POST /api/strategies/{strategy_id}/simulate-pregame?game_id=<UUID>
Body: {"KXNBAGAME-26JAN08DALUTA-DAL": 65.0, "KXNBAGAME-26JAN08DALUTA-UTA": 35.0}
```

**Testing via CLI:**
```bash
python scripts/test_strategy.py --test-mean-reversion --game-id <UUID>
```

### Signal Metadata

Generated signals include:
```python
{
    "pregame_price": 60.0,
    "current_price": 45.0,
    "swing_percent": 15.0,
    "swing_direction": "down",
    "entry_price": 46.0,
    "period": 2,
    "score_home": 42,
    "score_away": 52
}
```

### Important Notes

1. **Live Games Only** - Strategy only activates when `game_state.phase == LIVE`
2. **Pre-Game Price Storage** - Prices are stored in memory; lost on server restart
3. **First Half Preferred** - Mean reversion is most reliable early in games
4. **Blowout Protection** - `max_score_deficit` prevents trading when odds shift is legitimate
5. **Testing Mode** - Use `simulate_pregame_prices()` to test without waiting for live games

---

## Cross-Market Correlation Strategy (Iteration 9)

**File:** `backend/strategies/correlation.py`  
**Status:** ✅ Complete

### Strategy Concept

Different market types for the same game should be mathematically related. When one market moves but correlated markets don't adjust, there's an arbitrage opportunity. This strategy exploits pricing inefficiencies between related markets (moneyline, spread, totals).

**Key Correlations:**
- **Moneyline ↔ Spread:** Higher win probability should correlate with larger spread coverage
- **Complementary Markets:** Home YES + Away YES should sum to ~100%
- **Totals:** Over + Under should sum to ~100% (minus vig)

**Example Scenario:**
- Moneyline: Lakers 60% to win
- Spread: Lakers -5.5 @ 52% (implies ~58% moneyline)
- Discrepancy detected → Trade to exploit the gap

### How It Works

**Check 1: Complementary Market Sum**
1. Get moneyline YES prices for both teams
2. Sum them: `home_yes + away_yes`
3. If sum > 105%: Both overvalued → BUY NO on higher priced side
4. If sum < 95%: Both undervalued (unusual, no signal)

**Check 2: Moneyline vs Spread Correlation**
1. Get moneyline implied probability for favorite
2. Estimate expected spread probability: `spread_prob ≈ 50 + (ml_prob - 50) * 0.5`
3. Compare to actual spread price
4. If discrepancy > threshold: Trade the mispriced market

### Configuration Parameters

```python
{
    "min_discrepancy_percent": 5.0,      # Min % discrepancy to trigger
    "complementary_max_sum": 105.0,      # Max sum before overvalued
    "complementary_min_sum": 95.0,       # Min sum before undervalued
    "position_size": 10,                 # Contracts per trade
    "cooldown_minutes": 5,               # Time between trades
    "check_complementary": True,          # Enable home+away sum check
    "check_moneyline_spread": True,       # Enable ML vs spread check
    "prefer_no_on_overvalued": True       # Buy NO when sum > max
}
```

### Code Examples

**Loading the Strategy:**
```python
from backend.engine.strategy_engine import get_strategy_engine

engine = get_strategy_engine()

strategy = await engine.load_strategy(
    strategy_type="correlation",
    config={
        "min_discrepancy_percent": 3.0,
        "complementary_max_sum": 102.0
    },
    enable=True
)
```

**Testing via CLI:**
```bash
python scripts/test_strategy.py --test-correlation --game-id <UUID>
```

### Signal Metadata

**Complementary Market Signal:**
```python
{
    "home_team": "DAL",
    "away_team": "UTA",
    "home_yes_price": 55.0,
    "away_yes_price": 52.0,
    "total_sum": 107.0,
    "excess_percent": 7.0,
    "signal_type": "complementary_overvalued"
}
```

**ML-Spread Correlation Signal:**
```python
{
    "spread_ticker": "KXNBASPREAD-26JAN08DALUTA-DAL7",
    "spread_value": 7,
    "spread_prob": 58.0,
    "expected_spread_prob": 52.5,
    "moneyline_prob": 65.0,
    "favorite_team": "DAL",
    "discrepancy": 5.5,
    "signal_type": "ml_spread_correlation"
}
```

### Important Notes

1. **ML-Spread Model Simplified** - Uses linear approximation: `expected = 50 + (ml - 50) * 0.5`
2. **Vig Consideration** - Complementary markets naturally sum > 100% due to vig
3. **Best Conditions** - Works when one market updates before another (latency arb)
4. **Ticker Parsing** - Spread tickers expected format: `KXNBASPREAD-{EVENT}-{TEAM}{VALUE}`

---

## ✅ Order Execution Engine (Iteration 10)

**Location:** `backend/engine/execution.py`, `backend/api/routes/execution.py`
**Status:** ✅ Complete

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Engine                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Signal Processing                        │  │
│  │  • Receive TradeSignal from strategies               │  │
│  │  • Convert to SimulatedOrder                         │  │
│  │  • Validate against risk limits                      │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │              Order Execution                          │  │
│  │  • Get current ask price from orderbook              │  │
│  │  • Simulate immediate fill                           │  │
│  │  • Store order in database                           │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │              Position Management                      │  │
│  │  • Update position size and avg price                │  │
│  │  • Track cost basis                                  │  │
│  │  • Store position in database                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Order Lifecycle

```
TradeSignal (from strategy)
        ↓
SimulatedOrder (PENDING)
        ↓
    Validation
        ↓
   ┌────┴────┐
   │         │
REJECTED    Get Fill Price
   │         │
   │         ↓
   │      FILLED
   │         │
   └────┬────┘
        ↓
  Store in Database
        ↓
  Update Position
```

### Risk Controls

The execution engine enforces risk limits:

| Control | Default | Description |
|---------|---------|-------------|
| `max_position_size` | 100 | Max contracts per market |
| `max_daily_orders` | 50 | Max orders per day |

### Code Examples

**Executing a Signal:**
```python
from backend.engine.execution import get_execution_engine
from backend.models.order import TradeSignal, OrderSide

engine = get_execution_engine()

signal = TradeSignal(
    strategy_id="my-strategy-uuid",
    strategy_name="Sharp Line",
    market_ticker="KXNBAGAME-26JAN08DALUTA-DAL",
    side=OrderSide.YES,
    quantity=10,
    confidence=0.85,
    reason="Kalshi undervalued by 7%"
)

result = await engine.execute_signal(signal, game_id="game-uuid")

if result.success:
    print(f"Filled @ {result.order.filled_price}¢")
    print(f"Position: {result.new_position.quantity} contracts")
else:
    print(f"Rejected: {result.error}")
```

**Getting Positions:**
```python
engine = get_execution_engine()

# All positions
positions = engine.get_all_positions()

# Open positions only
open_positions = engine.get_open_positions()

# Single position
position = engine.get_position("KXNBAGAME-26JAN08DALUTA-DAL")
```

**Adding Execution Callback:**
```python
async def on_execution(order, position):
    print(f"Order filled: {order.side} {order.quantity} @ {order.filled_price}")

engine = get_execution_engine()
engine.add_execution_callback(on_execution)
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/execution/stats` | GET | Get execution engine statistics |
| `/api/execution/positions` | GET | Get all positions |
| `/api/execution/positions/open` | GET | Get open positions only |
| `/api/execution/orders` | GET | Get recent orders |
| `/api/execution/orders/game/{game_id}` | GET | Get orders for a game |
| `/api/execution/orders/strategy/{strategy_id}` | GET | Get orders for a strategy |
| `/api/execution/execute/manual` | POST | Place a manual order |
| `/api/execution/execute/signal` | POST | Execute a signal manually |
| `/api/execution/execute/strategy/{strategy_id}` | POST | Run strategy and execute signals |

### Test Script

```bash
# Get execution stats
python scripts/test_execution.py --stats

# Place manual order
python scripts/test_execution.py --manual-order \
    --game-id <UUID> \
    --market KXNBAGAME-26JAN08DALUTA-DAL \
    --side yes \
    --quantity 10

# View recent orders
python scripts/test_execution.py --view-orders

# View positions
python scripts/test_execution.py --view-positions

# Execute strategy signals
python scripts/test_execution.py --execute-strategy \
    --strategy-id <UUID> \
    --game-id <UUID>
```

### Important Notes

1. **Paper Trading Only** - All orders are simulated, no real money
2. **Immediate Fill** - Orders fill instantly at current ask price
3. **In-Memory Positions** - Positions are tracked in memory and synced to DB
4. **Daily Reset** - Order counter resets at UTC midnight
5. **Database Tables** - Uses `simulated_orders` and `positions` tables

---

## ✅ P&L Tracking & Performance Metrics (Iteration 11)

**Location:** `backend/utils/pnl_calculator.py`, `backend/engine/execution.py`, `backend/api/routes/execution.py`
**Status:** ✅ Complete

### P&L Calculation Methodology

Kalshi contracts are binary options with a fixed payout structure:
- **YES contracts** pay $1.00 (100¢) if outcome is YES, $0 if NO
- **NO contracts** pay $1.00 (100¢) if outcome is NO, $0 if YES

**Example:**
- Buy YES at 40¢ → If YES wins: +60¢ profit | If NO wins: -40¢ loss
- Buy NO at 40¢ → If NO wins: +60¢ profit | If YES wins: -40¢ loss

### Unrealized vs Realized P&L

| Type | Description | Formula |
|------|-------------|---------|
| **Unrealized P&L** | Paper profit/loss on open positions | `(current_price - avg_entry_price) * quantity` |
| **Realized P&L** | Locked-in profit/loss from closed positions | `(exit_price - entry_price) * quantity * direction` |
| **Settlement P&L** | P&L at contract expiry | Position value at settlement (0 or 100¢) minus cost basis |

### Performance Metrics Tracked

1. **Portfolio Metrics:**
   - Total cost basis
   - Total unrealized P&L
   - Total realized P&L
   - Combined total P&L

2. **Order Statistics:**
   - Total orders placed
   - Fill rate percentage
   - Average fill price
   - Unique markets traded

3. **Win Rate Metrics (for settled positions):**
   - Winning trades count
   - Losing trades count
   - Win rate percentage
   - Average win/loss size
   - Profit factor

### Code Examples

**Getting Portfolio P&L:**
```python
from backend.engine.execution import get_execution_engine

engine = get_execution_engine()
summary = engine.get_portfolio_summary()

print(f"Open positions: {summary['open_positions']}")
print(f"Total P&L: {summary['total_pnl']:.1f}¢")
```

**Refreshing Unrealized P&L:**
```python
engine = get_execution_engine()
portfolio = await engine.update_unrealized_pnl()

print(f"Updated {portfolio['position_count']} positions")
print(f"Total unrealized: {portfolio['total_unrealized_pnl']:.1f}¢")
```

**Closing a Position:**
```python
from decimal import Decimal

engine = get_execution_engine()
position = await engine.close_position(
    market_ticker="KXNBAGAME-26JAN09MILLAL-MIL",
    exit_price=Decimal("55")  # Optional, uses market bid if None
)

print(f"Realized P&L: {position.realized_pnl:.1f}¢")
```

**Settling at Contract Expiry:**
```python
engine = get_execution_engine()

# YES won the market
position = await engine.settle_position(
    market_ticker="KXNBAGAME-26JAN09MILLAL-MIL",
    outcome=True  # True = YES won, False = NO won
)

print(f"Settlement P&L: {position.realized_pnl:.1f}¢")
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/execution/pnl` | GET | Get portfolio P&L summary |
| `/api/execution/pnl/refresh` | POST | Refresh unrealized P&L from market prices |
| `/api/execution/positions/{ticker}/close` | POST | Close a position at market or specified price |
| `/api/execution/positions/{ticker}/settle` | POST | Settle a position at contract expiry |
| `/api/execution/performance` | GET | Get overall trading performance metrics |
| `/api/execution/performance/strategy/{id}` | GET | Get performance for a specific strategy |

### Test Script

```bash
# Get portfolio P&L summary
python scripts/test_execution.py --pnl

# Refresh P&L from current market prices
python scripts/test_execution.py --refresh-pnl

# Get trading performance metrics
python scripts/test_execution.py --performance

# Close a position
python scripts/test_execution.py --close-position KXNBAGAME-26JAN09MILLAL-MIL

# Close at specific exit price
python scripts/test_execution.py --close-position KXNBAGAME-26JAN09MILLAL-MIL --exit-price 55
```

### Important Notes

1. **Unrealized P&L Updates** - Call `/pnl/refresh` periodically to update unrealized P&L as market prices change
2. **Settlement** - Use `settle_position` when a market reaches expiry to lock in final P&L
3. **Position Closing** - Use `close_position` to exit before settlement at current market bid
4. **Decimal Precision** - All P&L calculations use `Decimal` to avoid floating point errors

---

## ✅ Risk Management System (Iteration 12)

**Location:** `backend/engine/risk_manager.py`, `backend/api/routes/risk.py`
**Status:** ✅ Complete

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Risk Manager                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Risk Checks                              │  │
│  │  • Position limits (per market, game, total)         │  │
│  │  • Loss limits (daily, weekly, per-trade)            │  │
│  │  • Exposure limits (total, per-game, per-strategy)   │  │
│  │  • Trading limits (orders per hour/day, cooldown)    │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │              Order Flow                               │  │
│  │  Signal → Risk Check → Approved/Rejected → Execution │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Tracking                                 │  │
│  │  • Daily/weekly loss accumulation                    │  │
│  │  • Consecutive loss streak detection                 │  │
│  │  • Auto cooldown after loss streak                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Risk Limit Types

| Limit Type | Default | Description |
|------------|---------|-------------|
| `max_contracts_per_market` | 100 | Max contracts in single market |
| `max_contracts_per_game` | 200 | Max contracts across all markets for one game |
| `max_total_contracts` | 500 | Max total open contracts |
| `max_daily_loss` | 1000¢ | Daily loss limit ($10) |
| `max_weekly_loss` | 5000¢ | Weekly loss limit ($50) |
| `max_per_trade_risk` | 500¢ | Maximum risk per trade ($5) |
| `max_total_exposure` | 10000¢ | Maximum total capital at risk ($100) |
| `max_exposure_per_game` | 2000¢ | Maximum exposure per game ($20) |
| `max_exposure_per_strategy` | 3000¢ | Maximum exposure per strategy ($30) |
| `max_orders_per_day` | 50 | Maximum orders per day |
| `max_orders_per_hour` | 20 | Maximum orders per hour |
| `loss_streak_cooldown` | 3 | Consecutive losses before 5-min pause |

### Loss Streak Cooldown

After N consecutive losing trades (default: 3), trading pauses for 5 minutes:

```
Trade 1: Loss → streak = 1
Trade 2: Loss → streak = 2  
Trade 3: Loss → streak = 3 → COOLDOWN TRIGGERED (5 min pause)
Trade 4: Win → streak = 0 (cooldown ends, trading resumes)
```

### Code Examples

**Checking an Order:**
```python
from backend.engine.risk_manager import get_risk_manager

risk_manager = get_risk_manager()
result = risk_manager.check_order(order, current_positions)

if result.approved:
    # Proceed with execution
else:
    print(f"Rejected: {result.reason}")
    print(f"Limit: {result.limit_type}, Current: {result.current_value}, Max: {result.limit_value}")
```

**Recording Order Execution:**
```python
risk_manager = get_risk_manager()
risk_manager.record_order(order, fill_price)
```

**Recording P&L:**
```python
risk_manager = get_risk_manager()
risk_manager.record_pnl(realized_pnl)  # Triggers cooldown if loss streak
```

**Adjusting Limits:**
```python
from backend.engine.risk_manager import get_risk_manager, RiskLimitType

risk_manager = get_risk_manager()
risk_manager.set_limit(RiskLimitType.MAX_DAILY_LOSS, 2000)  # Increase to $20
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/risk/status` | GET | Get current risk status (losses, orders, cooldown) |
| `/api/risk/limits` | GET | Get all risk limit values |
| `/api/risk/limits` | PUT | Set a specific risk limit |
| `/api/risk/limits/bulk` | PUT | Set multiple limits at once |
| `/api/risk/enable` | POST | Enable risk management |
| `/api/risk/disable` | POST | Disable risk management (WARNING!) |
| `/api/risk/reset` | POST | Reset all tracking counters |
| `/api/risk/check` | GET | Check if hypothetical order would pass |

### Test Script

```bash
# Get risk status
python scripts/test_risk.py --status

# View all limits
python scripts/test_risk.py --limits

# Set a limit
python scripts/test_risk.py --set-limit max_daily_loss 2000

# Check hypothetical order
python scripts/test_risk.py --check --game-id <UUID> --market <TICKER> --side yes --quantity 10

# Enable/disable risk management
python scripts/test_risk.py --enable
python scripts/test_risk.py --disable

# Reset counters
python scripts/test_risk.py --reset
```

### Integration with Execution Engine

Risk checks are automatically integrated into the execution flow:

```
TradeSignal
    ↓
ExecutionEngine.execute_signal()
    ↓
RiskManager.check_order()  ← RISK CHECK HERE
    ↓
┌────┴────┐
│         │
REJECTED  APPROVED
│         │
│         ↓
│     Execute Order
│         │
│         ↓
│     RiskManager.record_order()  ← TRACKING HERE
└─────────┘
```

### Important Notes

1. **Risk checks run BEFORE validation** - A rejected order never reaches the market
2. **Daily/weekly resets automatic** - Daily at midnight UTC, weekly on Monday
3. **Exposure uses worst-case** - Assumes 100¢ per contract for conservative limits
4. **Disable with caution** - Removes all protections when disabled
5. **Cooldown non-negotiable** - Cannot trade during loss streak cooldown

---

## ✅ Frontend Dashboard (Iteration 14)

**Location:** `frontend/`
**Status:** ✅ Static UI Complete (Awaiting Backend Integration)

### Architecture Overview

```
frontend/
├── src/
│   ├── main.tsx                      # Application entry point
│   ├── App.tsx                       # Router setup (React Router v6)
│   ├── index.css                     # Global styles + Tailwind
│   ├── data/
│   │   └── mockData.ts               # All hardcoded mock data
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx            # Main layout wrapper
│   │   │   ├── Header.tsx            # Top bar with status/stats
│   │   │   └── Sidebar.tsx           # Navigation menu
│   │   └── ui/
│   │       ├── Panel.tsx             # Card container with neon border
│   │       ├── Button.tsx            # Button with variants
│   │       └── Badge.tsx             # Status badges
│   └── pages/
│       ├── GamesPage.tsx             # Game management (/)
│       ├── StrategiesPage.tsx        # Strategy control (/strategies)
│       ├── TradingPage.tsx           # Positions & orders (/trading)
│       ├── PnLPage.tsx               # Portfolio P&L (/pnl)
│       └── RiskPage.tsx              # Risk management (/risk)
├── public/
│   └── vite.svg                      # Favicon
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── README.md
└── FRONTEND_API_INTEGRATION.md       # Backend integration guide
```

### Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **Icons:** Lucide React
- **State Management:** Zustand (to be added)

### Design System: Cyberpunk Trading Terminal

**Color Palette:**
```css
--terminal-bg: #0a0e17;      /* Deep space black */
--terminal-surface: #111827;  /* Panel background */
--neon-cyan: #00f0ff;         /* Primary accent */
--neon-green: #00ff88;        /* Profit/success */
--neon-red: #ff3366;          /* Loss/danger */
--neon-yellow: #ffcc00;       /* Warning */
```

**Typography:**
- Display: `Orbitron` - Geometric, futuristic headers
- Data: `JetBrains Mono` - Crisp monospace for numbers
- UI: `Outfit` - Clean geometric sans for navigation

**Effects:**
- Neon glow borders on focused elements
- Subtle grid pattern background
- Pulsing indicators for live data
- Color-coded P&L (green/red)

### Page Structure

#### Games Page (`/`)
- Active games list with expandable market tables
- Browse available games by date
- Place orders (Buy Yes/No buttons)
- Consensus odds from sportsbooks

#### Strategies Page (`/strategies`)
- Strategy cards with enable/disable toggle
- Expandable JSON configuration
- Live signals feed with confidence scores

#### Trading Page (`/trading`)
- Open positions table with unrealized P&L
- Order history with status badges
- Close position buttons

#### P&L Page (`/pnl`)
- Summary cards (Total, Unrealized, Realized P&L)
- Win rate and profit factor metrics
- Position breakdown table

#### Risk Page (`/risk`)
- Risk enabled/disabled toggle
- Progress bars for limit usage
- Loss streak counter
- All 12 risk limits configuration

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Integration Guide

See `frontend/FRONTEND_API_INTEGRATION.md` for:
- API endpoint mapping by page
- WebSocket channel subscriptions
- Zustand store structure
- API client setup code

### Key Components

1. **Header**
   - Connection status indicators (API, WS, Kalshi)
   - Total P&L with color coding
   - Position count, orders today

2. **Sidebar**
   - Navigation links with active state
   - Icons and descriptions

3. **Panel**
   - Reusable card container
   - Neon border variants
   - Corner accent decorations

4. **Button**
   - Variants: primary, secondary, success, danger, ghost
   - Sizes: sm, md, lg

5. **Badge**
   - Variants: default, success, danger, warning, info
   - Optional pulse animation

### Mock Data Structure

All mock data is centralized in `src/data/mockData.ts`:

```typescript
// Games
activeGames: ActiveGame[]      // Currently loaded games
availableGames: AvailableGame[] // Games to browse/load

// Strategies
strategies: Strategy[]         // Loaded strategy instances
recentSignals: Signal[]        // Trading signals

// Trading
openPositions: Position[]      // Current positions
orderHistory: Order[]          // Order log

// P&L
pnlSummary: PnLSummary        // Portfolio totals

// Risk
riskStatus: RiskStatus        // Current risk state
riskLimits: RiskLimit[]       // All 12 limits
```

4. **SignalsLog**
   - Timestamp
   - Strategy name
   - Market ticker
   - Signal side and quantity
   - Confidence score
   - Execution status

5. **PnLSummary**
   - Total cost basis
   - Unrealized P&L
   - Realized P&L
   - Total P&L
   - Win rate

6. **RiskStatus**
   - Daily loss limit usage
   - Position limit usage
   - Orders today count
   - Loss streak status
   - Cooldown indicator

### API Integration (Planned)

```typescript
// API client setup
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Example API calls
const fetchStrategies = () => fetch(`${API_BASE}/api/strategies/`);
const fetchPositions = () => fetch(`${API_BASE}/api/execution/positions/open`);
const fetchPnL = () => fetch(`${API_BASE}/api/execution/pnl`);
const fetchRiskStatus = () => fetch(`${API_BASE}/api/risk/status`);
```

### WebSocket Integration (Planned)

```typescript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws?channels=all');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'orderbook_update':
      // Update market prices
      break;
    case 'signal':
      // Add new signal to log
      break;
    case 'order':
      // Update positions
      break;
    case 'pnl_update':
      // Refresh P&L
      break;
  }
};
```

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## 🔌 Complete API Reference

### Games & Aggregator

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/aggregator/states` | GET | List all active game states |
| `/api/aggregator/state/{game_id}` | GET | Get unified state for a specific game |
| `/api/games/available?date=YYYY-MM-DD` | GET | List available NBA games for a date |
| `/api/aggregator/load/{game_id}` | POST | Load a game into the aggregator |
| `/api/aggregator/unload/{game_id}` | POST | Stop tracking a game |

### Strategies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategies/types` | GET | List available strategy types |
| `/api/strategies/` | GET | List all loaded strategies |
| `/api/strategies/load` | POST | Load a new strategy instance |
| `/api/strategies/{id}/enable` | POST | Enable a strategy |
| `/api/strategies/{id}/disable` | POST | Disable a strategy |

### Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/execution/stats` | GET | Get execution engine statistics |
| `/api/execution/orders` | GET | Get recent orders |
| `/api/execution/positions` | GET | Get all positions |
| `/api/execution/positions/open` | GET | Get open positions only |
| `/api/execution/execute/manual` | POST | Place a manual order |

### P&L

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/execution/pnl` | GET | Get portfolio P&L summary |
| `/api/execution/pnl/refresh` | POST | Refresh unrealized P&L from market prices |
| `/api/execution/positions/{ticker}/close` | POST | Close a position |
| `/api/execution/performance` | GET | Get trading performance metrics |

### Risk Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/risk/status` | GET | Get current risk status |
| `/api/risk/limits` | GET | Get all risk limit values |
| `/api/risk/limits` | PUT | Set a specific risk limit |
| `/api/risk/enable` | POST | Enable risk management |
| `/api/risk/disable` | POST | Disable risk management |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws?channels=all` | Real-time updates for all channels |

**Available WebSocket Channels:**
- `orderbook` - Market price updates
- `nba` - NBA game score updates
- `signals` - Trading signal notifications
- `orders` - Order execution updates
- `positions` - Position changes

---

## ❌ Not Yet Implemented

### Backend Infrastructure
**Status:** ✅ Complete (Iteration 1)

### Kalshi API Integration
**Status:** ✅ Complete (Iteration 2)

### API Integrations Remaining
**Priority:** High  
**Status:** ✅ Complete

- ✅ Kalshi REST API client
- ✅ Kalshi WebSocket connection
- ✅ Orderbook processing
- ✅ balldontlie.io REST API client
- ✅ NBA live data polling
- ✅ Betting odds fetching
- ✅ Auto game matching logic

### Data Aggregation Layer
**Priority:** High  
**Status:** ✅ Complete (Iteration 4)

- ✅ Unified GameState model
- ✅ Odds calculation utilities (Decimal-based)
- ✅ DataAggregator with background polling
- ✅ WebSocket integration
- ✅ Event subscription system
- ✅ Aggregator API endpoints

### Trading Engine
**Priority:** High  
**Status:** ✅ Complete (Iteration 12)

- ✅ Strategy base class
- ✅ Sharp Line Detection strategy
- ✅ Strategy execution engine
- ✅ Momentum Scalping strategy
- ✅ EV Multi-Book Arbitrage strategy
- ✅ Mean Reversion strategy
- ✅ Cross-Market Correlation strategy
- ✅ Order execution simulator
- ✅ Position manager
- ✅ P&L calculator
- ✅ Risk management system

### Frontend
**Priority:** Medium
**Status:** Partially Complete (Static UI)

- ✅ Next.js application
- ✅ Dashboard UI (static)
- ✅ Strategy control cards (static)
- ❌ Live market data table
- ✅ Position tracking table (static)
- ❌ Performance charts
- ✅ Trade log viewer (static)
- ❌ WebSocket client integration
- ❌ API client integration
- ❌ State management (Zustand)

### Testing & Deployment
**Priority:** Low  
**Next Up:** Phase 5

- ❌ Unit tests
- ❌ Integration tests
- ❌ Error handling
- ❌ Deployment scripts

---

## 📁 Planned Project Structure

```
kalshi_nba_trading/
├── backend/                         [NOT CREATED]
│   ├── main.py                      # FastAPI entry point
│   ├── config/
│   │   ├── settings.py              # Environment config
│   │   └── supabase.py              # DB connection
│   ├── database/
│   │   ├── schema.sql               # Database schema
│   │   └── migrations/
│   ├── models/                      # Pydantic models
│   │   ├── game.py
│   │   ├── market.py
│   │   ├── strategy.py
│   │   └── order.py
│   ├── api/                         # REST endpoints
│   │   ├── routes/
│   │   │   ├── games.py
│   │   │   ├── strategies.py
│   │   │   └── trading.py
│   │   └── websocket.py             # WS server
│   ├── integrations/                # External APIs
│   │   ├── kalshi/
│   │   │   ├── client.py
│   │   │   └── websocket.py
│   │   └── balldontlie/
│   │       └── client.py
│   ├── strategies/                  # Trading strategies
│   │   ├── base.py
│   │   ├── sharp_line.py
│   │   ├── momentum.py
│   │   ├── ev_multi.py
│   │   ├── mean_reversion.py
│   │   └── correlation.py
│   ├── engine/                      # Execution engine
│   │   ├── executor.py
│   │   ├── position_manager.py
│   │   └── pnl_calculator.py
│   └── utils/
│       ├── logger.py
│       └── ticker_parser.py
├── frontend/                        [NOT CREATED]
│   └── [Next.js app structure]
├── tests/                           [NOT CREATED]
├── docs/                            ✅ [COMPLETE]
│   ├── kalshi_nba_paper_trading_prd.md
│   ├── kalshi_openapi.yaml
│   └── sports_openapi.yaml
├── .env                             [NOT CREATED]
├── .env.example                     [NOT CREATED]
├── requirements.txt                 [NOT CREATED]
├── README.md                        [NOT CREATED]
├── CLAUDE.md                        ✅ [COMPLETE]
├── PROGRESS.md                      ✅ [COMPLETE]
└── ARCHITECTURE.md                  ✅ [COMPLETE - This file]
```

---

## 🗄️ Database Schema (Planned)

### Tables to Implement

1. **games** - Core game tracking
   - Stores game metadata, team info, status
   - Links Kalshi event to NBA game

2. **kalshi_markets** - Kalshi market metadata
   - Tracks all markets for a game (moneyline, spreads, totals)
   - References games table

3. **orderbook_snapshots** - Real-time market data
   - Stores bid/ask prices from Kalshi WebSocket
   - High-volume table (5-second intervals)

4. **nba_live_data** - Live NBA game stats
   - Stores box scores, scoring pace, period info
   - Updated every 5 seconds during live games

5. **betting_odds** - Sportsbook odds
   - Aggregates odds from multiple books
   - Used for strategy calculations

6. **strategies** - Strategy configurations
   - Stores strategy settings and parameters
   - Enable/disable status

7. **simulated_orders** - Order history
   - All simulated trades executed
   - Links to strategy and position

8. **positions** - Open/closed positions
   - Tracks current holdings
   - Real-time P&L calculation

9. **strategy_performance** - Performance metrics
   - Win rate, Sharpe ratio, total P&L
   - Time-series data

10. **risk_limits** - Risk management rules
    - Position size limits
    - Drawdown limits

11. **system_logs** - Application logs
    - Structured logging for debugging

**All tables include:**
- Proper indexes for performance
- Foreign key relationships
- Timestamps (created_at, updated_at)

---

## 🔌 API Integration Patterns

### Kalshi Integration (IMPLEMENTED ✅)

**Authentication (RSA-PSS):**
```python
from backend.integrations.kalshi.auth import KalshiAuth
from backend.config.settings import settings, get_kalshi_private_key

# Auth is handled automatically by KalshiClient
auth = KalshiAuth(settings.kalshi_api_key, get_kalshi_private_key())
headers = auth.get_auth_headers("GET", "/trade-api/v2/exchange/status")
```

**Game Selection Flow (NEW):**
```python
from backend.integrations.kalshi.client import KalshiClient

client = KalshiClient()

# Step 1: User provides a date
games = await client.get_nba_games_for_date("2026-01-08")
# Returns list of games with all market types

# Step 2: User selects a game
game = games[0]  # LAL @ SAC
event_ticker = game["event_ticker"]  # KXNBAGAME-26JAN08LALSAC

# Step 3: Load full game with all markets
event = await client.get_event(event_ticker, with_nested_markets=True)
```

**WebSocket for Real-Time Data:**
```python
from backend.integrations.kalshi.websocket import KalshiWebSocketClient

ws = KalshiWebSocketClient()
await ws.connect()  # Auth headers included automatically
await ws.subscribe(["KXNBAGAME-26JAN08LALSAC-Y"], ["ticker", "orderbook_delta"])

async for message in ws.listen():
    if message["type"] == "orderbook_delta":
        # Orderbook state is tracked automatically
        orderbook = ws.get_orderbook("KXNBAGAME-26JAN08LALSAC-Y")
```

### balldontlie.io Integration (Planned)

**Auto-Matching Games:**
```python
def extract_game_info(ticker: str):
    # "kxnbagame-26jan06dalsac" →
    # date: 2026-01-06, away: DAL, home: SAC
    pass

async def find_nba_game(date, away, home):
    games = await bdl_client.get(
        "/nba/v1/games",
        params={"dates[]": [date]}
    )
    # Match teams and return game_id
```

**Live Data Polling:**
```python
while game_is_live:
    # Every 5 seconds
    box_scores = await bdl_client.get("/nba/v1/box_scores/live")
    odds = await bdl_client.get("/nba/v2/odds", params={...})
    
    await store_data(box_scores, odds)
    await evaluate_strategies()
```

---

## 🎮 Trading Strategy Architecture (Planned)

### Base Strategy Class
```python
class BaseStrategy:
    def __init__(self, config: dict):
        self.config = config
        self.is_enabled = False
    
    async def evaluate(
        self, 
        market_data: dict, 
        nba_data: dict,
        odds_data: dict
    ) -> Optional[TradeSignal]:
        # Implement in subclass
        pass
    
    async def execute_trade(self, signal: TradeSignal):
        # Common execution logic
        pass
```

### Strategy 1: Sharp Line Detection
**Logic:** Compare Kalshi price to aggregated sportsbook odds
**Trigger:** Divergence > 5% (configurable)
**Example:** Kalshi @ 45¢, Sportsbooks @ 60% implied → BUY

### Strategy 2: Momentum Scalping
**Logic:** Detect scoring runs, exploit price lag
**Trigger:** 8+ point run in 2 minutes, price hasn't adjusted
**Example:** Team goes on 12-0 run → BUY spread

### Strategy 3: EV Multi-Source
**Logic:** Aggregate multiple sportsbooks, find +EV
**Trigger:** Expected value > 3%
**Example:** True prob 55%, Kalshi @ 48¢ → BUY

### Strategy 4: Mean Reversion
**Logic:** When scoring pace deviates significantly
**Trigger:** Projected total > 15% above opening
**Example:** Pace for 280, opened 220 → BET UNDER

### Strategy 5: Correlation Play
**Logic:** Mispriced spread relationships
**Trigger:** P(spread -4.5) < P(spread -6.5)
**Example:** Adjacent spreads inverted → Arbitrage

---

## 🔧 Technology Decisions

### Why Supabase?
- Real-time subscriptions built-in
- PostgreSQL with excellent Python support
- Row Level Security for data protection
- Easy hosting and management

### Why FastAPI?
- Native async/await support (critical for WebSockets)
- Automatic OpenAPI documentation
- Type validation with Pydantic
- High performance

### Why Next.js?
- Server-side rendering for SEO
- App Router for modern patterns
- Great DX with hot reload
- Easy deployment to Vercel

### Why WebSockets?
- Real-time orderbook updates (<1s latency)
- Push updates to frontend
- More efficient than polling

---

## 🎯 Key Implementation Challenges

### Challenge 1: WebSocket Reliability
**Issue:** Kalshi WebSocket may disconnect
**Solution:** Exponential backoff reconnection logic

### Challenge 2: Data Synchronization
**Issue:** Multiple data sources (Kalshi, NBA, odds)
**Solution:** Central aggregator with timestamp alignment

### Challenge 3: Real-Time P&L
**Issue:** Need to calculate P&L as prices change
**Solution:** In-memory price cache + 5-second update loop

### Challenge 4: Strategy Coordination
**Issue:** Multiple strategies trading same markets
**Solution:** Event-driven architecture, strategies subscribe to data updates

---

## 📊 Performance Requirements

### Data Update Frequencies
- Kalshi orderbook: Real-time via WebSocket
- NBA box scores: Every 5 seconds (live games)
- Betting odds: Every 10 seconds
- P&L calculation: Every 5 seconds
- Frontend updates: Real-time via WebSocket

### Latency Targets
- Order execution: <500ms
- Strategy evaluation: <200ms per strategy
- WebSocket message processing: <100ms
- Frontend data display: <1s from source update

---

## 🔐 Security & Configuration

### Environment Variables Required
```bash
KALSHI_API_KEY=xxx
KALSHI_API_SECRET=xxx
BALLDONTLIE_API_KEY=xxx
SUPABASE_URL=xxx
SUPABASE_SERVICE_KEY=xxx
REDIS_URL=redis://localhost:6379
```

### Security Measures
- API keys in environment variables only
- Supabase Row Level Security enabled
- Rate limiting on API endpoints
- Input validation on all user data

---

## 📈 Monitoring & Observability (Planned)

### Metrics to Track
- WebSocket connection uptime
- API response times
- Strategy execution frequency
- Trade success rate
- Database query performance

### Logging Strategy
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized logging (future: send to Datadog/LogStash)

---

## 🐛 Known Issues

### 1. Ticker Parser Date Format (Priority: FIXED ✅)
**Component:** `backend/utils/ticker_parser.py`
**Description:** Date parsing logic interpreted format incorrectly
**Root Cause:** Parser treated '26jan06' as DDmmmYY instead of YYmmmDD
**Resolution:** ✅ Fixed in Iteration 2 - Now correctly parses YYmmmDD format
**Status:** All 17 unit tests pass

### 2. Dependency Versions (Priority: FIXED ✅)
**Component:** `requirements.txt`
**Description:** Initial dependency versions had conflicts
**Resolution:** ✅ Updated to working versions
**Current Versions:**
- supabase==2.27.1
- httpx==0.28.1
- websockets==15.0.1
- cryptography==41.0.0 (added for RSA-PSS)
- All conflicts resolved

### 3. WebSocket URL (Priority: FIXED ✅)
**Component:** `backend/config/settings.py`
**Description:** Wrong WebSocket URL was configured
**Resolution:** ✅ Fixed to `wss://api.elections.kalshi.com/trade-api/ws/v2`

---

## 💡 Architectural Decisions Log

### Decision 1: Supabase for Database
**Date:** [Today]  
**Reason:** Need real-time capabilities, PostgreSQL features, easy setup  
**Alternative Considered:** Self-hosted PostgreSQL  
**Outcome:** Going with Supabase for speed

### Decision 2: FastAPI over Flask/Django
**Date:** [Today]  
**Reason:** Native async support critical for WebSocket performance  
**Alternative Considered:** Flask + gevent, Django Channels  
**Outcome:** FastAPI chosen for best async story

### Decision 3: Simulated Execution at Best Bid/Ask
**Date:** [Today]  
**Reason:** Simplicity, reasonable approximation  
**Alternative Considered:** Limit orders with fill simulation  
**Outcome:** Start simple, can add complexity later

---

## 🚀 Next Steps

### Immediate (Iteration 1):
1. Create Python backend structure
2. Implement Supabase schema
3. Setup FastAPI skeleton
4. Configure environment variables

### Short-term (Iterations 2-5):
1. Build Kalshi integration
2. Build balldontlie.io integration
3. Implement trading strategies
4. Build execution engine

### Medium-term (Phase 4):
1. Create Next.js frontend
2. Build dashboard UI
3. Integrate WebSocket client

---

*This document will be updated after each iteration to reflect the current system state.*

**Last Updated:** [Today's Date]  
**Next Update:** After Iteration 1 completes

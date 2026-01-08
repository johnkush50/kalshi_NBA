# Kalshi NBA Paper Trading Application - Product Requirements Document

## 1. Executive Summary

Build a full-stack web application for paper trading NBA prediction markets on Kalshi using live market data and comprehensive NBA statistics. The system will execute multiple configurable trading strategies simultaneously, track their performance separately, and provide real-time monitoring of positions and P&L.

### Core Capabilities
- Real-time Kalshi orderbook monitoring via websocket
- Live NBA game data and betting odds integration
- Multiple concurrent trading strategies with individual performance tracking
- Simulated order execution at best bid/ask
- Comprehensive dashboard for monitoring and control

---

## 2. Technical Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **WebSocket**: python-socketio / websockets
- **Task Queue**: Celery with Redis (for async data processing)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: Zustand
- **Real-time**: Socket.io client
- **Charts**: Recharts

### Infrastructure
- **Hosting**: Localhost (initial), Vercel (future frontend), self-hosted backend
- **Database**: Supabase cloud
- **Cache**: Redis

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │  Dashboard   │   Strategy   │   Performance Analytics  │ │
│  │   Monitor    │   Controls   │       & Charts          │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────┴────────────────────────────────────┐
│                   Backend (FastAPI + Python)                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Strategy Execution Engine                   │  │
│  │  ┌──────────────┬──────────────┬──────────────────┐  │  │
│  │  │  Strategy 1  │  Strategy 2  │  Strategy 3-5    │  │  │
│  │  │  Sharp Line  │  Momentum    │  EV/Reversion/   │  │  │
│  │  │  Detection   │  Scalping    │  Correlation     │  │  │
│  │  └──────────────┴──────────────┴──────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────┬───────────────────────────────┐  │
│  │   Data Aggregator    │    Order Execution Engine     │  │
│  │  - Kalshi WS Stream  │  - Simulated Order Fills      │  │
│  │  - NBA Live Data     │  - Position Tracking          │  │
│  │  - Betting Odds      │  - P&L Calculation           │  │
│  └──────────────────────┴───────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    External APIs                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Kalshi WebSocket     │   balldontlie.io REST API    │  │
│  │  - Market Data        │   - Live Box Scores          │  │
│  │  - Orderbook Updates  │   - Betting Odds             │  │
│  │                       │   - Game Stats               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Supabase (PostgreSQL)                     │
│  - Raw Market Data        - Strategy Configurations          │
│  - Simulated Trades       - Performance Metrics              │
│  - Historical Odds        - System Logs                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Models

### 4.1 Database Schema (Supabase)

#### Table: `games`
```sql
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kalshi_event_ticker VARCHAR(100) UNIQUE NOT NULL,
    kalshi_market_ticker_seed VARCHAR(100) NOT NULL, -- The initial ticker entered by user
    nba_game_id INTEGER UNIQUE,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    home_team_id INTEGER,
    away_team_id INTEGER,
    game_date TIMESTAMP NOT NULL,
    status VARCHAR(20), -- 'scheduled', 'live', 'finished'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `kalshi_markets`
```sql
CREATE TABLE kalshi_markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    ticker VARCHAR(100) UNIQUE NOT NULL,
    market_type VARCHAR(20) NOT NULL, -- 'moneyline_home', 'moneyline_away', 'spread', 'total'
    strike_value DECIMAL(10,2), -- For spreads and totals
    side VARCHAR(10), -- 'yes', 'no'
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kalshi_markets_game ON kalshi_markets(game_id);
CREATE INDEX idx_kalshi_markets_ticker ON kalshi_markets(ticker);
```

#### Table: `orderbook_snapshots`
```sql
CREATE TABLE orderbook_snapshots (
    id BIGSERIAL PRIMARY KEY,
    market_id UUID REFERENCES kalshi_markets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    yes_bid DECIMAL(10,4),
    yes_ask DECIMAL(10,4),
    no_bid DECIMAL(10,4),
    no_ask DECIMAL(10,4),
    yes_bid_size INTEGER,
    yes_ask_size INTEGER,
    no_bid_size INTEGER,
    no_ask_size INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orderbook_market_time ON orderbook_snapshots(market_id, timestamp DESC);
```

#### Table: `nba_live_data`
```sql
CREATE TABLE nba_live_data (
    id BIGSERIAL PRIMARY KEY,
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    period INTEGER,
    time_remaining VARCHAR(20),
    home_score INTEGER,
    away_score INTEGER,
    game_status VARCHAR(50),
    raw_data JSONB, -- Full box score data
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_nba_live_game_time ON nba_live_data(game_id, timestamp DESC);
```

#### Table: `betting_odds`
```sql
CREATE TABLE betting_odds (
    id BIGSERIAL PRIMARY KEY,
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    nba_game_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    vendor VARCHAR(50),
    moneyline_home INTEGER,
    moneyline_away INTEGER,
    spread_home_value DECIMAL(10,2),
    spread_home_odds INTEGER,
    spread_away_value DECIMAL(10,2),
    spread_away_odds INTEGER,
    total_value DECIMAL(10,2),
    total_over_odds INTEGER,
    total_under_odds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_betting_odds_game_time ON betting_odds(game_id, timestamp DESC);
```

#### Table: `strategies`
```sql
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'sharp_line', 'momentum', 'ev_multi', 'mean_reversion', 'correlation'
    is_enabled BOOLEAN DEFAULT false,
    config JSONB NOT NULL, -- Strategy-specific parameters
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `simulated_orders`
```sql
CREATE TABLE simulated_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    market_id UUID REFERENCES kalshi_markets(id) ON DELETE SET NULL,
    market_ticker VARCHAR(100) NOT NULL,
    order_type VARCHAR(10) NOT NULL, -- 'market', 'limit'
    side VARCHAR(10) NOT NULL, -- 'yes', 'no'
    quantity INTEGER NOT NULL,
    limit_price DECIMAL(10,4), -- For limit orders
    filled_price DECIMAL(10,4),
    status VARCHAR(20) NOT NULL, -- 'pending', 'filled', 'cancelled'
    placed_at TIMESTAMP NOT NULL,
    filled_at TIMESTAMP,
    signal_data JSONB, -- What triggered this trade
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orders_strategy ON simulated_orders(strategy_id, placed_at DESC);
CREATE INDEX idx_orders_game ON simulated_orders(game_id);
```

#### Table: `positions`
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    market_id UUID REFERENCES kalshi_markets(id) ON DELETE SET NULL,
    market_ticker VARCHAR(100) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'yes', 'no'
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10,4) NOT NULL,
    current_price DECIMAL(10,4),
    unrealized_pnl DECIMAL(10,2),
    realized_pnl DECIMAL(10,2) DEFAULT 0,
    is_open BOOLEAN DEFAULT true,
    opened_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_positions_strategy_open ON positions(strategy_id, is_open);
```

#### Table: `strategy_performance`
```sql
CREATE TABLE strategy_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(10,2) DEFAULT 0,
    unrealized_pnl DECIMAL(10,2) DEFAULT 0,
    realized_pnl DECIMAL(10,2) DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_trade_pnl DECIMAL(10,2),
    max_drawdown DECIMAL(10,2),
    sharpe_ratio DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_performance_strategy_time ON strategy_performance(strategy_id, timestamp DESC);
```

#### Table: `risk_limits`
```sql
CREATE TABLE risk_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    max_position_size INTEGER, -- Max contracts per position
    max_total_exposure INTEGER, -- Max total open contracts
    max_loss_per_trade DECIMAL(10,2), -- Max loss per single trade
    max_daily_loss DECIMAL(10,2), -- Max total loss per day
    max_drawdown_percent DECIMAL(5,2), -- Max drawdown %
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table: `system_logs`
```sql
CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error'
    component VARCHAR(50) NOT NULL, -- 'kalshi_ws', 'nba_api', 'strategy_engine', etc.
    message TEXT NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs(level);
```

---

## 5. Trading Strategies

### 5.1 Strategy 1: Sharp Line Detection

**Concept**: Compare Kalshi prices to professional sportsbook odds. When divergence exceeds threshold, follow the "sharp" money.

**Configurable Parameters**:
```typescript
{
  threshold_percent: number;        // Min % difference to trigger (default: 5.0)
  min_sample_sportsbooks: number;   // Min number of books to compare (default: 3)
  position_size: number;            // Contracts per trade (default: 10)
  cooldown_minutes: number;         // Time between trades on same market (default: 5)
}
```

**Logic**:
1. Aggregate odds from multiple sportsbooks (via balldontlie.io)
2. Convert American odds to implied probabilities
3. Calculate consensus probability (mean or median)
4. Compare to Kalshi market price
5. If abs(kalshi_prob - consensus_prob) > threshold AND kalshi is undervalued → BUY
6. If abs(kalshi_prob - consensus_prob) > threshold AND kalshi is overvalued → SELL

**Example**:
- Kalshi: Lakers YES @ 45¢ (45% implied)
- Sportsbooks consensus: Lakers @ -150 (60% implied)
- Divergence: 15% → BUY Lakers YES on Kalshi

---

### 5.2 Strategy 2: Live Momentum Scalping

**Concept**: Detect when Kalshi prices lag behind rapid in-game developments (scoring runs, lead changes).

**Configurable Parameters**:
```typescript
{
  scoring_run_threshold: number;    // Points scored in timeframe (default: 8)
  timeframe_seconds: number;        // Lookback window (default: 120)
  price_lag_threshold: number;      // Min ¢ lag to trigger (default: 3)
  position_size: number;            // Contracts per trade (default: 10)
  exit_on_reversion: boolean;       // Close when price normalizes (default: true)
}
```

**Logic**:
1. Monitor live box scores for scoring runs
2. Detect significant momentum shifts (e.g., 10-0 run in 2 minutes)
3. Check if Kalshi price has adjusted proportionally
4. If lag detected → Trade in direction of momentum
5. Optional: Exit when price catches up or momentum reverses

**Example**:
- Warriors go on 12-0 run in 90 seconds
- Warriors spread market still at pre-run price
- Strategy buys Warriors spread YES

---

### 5.3 Strategy 3: Expected Value Multi-Source

**Concept**: Aggregate odds from multiple sportsbooks to calculate true probability, then find +EV opportunities.

**Configurable Parameters**:
```typescript
{
  min_ev_percent: number;           // Minimum +EV to trade (default: 3.0)
  aggregation_method: string;       // 'mean', 'median', 'weighted' (default: 'median')
  min_sportsbooks: number;          // Min books for consensus (default: 5)
  position_size: number;            // Contracts per trade (default: 10)
  kelly_fraction: number;           // Kelly criterion fraction (default: 0.25)
}
```

**Logic**:
1. Fetch odds from all available sportsbooks
2. Remove outliers (optional)
3. Calculate aggregated implied probability
4. Compare to Kalshi price
5. Calculate EV = (kalshi_payout * true_prob) - kalshi_price
6. If EV > min_ev_percent → Trade
7. Optional: Size position using Kelly criterion

---

### 5.4 Strategy 4: Total Points Mean Reversion

**Concept**: Track live scoring pace vs projected total. Bet on regression when deviation is significant.

**Configurable Parameters**:
```typescript
{
  min_deviation_percent: number;    // Min % deviation to trigger (default: 15.0)
  min_time_elapsed_percent: number; // Min % of game elapsed (default: 25.0)
  reversion_confidence: number;     // Confidence multiplier (default: 1.0)
  position_size: number;            // Contracts per trade (default: 10)
  partial_exit_threshold: number;   // Exit % when deviation normalizes (default: 50.0)
}
```

**Logic**:
1. Get opening total from sportsbooks
2. Calculate expected pace: total / 48 minutes
3. Track actual scoring pace in real-time
4. Calculate projected final score based on current pace
5. If projected_total >> opening_total AND deviation > threshold → BET UNDER
6. If projected_total << opening_total AND deviation > threshold → BET OVER
7. Exit when pace normalizes or end of game approaches

**Example**:
- Opening total: 220.5
- After Q1: Teams scored 70 points (pace for 280 total)
- Deviation: +27% → BET UNDER

---

### 5.5 Strategy 5: Spread Correlation Play

**Concept**: Monitor multiple spread markets (e.g., -5.5, -6.5, -7.5). Identify mispriced relationships between adjacent lines.

**Configurable Parameters**:
```typescript
{
  max_spread_gap: number;           // Max spread difference to monitor (default: 3.0)
  correlation_threshold: number;    // Min correlation violation (default: 0.10)
  position_size: number;            // Contracts per trade (default: 10)
  hedge_mode: boolean;              // Auto-hedge across spreads (default: false)
}
```

**Logic**:
1. Identify all spread markets for a game (e.g., -4.5, -5.5, -6.5)
2. Calculate implied probabilities for each spread
3. Check if probabilities follow logical ordering
4. If P(spread -4.5) < P(spread -6.5) → Arbitrage opportunity
5. Execute trades to exploit mispricing

**Example**:
- Lakers -5.5 YES @ 52¢ (52% implied)
- Lakers -6.5 YES @ 48¢ (48% implied)
- This is correct ordering
- BUT if -6.5 YES @ 54¢ → Mispriced, sell -6.5 / buy -5.5

---

## 6. API Integration Details

### 6.1 Kalshi Integration

#### 6.1.1 Market Discovery Flow
```python
# User enters: "kxnbagame-26jan06dalsac"

# Step 1: GET /markets/{ticker}
response = kalshi_client.get_market("kxnbagame-26jan06dalsac")
event_ticker = response.event_ticker  # e.g., "NBAGAME-26JAN06-DALSAC"

# Step 2: GET /events/{event_ticker}?with_nested_markets=true
event_response = kalshi_client.get_event(event_ticker, with_nested_markets=True)

# Step 3: Parse all markets
markets = event_response.markets
for market in markets:
    # market.ticker, market.yes_bid, market.yes_ask, etc.
    # Categorize by type: moneyline, spread, total
    classify_market(market)
```

#### 6.1.2 WebSocket Connection
```python
# Note: WebSocket details not in OpenAPI spec - refer to Kalshi docs
import websockets

async def connect_kalshi_ws():
    uri = "wss://trading-api.kalshi.com/trade-api/ws/v2"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Subscribe to markets
        subscribe_msg = {
            "cmd": "subscribe",
            "params": {
                "channels": ["orderbook_delta", "ticker"],
                "market_tickers": [ticker for ticker in market_tickers]
            }
        }
        await ws.send(json.dumps(subscribe_msg))
        
        # Listen for updates
        async for message in ws:
            data = json.loads(message)
            await process_orderbook_update(data)
```

#### 6.1.3 Orderbook Data Processing
```python
async def process_orderbook_update(data):
    """
    Handle orderbook delta messages from Kalshi WebSocket
    Process asynchronously to avoid blocking
    """
    market_ticker = data['market_ticker']
    timestamp = datetime.fromtimestamp(data['ts'] / 1000)
    
    # Update in-memory orderbook
    orderbook_cache[market_ticker] = {
        'yes_bid': data.get('yes', {}).get('bid'),
        'yes_ask': data.get('yes', {}).get('ask'),
        'no_bid': data.get('no', {}).get('bid'),
        'no_ask': data.get('no', {}).get('ask'),
        'timestamp': timestamp
    }
    
    # Store snapshot in database (async task)
    await store_orderbook_snapshot(market_ticker, orderbook_cache[market_ticker])
    
    # Emit to frontend via WebSocket
    await socketio.emit('orderbook_update', {
        'market': market_ticker,
        'data': orderbook_cache[market_ticker]
    })
    
    # Trigger strategy evaluation
    await evaluate_strategies(market_ticker)
```

---

### 6.2 balldontlie.io Integration

#### 6.2.1 Auto-Extraction from Kalshi Ticker

```python
def extract_game_info_from_kalshi_ticker(ticker: str) -> dict:
    """
    Parse Kalshi market ticker to extract date and teams
    Example: "kxnbagame-26jan06dalsac" → {"date": "2026-01-06", "teams": ["DAL", "SAC"]}
    """
    # Remove prefix
    ticker = ticker.replace("kxnbagame-", "").replace("kx", "")
    
    # Extract date portion (format: DDmmmYY)
    # Example: "26jan06" → 06-Jan-2026
    date_pattern = r'(\d{2})([a-z]{3})(\d{2})'
    match = re.search(date_pattern, ticker, re.IGNORECASE)
    
    if match:
        day = match.group(1)
        month = match.group(2).capitalize()
        year = "20" + match.group(3)
        
        # Convert to date
        date_str = f"{year}-{month}-{day}"
        game_date = datetime.strptime(date_str, "%Y-%b-%d")
        
        # Extract team codes (remaining characters)
        teams_portion = ticker[match.end():]
        # Typically 6 chars: 3 for each team
        if len(teams_portion) >= 6:
            away_team = teams_portion[:3].upper()
            home_team = teams_portion[3:6].upper()
            
            return {
                "date": game_date.strftime("%Y-%m-%d"),
                "away_team_abbr": away_team,
                "home_team_abbr": home_team
            }
    
    raise ValueError(f"Could not parse Kalshi ticker: {ticker}")
```

#### 6.2.2 Match to balldontlie.io Game

```python
async def find_nba_game(date: str, away_abbr: str, home_abbr: str) -> int:
    """
    Find NBA game ID from balldontlie.io
    """
    # Step 1: Get all games for the date
    response = await bdl_client.get(f"/nba/v1/games", params={
        "dates[]": [date]
    })
    
    games = response['data']
    
    # Step 2: Match teams
    for game in games:
        away_match = game['visitor_team']['abbreviation'] == away_abbr
        home_match = game['home_team']['abbreviation'] == home_abbr
        
        if away_match and home_match:
            return game['id']
    
    raise ValueError(f"No game found for {away_abbr} @ {home_abbr} on {date}")
```

#### 6.2.3 Live Data Polling

```python
async def poll_live_nba_data(game_id: int, nba_game_id: int):
    """
    Poll balldontlie.io for live game data
    Run every 5-10 seconds during live games
    """
    while game_is_active(game_id):
        try:
            # Get live box scores
            box_score_response = await bdl_client.get("/nba/v1/box_scores/live")
            live_games = box_score_response['data']
            
            game_data = next(
                (g for g in live_games if g['game']['id'] == nba_game_id),
                None
            )
            
            if game_data:
                # Store in database
                await store_nba_live_data(game_id, game_data)
                
                # Emit to frontend
                await socketio.emit('nba_live_update', {
                    'game_id': game_id,
                    'data': game_data
                })
            
            # Get latest odds
            odds_response = await bdl_client.get("/nba/v2/odds", params={
                "game_ids": [nba_game_id]
            })
            
            if odds_response['data']:
                await store_betting_odds(game_id, odds_response['data'])
            
            await asyncio.sleep(5)  # Poll every 5 seconds
            
        except Exception as e:
            logger.error(f"Error polling NBA data: {e}")
            await asyncio.sleep(10)
```

---

### 6.3 Data Aggregation Layer

The Data Aggregation Layer provides a unified interface for accessing all game-related data (Kalshi orderbooks, NBA live data, betting odds) through a single `GameState` model and coordinates background polling tasks.

#### 6.3.1 GameState Model

```python
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel

class OrderbookState(BaseModel):
    """Current orderbook state for a market."""
    ticker: str
    yes_bid: Optional[Decimal] = None
    yes_ask: Optional[Decimal] = None
    no_bid: Optional[Decimal] = None
    no_ask: Optional[Decimal] = None
    yes_bid_size: Optional[int] = None
    yes_ask_size: Optional[int] = None
    last_updated: datetime

class NBALiveState(BaseModel):
    """Current NBA game state."""
    period: int
    time_remaining: str
    home_score: int
    away_score: int
    game_status: str
    last_updated: datetime

class OddsState(BaseModel):
    """Aggregated betting odds from sportsbooks."""
    vendor: str
    moneyline_home: Optional[int] = None
    moneyline_away: Optional[int] = None
    spread_home_value: Optional[Decimal] = None
    spread_home_odds: Optional[int] = None
    total_value: Optional[Decimal] = None
    total_over_odds: Optional[int] = None
    total_under_odds: Optional[int] = None
    last_updated: datetime

class GameState(BaseModel):
    """Unified game state combining all data sources."""
    game_id: str
    event_ticker: str
    home_team: str
    away_team: str
    game_date: datetime
    status: str  # 'scheduled', 'live', 'finished'
    
    # Kalshi orderbooks by market ticker
    orderbooks: Dict[str, OrderbookState] = {}
    
    # NBA live data
    nba_state: Optional[NBALiveState] = None
    
    # Betting odds by vendor
    odds: Dict[str, OddsState] = {}
    
    # Calculated fields
    implied_probabilities: Dict[str, Decimal] = {}
    
    last_updated: datetime
```

#### 6.3.2 Data Flow Diagram

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
│  ┌──────────────────────────────────────────────────┐      │
│  │              GameState Cache                      │      │
│  │  • orderbooks: Dict[ticker, OrderbookState]      │      │
│  │  • nba_state: NBALiveState                       │      │
│  │  • odds: Dict[vendor, OddsState]                 │      │
│  │  • implied_probabilities: Dict[ticker, Decimal]  │      │
│  └──────────────────────┬───────────────────────────┘      │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────┐      │
│  │           Event Subscription System               │      │
│  │  • on_orderbook_update(callback)                 │      │
│  │  • on_nba_update(callback)                       │      │
│  │  • on_odds_update(callback)                      │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Strategy Engine                            │
│  • Receives unified GameState                               │
│  • Evaluates trading signals                                │
│  • Executes simulated orders                                │
└─────────────────────────────────────────────────────────────┘
```

#### 6.3.3 Polling Frequencies

| Data Source | Polling Frequency | Notes |
|-------------|-------------------|-------|
| Kalshi Orderbook | Real-time (WebSocket) | Snapshot + delta updates |
| NBA Live Data | 5 seconds | During live games only |
| Betting Odds | 10 seconds | During live games only |
| P&L Calculation | 5 seconds | Triggered by orderbook updates |

#### 6.3.4 Event Subscription System

```python
from typing import Callable, Awaitable
from enum import Enum

class EventType(Enum):
    ORDERBOOK_UPDATE = "orderbook_update"
    NBA_UPDATE = "nba_update"
    ODDS_UPDATE = "odds_update"
    STATE_CHANGE = "state_change"

class DataAggregator:
    """Central data aggregator with event subscription."""
    
    def __init__(self):
        self._game_states: Dict[str, GameState] = {}
        self._subscribers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._polling_tasks: Dict[str, asyncio.Task] = {}
    
    def subscribe(
        self, 
        event_type: EventType, 
        callback: Callable[[str, GameState], Awaitable[None]]
    ) -> None:
        """Subscribe to data updates."""
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(
        self, 
        event_type: EventType, 
        callback: Callable
    ) -> None:
        """Unsubscribe from data updates."""
        self._subscribers[event_type].remove(callback)
    
    async def _notify_subscribers(
        self, 
        event_type: EventType, 
        game_id: str
    ) -> None:
        """Notify all subscribers of an event."""
        state = self._game_states.get(game_id)
        if state:
            for callback in self._subscribers[event_type]:
                try:
                    await callback(game_id, state)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
```

#### 6.3.5 API Endpoints for Aggregator

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/aggregator/states` | GET | List all active game states |
| `/api/aggregator/load/{game_id}` | POST | Load a game into the aggregator |
| `/api/aggregator/state/{game_id}` | GET | Get unified state for a game |
| `/api/aggregator/unload/{game_id}` | DELETE | Stop tracking a game |
| `/api/aggregator/subscribe` | WebSocket | Subscribe to real-time updates |

---

## 7. Order Execution Simulation

### 7.1 Execution Logic

```python
async def execute_simulated_order(
    strategy_id: str,
    market_ticker: str,
    side: str,  # 'yes' or 'no'
    quantity: int,
    order_type: str = 'market'
):
    """
    Simulate order execution at current best bid/ask
    """
    # Get current orderbook
    orderbook = orderbook_cache.get(market_ticker)
    if not orderbook:
        raise ValueError(f"No orderbook data for {market_ticker}")
    
    # Determine fill price
    if side == 'yes':
        fill_price = orderbook['yes_ask']  # Buying YES = taking the ask
    else:
        fill_price = orderbook['no_ask']   # Buying NO = taking the ask
    
    # Check risk limits
    await check_risk_limits(strategy_id, quantity, fill_price)
    
    # Create order record
    order = {
        'id': str(uuid.uuid4()),
        'strategy_id': strategy_id,
        'market_ticker': market_ticker,
        'side': side,
        'quantity': quantity,
        'order_type': order_type,
        'filled_price': fill_price,
        'status': 'filled',
        'placed_at': datetime.utcnow(),
        'filled_at': datetime.utcnow()
    }
    
    # Store in database
    await db.insert('simulated_orders', order)
    
    # Update position
    await update_position(strategy_id, market_ticker, side, quantity, fill_price)
    
    # Log trade
    logger.info(f"Executed: {side.upper()} {quantity} {market_ticker} @ {fill_price}¢")
    
    return order
```

### 7.2 Position Management

```python
async def update_position(
    strategy_id: str,
    market_ticker: str,
    side: str,
    quantity: int,
    price: float
):
    """
    Update or create position after trade execution
    """
    # Check if position exists
    position = await db.query_one(
        'positions',
        {'strategy_id': strategy_id, 'market_ticker': market_ticker, 'side': side, 'is_open': True}
    )
    
    if position:
        # Update existing position
        old_quantity = position['quantity']
        old_avg_price = position['avg_price']
        
        new_quantity = old_quantity + quantity
        new_avg_price = ((old_quantity * old_avg_price) + (quantity * price)) / new_quantity
        
        await db.update('positions', position['id'], {
            'quantity': new_quantity,
            'avg_price': new_avg_price,
            'updated_at': datetime.utcnow()
        })
    else:
        # Create new position
        await db.insert('positions', {
            'id': str(uuid.uuid4()),
            'strategy_id': strategy_id,
            'market_ticker': market_ticker,
            'side': side,
            'quantity': quantity,
            'avg_price': price,
            'is_open': True,
            'opened_at': datetime.utcnow()
        })
```

### 7.3 Real-Time P&L Calculation

```python
async def calculate_pnl(strategy_id: str) -> dict:
    """
    Calculate real-time P&L for a strategy
    """
    positions = await db.query_many(
        'positions',
        {'strategy_id': strategy_id, 'is_open': True}
    )
    
    total_unrealized_pnl = 0
    
    for pos in positions:
        market_ticker = pos['market_ticker']
        orderbook = orderbook_cache.get(market_ticker)
        
        if not orderbook:
            continue
        
        # Current market price (what we could sell for)
        if pos['side'] == 'yes':
            current_price = orderbook['yes_bid']  # Sell YES at bid
        else:
            current_price = orderbook['no_bid']   # Sell NO at bid
        
        # Update position with current price
        await db.update('positions', pos['id'], {
            'current_price': current_price
        })
        
        # Calculate unrealized P&L
        # P&L = (current_price - avg_price) * quantity (in cents)
        pnl = (current_price - pos['avg_price']) * pos['quantity']
        
        await db.update('positions', pos['id'], {
            'unrealized_pnl': pnl / 100  # Convert to dollars
        })
        
        total_unrealized_pnl += pnl / 100
    
    # Get realized P&L from closed positions
    realized_pnl = await db.query_scalar(
        'positions',
        {'strategy_id': strategy_id, 'is_open': False},
        'SUM(realized_pnl)'
    )
    
    return {
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_realized_pnl': realized_pnl or 0,
        'total_pnl': total_unrealized_pnl + (realized_pnl or 0)
    }
```

---

## 8. Frontend UI Specification

### 8.1 Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Kalshi NBA Paper Trading                    [Settings] [⚙] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Game Setup                                          │  │
│  │  ┌────────────────────────────┐  [Load Game]        │  │
│  │  │ kxnbagame-26jan06dalsac    │                      │  │
│  │  └────────────────────────────┘                      │  │
│  │  Status: ● ACTIVE  |  LAL @ DAL  |  Q2 5:32          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Strategy Controls                                   │  │
│  │  ┌────────────┬────────────┬────────────────────┐   │  │
│  │  │ Sharp Line │ Momentum   │ EV Multi-Source    │   │  │
│  │  │ [ON] 🟢    │ [OFF] ⚪   │ [ON] 🟢           │   │  │
│  │  │ Config ⚙   │ Config ⚙   │ Config ⚙           │   │  │
│  │  └────────────┴────────────┴────────────────────┘   │  │
│  │  ┌────────────┬────────────┐                        │  │
│  │  │ Mean Rev.  │ Correlation│                        │  │
│  │  │ [ON] 🟢    │ [OFF] ⚪   │                        │  │
│  │  │ Config ⚙   │ Config ⚙   │                        │  │
│  │  └────────────┴────────────┘                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Live Market Data                                    │  │
│  │  ┌───────────────────┬──────┬──────┬──────┬──────┐  │  │
│  │  │ Market            │ Bid  │ Ask  │ Last │ Vol  │  │  │
│  │  ├───────────────────┼──────┼──────┼──────┼──────┤  │  │
│  │  │ LAL ML YES        │ 0.42 │ 0.44 │ 0.43 │ 2.5K │  │  │
│  │  │ DAL ML YES        │ 0.56 │ 0.58 │ 0.57 │ 3.1K │  │  │
│  │  │ LAL -5.5 YES      │ 0.48 │ 0.50 │ 0.49 │ 1.8K │  │  │
│  │  │ Total 225.5 OVER  │ 0.51 │ 0.53 │ 0.52 │ 2.2K │  │  │
│  │  └───────────────────┴──────┴──────┴──────┴──────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Active Positions                                    │  │
│  │  ┌──────────┬────────┬──────┬─────┬─────┬─────────┐ │  │
│  │  │ Strategy │ Market │ Side │ Qty │ Avg │ P&L     │ │  │
│  │  ├──────────┼────────┼──────┼─────┼─────┼─────────┤ │  │
│  │  │ Sharp    │ LAL ML │ YES  │ 25  │ 0.41│ +$1.25  │ │  │
│  │  │ EV Multi │ Total  │ OVER │ 15  │ 0.50│ +$0.45  │ │  │
│  │  │ Momentum │ LAL -5 │ YES  │ 20  │ 0.47│ -$0.40  │ │  │
│  │  └──────────┴────────┴──────┴─────┴─────┴─────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Performance Summary                                 │  │
│  │  ┌───────────┬────────┬─────────┬──────────────┐    │  │
│  │  │ Strategy  │ Trades │ Win %   │ Total P&L    │    │  │
│  │  ├───────────┼────────┼─────────┼──────────────┤    │  │
│  │  │ Sharp     │ 12     │ 66.7%   │ +$5.80       │    │  │
│  │  │ Momentum  │ 8      │ 50.0%   │ -$1.20       │    │  │
│  │  │ EV Multi  │ 15     │ 73.3%   │ +$8.45       │    │  │
│  │  │ Mean Rev. │ 6      │ 83.3%   │ +$3.10       │    │  │
│  │  │ ALL       │ 41     │ 68.3%   │ +$16.15      │    │  │
│  │  └───────────┴────────┴─────────┴──────────────┘    │  │
│  │                                                       │  │
│  │  [P&L Chart]                                         │  │
│  │   📈 Line chart showing cumulative P&L over time     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Trade Log (Live)                                    │  │
│  │  ┌──────────┬────────┬──────┬─────┬──────┬────────┐ │  │
│  │  │ Time     │ Strat  │ Mrkt │ Side│ Price│ Reason │ │  │
│  │  ├──────────┼────────┼──────┼─────┼──────┼────────┤ │  │
│  │  │ 14:32:15 │ Sharp  │ LAML │ YES │ 0.43 │ +7% EV │ │  │
│  │  │ 14:31:02 │ Moment │ LAL-5│ YES │ 0.48 │ 8-0 RUN│ │  │
│  │  └──────────┴────────┴──────┴─────┴──────┴────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Component Specifications

#### 8.2.1 Game Setup Panel
```typescript
interface GameSetupProps {
  onGameLoad: (ticker: string) => void;
}

// Features:
// - Text input for Kalshi market ticker
// - "Load Game" button
// - Status indicator (inactive/active/finished)
// - Game info display (teams, time, score)
```

#### 8.2.2 Strategy Control Cards
```typescript
interface StrategyCardProps {
  strategy: Strategy;
  isEnabled: boolean;
  onToggle: (strategyId: string, enabled: boolean) => void;
  onConfigEdit: (strategyId: string) => void;
}

// Features:
// - ON/OFF toggle with visual indicator
// - Strategy name and type
// - Quick stats (trades today, current P&L)
// - Config button → opens modal with parameters
```

#### 8.2.3 Live Market Data Table
```typescript
interface MarketDataProps {
  markets: KalshiMarket[];
  updateFrequency: number; // ms
}

// Features:
// - Real-time updating prices (via WebSocket)
// - Color coding for price movements (green up, red down)
// - Sortable columns
// - Filter by market type
```

#### 8.2.4 Positions Table
```typescript
interface PositionsTableProps {
  positions: Position[];
  onClose: (positionId: string) => void;
}

// Features:
// - Real-time P&L updates
// - Color coding for profit/loss
// - Manual close button
// - Grouped by strategy
```

#### 8.2.5 Performance Charts
```typescript
interface PerformanceChartProps {
  strategies: Strategy[];
  timeRange: string; // '1h', '4h', 'today', 'all'
}

// Features:
// - Line chart for cumulative P&L
// - Multiple lines (one per strategy + total)
// - Tooltips showing trade details on hover
// - Time range selector
```

---

## 9. Risk Management

### 9.1 Pre-Trade Checks

```python
async def check_risk_limits(strategy_id: str, quantity: int, price: float) -> bool:
    """
    Verify trade passes risk checks before execution
    """
    risk_limits = await db.query_one('risk_limits', {'strategy_id': strategy_id})
    
    if not risk_limits:
        return True  # No limits set
    
    # Check 1: Position size limit
    if risk_limits.max_position_size and quantity > risk_limits.max_position_size:
        logger.warning(f"Trade rejected: Exceeds max position size")
        return False
    
    # Check 2: Total exposure limit
    current_exposure = await get_total_open_contracts(strategy_id)
    if risk_limits.max_total_exposure and (current_exposure + quantity) > risk_limits.max_total_exposure:
        logger.warning(f"Trade rejected: Exceeds max total exposure")
        return False
    
    # Check 3: Max loss per trade
    max_loss = quantity * (price / 100)  # Convert cents to dollars
    if risk_limits.max_loss_per_trade and max_loss > risk_limits.max_loss_per_trade:
        logger.warning(f"Trade rejected: Potential loss exceeds limit")
        return False
    
    # Check 4: Daily loss limit
    daily_pnl = await get_daily_pnl(strategy_id)
    if risk_limits.max_daily_loss and daily_pnl < -risk_limits.max_daily_loss:
        logger.warning(f"Trade rejected: Daily loss limit reached")
        return False
    
    # Check 5: Drawdown limit
    max_dd_pct = await calculate_drawdown_percent(strategy_id)
    if risk_limits.max_drawdown_percent and max_dd_pct > risk_limits.max_drawdown_percent:
        logger.warning(f"Trade rejected: Max drawdown exceeded")
        return False
    
    return True
```

### 9.2 Position Limits

```python
# Default risk limits per strategy
DEFAULT_RISK_LIMITS = {
    'max_position_size': 100,        # Max 100 contracts per position
    'max_total_exposure': 500,       # Max 500 open contracts total
    'max_loss_per_trade': 50.00,     # Max $50 loss per trade
    'max_daily_loss': 200.00,        # Max $200 loss per day
    'max_drawdown_percent': 20.0     # Max 20% drawdown
}
```

---

## 10. System Configuration

### 10.1 Environment Variables

```bash
# Kalshi API
KALSHI_API_URL=https://api.elections.kalshi.com/trade-api/v2
KALSHI_WS_URL=wss://trading-api.kalshi.com/trade-api/ws/v2
KALSHI_API_KEY=your_api_key
KALSHI_API_SECRET=your_api_secret

# balldontlie.io API
BALLDONTLIE_API_URL=https://api.balldontlie.io
BALLDONTLIE_API_KEY=your_api_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Redis
REDIS_URL=redis://localhost:6379

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

### 10.2 Data Update Frequencies

```python
DATA_POLL_INTERVALS = {
    'kalshi_orderbook': 'websocket',     # Real-time via WebSocket
    'nba_live_boxscore': 5,              # Every 5 seconds during live games
    'betting_odds': 10,                  # Every 10 seconds
    'strategy_evaluation': 2,            # Every 2 seconds
    'pnl_calculation': 5,                # Every 5 seconds
    'performance_metrics': 60            # Every 60 seconds
}
```

---

## 11. API Endpoints (Backend)

### 11.1 Game Management

```
POST /api/games/load
Body: { "kalshi_ticker": "kxnbagame-26jan06dalsac" }
Response: { "game_id": "uuid", "event_ticker": "...", "markets": [...] }

GET /api/games/{game_id}
Response: { "game": {...}, "markets": [...], "nba_data": {...} }

DELETE /api/games/{game_id}
Response: { "success": true }
```

### 11.2 Strategy Management

```
GET /api/strategies
Response: { "strategies": [...] }

POST /api/strategies/{strategy_id}/toggle
Body: { "enabled": true }
Response: { "strategy": {...} }

PUT /api/strategies/{strategy_id}/config
Body: { "config": {...} }
Response: { "strategy": {...} }

GET /api/strategies/{strategy_id}/performance
Query: ?start_time=...&end_time=...
Response: { "metrics": {...}, "trades": [...] }
```

### 11.3 Trading

```
GET /api/positions
Query: ?strategy_id=...&is_open=true
Response: { "positions": [...] }

POST /api/orders/simulate
Body: { "strategy_id": "...", "market_ticker": "...", "side": "yes", "quantity": 10 }
Response: { "order": {...}, "position": {...} }

POST /api/positions/{position_id}/close
Response: { "success": true, "realized_pnl": 5.23 }
```

### 11.4 Market Data

```
GET /api/markets/{game_id}
Response: { "markets": [...] }

GET /api/orderbook/{market_ticker}
Response: { "ticker": "...", "yes_bid": 0.42, "yes_ask": 0.44, ... }
```

### 11.5 Analytics

```
GET /api/analytics/summary
Query: ?strategy_id=...&time_range=today
Response: { 
  "total_pnl": 25.50,
  "total_trades": 42,
  "win_rate": 0.678,
  "sharpe_ratio": 1.45
}

GET /api/analytics/pnl-history
Query: ?strategy_id=...&interval=1h
Response: { "datapoints": [{ "timestamp": "...", "pnl": 5.23 }, ...] }
```

---

## 12. WebSocket Events

### 12.1 Client → Server

```typescript
// Subscribe to game updates
socket.emit('subscribe_game', { game_id: 'uuid' });

// Subscribe to strategy updates
socket.emit('subscribe_strategy', { strategy_id: 'uuid' });

// Unsubscribe
socket.emit('unsubscribe_game', { game_id: 'uuid' });
```

### 12.2 Server → Client

```typescript
// Orderbook update
{
  event: 'orderbook_update',
  data: {
    market_ticker: 'kxnbagame-26jan06dalsac',
    yes_bid: 0.42,
    yes_ask: 0.44,
    timestamp: '2026-01-06T19:32:15Z'
  }
}

// NBA live data update
{
  event: 'nba_live_update',
  data: {
    game_id: 'uuid',
    period: 2,
    time_remaining: '5:32',
    home_score: 58,
    away_score: 52
  }
}

// Trade executed
{
  event: 'trade_executed',
  data: {
    strategy_id: 'uuid',
    order: {...},
    position: {...}
  }
}

// Position update (P&L change)
{
  event: 'position_update',
  data: {
    position_id: 'uuid',
    current_price: 0.45,
    unrealized_pnl: 1.25
  }
}

// Strategy signal (for debugging)
{
  event: 'strategy_signal',
  data: {
    strategy_name: 'Sharp Line Detection',
    signal_type: 'buy',
    confidence: 0.85,
    reason: 'Kalshi 7% undervalued vs sportsbooks'
  }
}
```

---

## 13. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Setup Supabase database with all tables
- [ ] Implement Kalshi API client (REST + WebSocket)
- [ ] Implement balldontlie.io API client
- [ ] Build auto-extraction logic for matching games
- [ ] Create backend API skeleton (FastAPI)
- [ ] Setup Redis for caching

### Phase 2: Data Pipeline (Week 2)
- [ ] Kalshi WebSocket connection and orderbook processing
- [ ] NBA live data polling loop
- [ ] Betting odds fetching and storage
- [ ] Data aggregation and caching layer
- [ ] WebSocket server for frontend

### Phase 3: Trading Engine (Week 3)
- [ ] Implement all 5 trading strategies
- [ ] Order execution simulation
- [ ] Position management system
- [ ] Real-time P&L calculation
- [ ] Risk management checks

### Phase 4: Frontend (Week 4)
- [ ] Build Next.js app structure
- [ ] Create all UI components
- [ ] WebSocket client integration
- [ ] Real-time data visualization
- [ ] Strategy configuration modals

### Phase 5: Testing & Refinement (Week 5)
- [ ] End-to-end testing with live data
- [ ] Performance optimization
- [ ] Error handling and logging
- [ ] Documentation
- [ ] Deploy to production

---

## 14. Testing Strategy

### 14.1 Unit Tests
- Strategy logic functions
- P&L calculation
- Risk limit checks
- API parsers (Kalshi ticker extraction)

### 14.2 Integration Tests
- Kalshi API integration
- balldontlie.io API integration
- Database operations
- WebSocket connections

### 14.3 End-to-End Tests
- Full game lifecycle (load → trade → close)
- Multi-strategy execution
- Real-time data flow
- Frontend interactions

---

## 15. Monitoring & Logging

### 15.1 Key Metrics to Track
- WebSocket connection uptime
- API response times
- Data polling latency
- Strategy execution frequency
- Trade execution success rate
- P&L accuracy

### 15.2 Logging Levels
```python
# INFO: Normal operations
logger.info("Game loaded: LAL @ DAL")
logger.info("Strategy Sharp Line enabled")

# WARNING: Non-critical issues
logger.warning("Orderbook data delayed by 2 seconds")
logger.warning("Risk limit check failed for trade")

# ERROR: Critical failures
logger.error("Kalshi WebSocket disconnected")
logger.error("Failed to fetch NBA live data")
```

---

## 16. Error Handling

### 16.1 Kalshi WebSocket Disconnection
```python
async def handle_kalshi_ws_disconnect():
    """
    Reconnect with exponential backoff
    """
    retries = 0
    max_retries = 10
    
    while retries < max_retries:
        try:
            await asyncio.sleep(2 ** retries)  # Exponential backoff
            await connect_kalshi_ws()
            logger.info("Kalshi WebSocket reconnected")
            return
        except Exception as e:
            retries += 1
            logger.error(f"Reconnection attempt {retries} failed: {e}")
    
    # Critical failure - notify user
    await send_alert("Kalshi WebSocket connection failed after 10 retries")
```

### 16.2 API Rate Limiting
```python
# balldontlie.io rate limit handling
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(url, params):
    response = await http_client.get(url, params=params)
    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    return response
```

---

## 17. Future Enhancements

### 17.1 Advanced Features
- [ ] Backtesting engine with historical data
- [ ] Machine learning model integration for predictions
- [ ] Multi-game support (trade multiple games simultaneously)
- [ ] Auto-hedging across correlated markets
- [ ] Portfolio-level risk management
- [ ] Automated strategy optimization (parameter tuning)

### 17.2 UI Improvements
- [ ] Mobile-responsive design
- [ ] Dark mode
- [ ] Advanced charting (TradingView integration)
- [ ] Trade replay and analysis
- [ ] Strategy comparison tools
- [ ] Alert/notification system

---

## 18. Security Considerations

### 18.1 API Key Management
- Store API keys in environment variables
- Never commit keys to version control
- Use Supabase Row Level Security (RLS)
- Implement API key rotation

### 18.2 Data Validation
- Validate all user inputs
- Sanitize Kalshi tickers before parsing
- Verify market data integrity
- Implement rate limiting on API endpoints

---

## 19. Deployment Checklist

### 19.1 Pre-Deployment
- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] API keys tested
- [ ] WebSocket connections verified
- [ ] Frontend build successful

### 19.2 Production Setup
- [ ] Setup monitoring (e.g., Sentry)
- [ ] Configure logging (e.g., Logstash)
- [ ] Database backups enabled
- [ ] SSL certificates installed
- [ ] CORS properly configured

---

## 20. Support & Maintenance

### 20.1 Known Limitations
- Kalshi WebSocket documentation may be incomplete (refer to official docs)
- balldontlie.io API has rate limits (check current limits)
- Simulated fills don't account for slippage
- No historical data storage for backtesting

### 20.2 Troubleshooting Guide
1. **WebSocket won't connect**: Check API credentials, network settings
2. **No NBA data**: Verify API key, check game is live
3. **Strategies not executing**: Check if enabled, verify risk limits
4. **Incorrect P&L**: Verify orderbook data is updating

---

## 21. Additional Notes

### 21.1 Strategy Parameter Tuning
Each strategy should be tested with different parameter values to find optimal settings. Recommended approach:
1. Start with conservative defaults
2. Run for 5-10 games
3. Analyze win rate and P&L
4. Adjust parameters incrementally
5. Re-test and iterate

### 21.2 Data Retention Policy
- **Orderbook snapshots**: Keep for 7 days (high volume)
- **NBA live data**: Keep for 30 days
- **Betting odds**: Keep for 90 days
- **Trades/positions**: Keep indefinitely
- **Performance metrics**: Keep indefinitely
- **System logs**: Keep for 30 days

---

## 22. Glossary

- **Kalshi**: Prediction market platform
- **Event**: A real-world occurrence (e.g., NBA game)
- **Market**: A specific binary outcome within an event (e.g., "Lakers win")
- **Ticker**: Unique identifier for a market
- **Orderbook**: List of bids and asks for a market
- **Paper Trading**: Simulated trading without real money
- **P&L**: Profit and Loss
- **Sharpe Ratio**: Risk-adjusted return metric
- **Kelly Criterion**: Position sizing formula based on edge and odds

---

## End of PRD

This document should provide comprehensive guidance for implementing the Kalshi NBA Paper Trading Application. The coding LLM should have all necessary information to build the complete system, including:

- Complete database schema
- All trading strategies with detailed logic
- API integration patterns for both Kalshi and balldontlie.io
- Order execution simulation
- Full frontend UI specification
- WebSocket event specifications
- Error handling and monitoring

**Next Steps**: Begin with Phase 1 (Core Infrastructure) and proceed sequentially through the implementation phases.

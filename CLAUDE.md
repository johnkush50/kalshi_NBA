# Claude Code Instructions

## Project Overview
Building a full-stack Kalshi NBA paper trading application. This system monitors live Kalshi prediction markets and NBA game data to execute multiple automated trading strategies and track simulated performance.

**Complete specifications:** See `kalshi_nba_paper_trading_prd.md`

---

## Current Phase
**Phase 1: Core Infrastructure** (Backend Setup - Weeks 1-2)

---

## Your Task This Session
**Iteration 6: Order Execution Engine**

**Iteration 5 Status:** ✅ COMPLETE

Sharp Line Detection Strategy is complete:
- ✅ Base strategy class with abstract interface (base.py)
- ✅ Sharp Line Detection strategy implementation (sharp_line.py)
- ✅ Strategy execution engine with background evaluation (strategy_engine.py)
- ✅ Strategy API endpoints (strategies.py routes)
- ✅ Test script created (test_strategy.py)
- ✅ Strategy engine lifecycle hooks in main.py

**Next Steps (Iteration 6):**
1. **ORDER EXECUTOR:**
   - Simulate order fills at best bid/ask
   - Handle market and limit orders
   - Track fill prices and timestamps
   - Connect to strategy signals

2. **POSITION MANAGER:**
   - Track open positions by market
   - Calculate average entry price
   - Handle position closes
   - Store positions in database

3. **P&L CALCULATOR:**
   - Real-time P&L calculation
   - Mark-to-market using current prices
   - Realized vs unrealized P&L
   - Performance metrics (win rate, Sharpe)

4. **RISK MANAGEMENT:**
   - Position size limits
   - Drawdown limits
   - Max concurrent positions

---

## Known Issues from Previous Iterations

### All Issues RESOLVED ✅

**Iteration 1 - Ticker Parser Date Bug:** ✅ FIXED
- Was: Parsed '26jan06' as DDmmmYY (2006-01-26)
- Fixed: Now correctly parses as YYmmmDD (2026-01-06)
- All 17 unit tests pass

**Iteration 1 - WebSocket URL Bug:** ✅ FIXED
- Was: `wss://trading-api.kalshi.com/trade-api/ws/v2`
- Fixed: `wss://api.elections.kalshi.com/trade-api/ws/v2`

**Iteration 1 - Private Key Format:** ✅ FIXED
- Added `get_kalshi_private_key()` function that converts `\n` to newlines

---

## Important Context Files
- **PRD:** `kalshi_nba_paper_trading_prd.md` - Complete specifications
- **Kalshi API:** `kalshi_openapi.yaml` - Kalshi API reference
- **NBA API:** `sports_openapi.yaml` - balldontlie.io API reference
- **Progress:** `PROGRESS.md` - Check what's already done (UPDATE THIS!)
- **Architecture:** `ARCHITECTURE.md` - Current state (UPDATE THIS!)

---

## Mandatory Rules

### Before You Start
1. ✅ Read PROGRESS.md to see what's already implemented
2. ✅ Check ARCHITECTURE.md to understand current system state
3. ✅ Review relevant PRD sections for specifications

### As You Work
1. ✅ Follow PRD specifications exactly - do NOT deviate
2. ✅ Use Python 3.11+ with type hints everywhere
3. ✅ Use async/await for all I/O operations (critical for WebSocket/API calls)
4. ✅ Add comprehensive docstrings and comments
5. ✅ Implement proper error handling (try/except with logging)
6. ✅ Use structured logging (not print statements)

### After You Complete
1. ✅ Update PROGRESS.md with:
   - New iteration section
   - Files created/modified
   - Status and notes
   - Any issues encountered
2. ✅ Update ARCHITECTURE.md with:
   - New components implemented
   - How to use them (code examples)
   - Current system state
   - Any architectural decisions made

---

## Tech Stack Requirements

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI with uvicorn
- **Database:** Supabase (PostgreSQL)
- **WebSocket:** python-socketio or websockets library
- **Async:** asyncio, aiohttp
- **Task Queue:** Celery + Redis (for background tasks)
- **Environment:** python-dotenv

### Key Libraries
```
fastapi==0.104.0
uvicorn[standard]==0.24.0
supabase==2.0.0
python-socketio==5.10.0
aiohttp==3.9.0
redis==5.0.0
celery==5.3.0
python-dotenv==1.0.0
pydantic==2.5.0
```

### Frontend (Phase 4 - Later)
- Next.js 14+ (App Router)
- shadcn/ui + Tailwind CSS
- Zustand (state management)
- Socket.io client

---

## Project Structure to Create

```
kalshi_nba_trading/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Environment variables & config
│   │   └── supabase.py            # Supabase client initialization
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql             # Complete database schema
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   ├── models/
│   │   ├── __init__.py
│   │   ├── game.py                # Pydantic models for data validation
│   │   ├── market.py
│   │   ├── strategy.py
│   │   └── order.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── games.py           # Game management endpoints
│   │   │   ├── strategies.py      # Strategy management endpoints
│   │   │   └── trading.py         # Trading endpoints
│   │   └── websocket.py           # WebSocket server for frontend
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── kalshi/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Kalshi REST API client
│   │   │   └── websocket.py       # Kalshi WebSocket client
│   │   └── balldontlie/
│   │       ├── __init__.py
│   │       └── client.py          # balldontlie.io API client
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py                # Base strategy class
│   │   ├── sharp_line.py          # Strategy 1
│   │   ├── momentum.py            # Strategy 2
│   │   ├── ev_multi.py            # Strategy 3
│   │   ├── mean_reversion.py      # Strategy 4
│   │   └── correlation.py         # Strategy 5
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── executor.py            # Order execution simulation
│   │   ├── position_manager.py    # Position tracking
│   │   └── pnl_calculator.py      # P&L calculation
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Logging configuration
│       └── ticker_parser.py       # Kalshi ticker parsing
├── frontend/                      # (Create in Phase 4)
├── tests/
│   ├── __init__.py
│   └── test_ticker_parser.py      # Start with unit tests
├── .env.example                   # Example environment variables
├── .gitignore
├── requirements.txt
├── README.md
├── CLAUDE.md                      # This file
├── PROGRESS.md                    # Your progress tracker
└── ARCHITECTURE.md                # Current implementation state
```

---

## Coding Standards

### Python Style
- Use Black for formatting
- Use type hints everywhere: `def func(arg: str) -> dict:`
- Docstrings in Google style
- Max line length: 100 characters

### Error Handling Pattern
```python
import logging

logger = logging.getLogger(__name__)

async def some_function():
    try:
        result = await some_async_operation()
        return result
    except SpecificException as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        raise
```

### Async Pattern
```python
# ALWAYS use async for I/O
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

---

## Database Schema Requirements

Implement ALL 12 tables from PRD Section 4.1:
1. `games` - Core game tracking
2. `kalshi_markets` - Market metadata
3. `orderbook_snapshots` - Real-time market data
4. `nba_live_data` - Live game stats
5. `betting_odds` - Sportsbook odds
6. `strategies` - Strategy configurations
7. `simulated_orders` - Order history
8. `positions` - Open/closed positions
9. `strategy_performance` - Performance metrics
10. `risk_limits` - Risk management rules
11. `system_logs` - Application logs
12. Any additional tables from PRD

**Critical:** Include ALL indexes specified in the PRD for performance.

---

## Environment Variables Template

Create `.env.example`:
```bash
# Kalshi API
KALSHI_API_URL=https://api.elections.kalshi.com/trade-api/v2
KALSHI_WS_URL=wss://trading-api.kalshi.com/trade-api/ws/v2
KALSHI_API_KEY=your_api_key_here
KALSHI_API_SECRET=your_api_secret_here

# balldontlie.io API
BALLDONTLIE_API_URL=https://api.balldontlie.io
BALLDONTLIE_API_KEY=your_api_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Redis
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

---

## Testing Requirements

For each component you build, create basic unit tests:
```python
# tests/test_ticker_parser.py
import pytest
from backend.utils.ticker_parser import extract_game_info_from_kalshi_ticker

def test_parse_valid_ticker():
    result = extract_game_info_from_kalshi_ticker("kxnbagame-26jan06dalsac")
    assert result["date"] == "2026-01-06"
    assert result["away_team_abbr"] == "DAL"
    assert result["home_team_abbr"] == "SAC"
```

---

## Success Criteria for This Session

You've succeeded when:
- ✅ Full project structure created with all directories
- ✅ Complete Supabase schema implemented (all 12 tables + indexes)
- ✅ Migration files created and documented
- ✅ FastAPI skeleton running (`uvicorn backend.main:app`)
- ✅ Configuration management setup (settings.py, .env)
- ✅ Supabase client connection working
- ✅ requirements.txt with all dependencies
- ✅ PROGRESS.md updated with Iteration 1 complete
- ✅ ARCHITECTURE.md updated with what's implemented
- ✅ Basic README.md with setup instructions

---

## Common Pitfalls to Avoid

1. ❌ Don't use synchronous I/O - ALWAYS async/await
2. ❌ Don't skip error handling - wrap everything in try/except
3. ❌ Don't use print() - use logging
4. ❌ Don't hardcode values - use environment variables
5. ❌ Don't skip type hints - Python 3.11+ requires them
6. ❌ Don't forget to update PROGRESS.md and ARCHITECTURE.md when done

---

## Next Sessions Preview

- **Session 2:** Kalshi API integration (REST + WebSocket)
- **Session 3:** balldontlie.io API integration
- **Session 4:** Implement trading strategies
- **Session 5:** Order execution engine
- **Session 6:** Frontend development

---

## Questions to Ask If Unclear

If anything is ambiguous:
1. Check the PRD first (section references provided)
2. Ask me before making assumptions
3. Document your decision in ARCHITECTURE.md

---

## Ready to Start?

Remember:
1. Read PROGRESS.md and ARCHITECTURE.md first
2. Follow PRD specifications exactly
3. Update both tracking files when complete
4. Use async/await for everything
5. Add comprehensive error handling

Let's build! 🚀

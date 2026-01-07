# Kalshi NBA Paper Trading Application

A full-stack web application for paper trading NBA prediction markets on Kalshi using live market data and comprehensive NBA statistics. The system executes multiple configurable trading strategies simultaneously and tracks their performance in real-time.

## 📋 Overview

This application integrates with:
- **Kalshi API** - Real-time prediction market orderbook data
- **balldontlie.io API** - Live NBA game statistics and betting odds
- **Supabase** - PostgreSQL database for data storage

It enables users to:
- Load NBA games by entering Kalshi market tickers
- Execute 5 different automated trading strategies
- Track simulated orders and positions
- Monitor real-time P&L across all strategies
- View performance metrics and analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase account)
- Redis (for task queue and caching)
- Kalshi API credentials
- balldontlie.io API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/johnkush50/kalshi_NBA.git
   cd kalshi_nba
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys and database credentials
   ```

5. **Setup database**
   - Create a Supabase project at https://supabase.com
   - Run the database migration:
     ```bash
     # Connect to your Supabase project and execute:
     psql -h your-project.supabase.co -U postgres -d postgres -f backend/database/schema.sql
     ```

6. **Run the application**
   ```bash
   uvicorn backend.main:app --reload
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

## 📁 Project Structure

```
kalshi_nba_trading/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── config/
│   │   ├── settings.py            # Environment configuration
│   │   └── supabase.py            # Supabase client
│   ├── database/
│   │   ├── schema.sql             # Complete database schema (11 tables)
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   ├── models/                    # Pydantic data models
│   │   ├── game.py
│   │   ├── market.py
│   │   ├── strategy.py
│   │   ├── order.py
│   │   └── position.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py          # Health check endpoints
│   │   │   ├── games.py           # Game management
│   │   │   ├── strategies.py      # Strategy configuration
│   │   │   └── trading.py         # Order execution & positions
│   │   └── websocket.py           # WebSocket server (future)
│   ├── integrations/
│   │   ├── kalshi/
│   │   │   ├── client.py          # Kalshi REST API client (skeleton)
│   │   │   └── websocket.py       # Kalshi WebSocket client (skeleton)
│   │   └── balldontlie/
│   │       └── client.py          # NBA API client (skeleton)
│   ├── strategies/
│   │   └── base.py                # Base strategy class (skeleton)
│   ├── engine/
│   │   ├── executor.py            # Order execution (skeleton)
│   │   ├── position_manager.py    # Position tracking (skeleton)
│   │   └── pnl_calculator.py      # P&L calculation (skeleton)
│   └── utils/
│       ├── logger.py              # Logging configuration
│       └── ticker_parser.py       # Kalshi ticker parsing
├── tests/
│   ├── conftest.py                # Pytest configuration
│   ├── test_ticker_parser.py      # Ticker parser tests
│   └── test_settings.py           # Settings tests
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md                      # Development instructions
├── PROGRESS.md                    # Iteration tracking
├── ARCHITECTURE.md                # System architecture
└── kalshi_nba_paper_trading_prd.md  # Complete product requirements
```

## 🗄️ Database Schema

The application uses 11 PostgreSQL tables:

1. **games** - Core game tracking with Kalshi and NBA IDs
2. **kalshi_markets** - Market metadata (ticker, type, strike value)
3. **orderbook_snapshots** - Real-time bid/ask data
4. **nba_live_data** - Live box scores (JSONB for raw data)
5. **betting_odds** - Sportsbook odds aggregation
6. **strategies** - Strategy configurations (JSONB for parameters)
7. **simulated_orders** - Order history
8. **positions** - Open/closed positions with P&L
9. **strategy_performance** - Time-series performance data
10. **risk_limits** - Risk management rules
11. **system_logs** - Application logs

See `backend/database/schema.sql` for complete schema definitions.

## 🔧 Configuration

### Environment Variables

Required variables (see `.env.example`):

```bash
# Kalshi API
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_api_secret

# balldontlie.io API
BALLDONTLIE_API_KEY=your_nba_api_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Redis (optional, for background tasks)
REDIS_URL=redis://localhost:6379
```

## 📡 API Endpoints

### Health
- `GET /api/health` - API health status
- `GET /api/health/ready` - Readiness check
- `GET /api/health/live` - Liveness check

### Games (Skeleton)
- `POST /api/games/load` - Load game from Kalshi ticker
- `GET /api/games/{game_id}` - Get game details
- `DELETE /api/games/{game_id}` - Delete game

### Strategies (Skeleton)
- `GET /api/strategies/` - List all strategies
- `POST /api/strategies/{id}/toggle` - Enable/disable strategy
- `PUT /api/strategies/{id}/config` - Update strategy config
- `GET /api/strategies/{id}/performance` - Get performance metrics

### Trading (Skeleton)
- `GET /api/trading/positions` - Get positions
- `POST /api/trading/orders/simulate` - Execute simulated order
- `POST /api/trading/positions/{id}/close` - Close position
- `GET /api/trading/pnl` - Get P&L summary

Full API documentation available at `/docs` when running.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_ticker_parser.py

# Run with verbose output
pytest -v
```

## 📈 Development Status

**✅ Iteration 1 Complete: Backend Foundation**
- [x] Project structure created
- [x] Complete database schema (11 tables)
- [x] FastAPI application skeleton
- [x] Configuration management
- [x] Pydantic models
- [x] Utilities (logger, ticker parser)
- [x] Unit tests
- [x] Documentation

**⏳ Next Steps:**
- Iteration 2: Kalshi API integration (REST + WebSocket)
- Iteration 3: balldontlie.io API integration
- Iteration 4: Implement trading strategies
- Iteration 5: Order execution engine
- Iteration 6: Frontend development (Next.js)

See `PROGRESS.md` for detailed iteration tracking.

## 🎯 Trading Strategies (Future Implementation)

1. **Sharp Line Detection** - Compare Kalshi prices to sportsbook consensus
2. **Momentum Scalping** - Exploit price lag during scoring runs
3. **EV Multi-Source** - Aggregate odds from multiple books for +EV
4. **Mean Reversion** - Bet on regression when scoring pace deviates
5. **Correlation Play** - Identify mispriced spread relationships

See `kalshi_nba_paper_trading_prd.md` for detailed strategy specifications.

## 🛠️ Tech Stack

**Backend:**
- FastAPI 0.104.0
- Python 3.11+
- Supabase (PostgreSQL)
- Redis (task queue)
- Pydantic 2.5.0 (data validation)

**Testing:**
- pytest
- pytest-asyncio
- pytest-cov

**APIs:**
- Kalshi API (prediction markets)
- balldontlie.io API (NBA data)

## 📚 Documentation

- **README.md** - This file (setup and overview)
- **CLAUDE.md** - Development instructions for Claude Code
- **PROGRESS.md** - Iteration tracking and progress log
- **ARCHITECTURE.md** - System architecture and design decisions
- **kalshi_nba_paper_trading_prd.md** - Complete product requirements (68 pages)
- **kalshi_openapi.yaml** - Kalshi API specification
- **sports_openapi.yaml** - balldontlie.io API specification

## 🤝 Contributing

This is a personal project. For issues or suggestions, please open an issue on GitHub.

## 📄 License

[Add license information]

## 🔗 Links

- **GitHub Repository**: https://github.com/johnkush50/kalshi_NBA
- **Kalshi API Docs**: https://trading-api.readme.io/
- **balldontlie.io API**: https://www.balldontlie.io/
- **Supabase**: https://supabase.com/

## 💡 Tips

- Check `PROGRESS.md` to see what's implemented and what's next
- Review `ARCHITECTURE.md` for system design decisions
- See `kalshi_nba_paper_trading_prd.md` for complete specifications
- Use `/docs` endpoint for interactive API testing
- Run `pytest -v` to verify all tests pass

---

**Status**: ✅ Iteration 1 Complete - Backend Foundation Ready
**Last Updated**: January 2026

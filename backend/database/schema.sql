-- Kalshi NBA Paper Trading Database Schema
-- Complete schema for all 12 tables with indexes and constraints
-- PostgreSQL / Supabase compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE 1: games
-- Core game tracking with Kalshi event and NBA game IDs
-- ============================================================================
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kalshi_event_ticker VARCHAR(100) UNIQUE NOT NULL,
    kalshi_market_ticker_seed VARCHAR(100) NOT NULL, -- Initial ticker entered by user
    nba_game_id INTEGER UNIQUE,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    home_team_id INTEGER,
    away_team_id INTEGER,
    game_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'live', 'finished'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_date ON games(game_date);

-- ============================================================================
-- TABLE 2: kalshi_markets
-- Market metadata for all Kalshi markets related to a game
-- ============================================================================
CREATE TABLE IF NOT EXISTS kalshi_markets (
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
CREATE INDEX idx_kalshi_markets_type ON kalshi_markets(market_type);

-- ============================================================================
-- TABLE 3: orderbook_snapshots
-- Real-time orderbook data from Kalshi WebSocket
-- ============================================================================
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
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

-- ============================================================================
-- TABLE 4: nba_live_data
-- Live NBA game statistics from balldontlie.io
-- ============================================================================
CREATE TABLE IF NOT EXISTS nba_live_data (
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

-- ============================================================================
-- TABLE 5: betting_odds
-- Sportsbook odds aggregation from balldontlie.io
-- ============================================================================
CREATE TABLE IF NOT EXISTS betting_odds (
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
CREATE INDEX idx_betting_odds_vendor ON betting_odds(vendor);

-- ============================================================================
-- TABLE 6: strategies
-- Trading strategy configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'sharp_line', 'momentum', 'ev_multi', 'mean_reversion', 'correlation'
    is_enabled BOOLEAN DEFAULT false,
    config JSONB NOT NULL, -- Strategy-specific parameters
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_strategies_enabled ON strategies(is_enabled);
CREATE INDEX idx_strategies_type ON strategies(type);

-- ============================================================================
-- TABLE 7: simulated_orders
-- Order history for all simulated trades
-- ============================================================================
CREATE TABLE IF NOT EXISTS simulated_orders (
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
CREATE INDEX idx_orders_status ON simulated_orders(status);

-- ============================================================================
-- TABLE 8: positions
-- Open and closed positions with P&L tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
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
CREATE INDEX idx_positions_game ON positions(game_id);

-- ============================================================================
-- TABLE 9: strategy_performance
-- Time-series performance metrics for each strategy
-- ============================================================================
CREATE TABLE IF NOT EXISTS strategy_performance (
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

-- ============================================================================
-- TABLE 10: risk_limits
-- Risk management rules per strategy
-- ============================================================================
CREATE TABLE IF NOT EXISTS risk_limits (
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

CREATE INDEX idx_risk_limits_strategy ON risk_limits(strategy_id);

-- ============================================================================
-- TABLE 11: system_logs
-- Application logs for monitoring and debugging
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error', 'critical'
    component VARCHAR(50) NOT NULL, -- 'kalshi_ws', 'nba_api', 'strategy_engine', etc.
    message TEXT NOT NULL,
    metadata JSONB
);

CREATE INDEX idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_component ON system_logs(component);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to games table
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to strategies table
CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to positions table
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to risk_limits table
CREATE TRIGGER update_risk_limits_updated_at BEFORE UPDATE ON risk_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Notes:
-- - All 11 core tables implemented with proper indexes
-- - Foreign key constraints with CASCADE/SET NULL as appropriate
-- - JSONB fields for flexible data storage
-- - Automatic timestamp triggers
-- - Ready for Supabase deployment

/**
 * TypeScript types matching backend API responses
 *
 * These types are derived from the backend Pydantic models
 * and API response structures.
 */

// ============================================================================
// Games & Aggregator Types
// ============================================================================

export interface MarketOrderbook {
  yes_bid: number | null
  yes_ask: number | null
  no_bid: number | null
  no_ask: number | null
  mid_price: number | null
  spread: number | null
  volume: number
  last_updated: string | null
}

export interface MarketState {
  ticker: string
  market_type: 'moneyline' | 'spread' | 'total'
  team_abbr: string | null
  spread_value: number | null
  total_value: number | null
  status: string
  orderbook: MarketOrderbook | null
}

export interface ConsensusOdds {
  home_win_probability: number | null
  away_win_probability: number | null
  spread_home: number | null
  total: number | null
  num_sportsbooks: number
}

export interface SportsbookOdds {
  vendor: string
  moneyline_home: number | null
  moneyline_away: number | null
  spread_home_value: number | null
  spread_home_odds: number | null
  total_value: number | null
  total_over_odds: number | null
  total_under_odds: number | null
  timestamp: string
}

export interface NbaLiveData {
  period: number
  time_remaining: string
  home_score: number
  away_score: number
  game_status: string
  timestamp: string
}

export interface GameState {
  game_id: string
  event_ticker: string
  home_team: string
  away_team: string
  game_date: string
  status: 'scheduled' | 'live' | 'finished'
  has_nba_data: boolean
  nba_game_id: number | null
  markets: Record<string, MarketState>
  consensus: ConsensusOdds | null
  odds: SportsbookOdds[]
  nba_live: NbaLiveData | null
  last_updated: string
}

export interface LoadedGamesResponse {
  count: number
  games: Record<string, GameState>
}

export interface AvailableGame {
  index: number
  away_team: string
  home_team: string
  event_ticker: string
  title: string
  game_date: string
  market_count: number
  market_types: string[]
}

export interface AvailableGamesResponse {
  date: string
  game_count: number
  games: AvailableGame[]
}

export interface LoadGameResponse {
  status: string
  message: string
  game_state?: GameState
}

// ============================================================================
// Strategy Types
// ============================================================================

export interface StrategyType {
  type: string
  name: string
  description: string
  default_config: Record<string, unknown>
}

export interface Strategy {
  strategy_id: string
  strategy_type: string
  strategy_name: string
  is_enabled: boolean
  config: Record<string, unknown>
}

export interface StrategiesResponse {
  strategies: Strategy[]
  count: number
}

export interface StrategyTypesResponse {
  strategy_types: StrategyType[]
}

export interface Signal {
  id: string
  strategy_id: string
  strategy_name: string
  market_ticker: string
  side: 'yes' | 'no'
  quantity: number
  confidence: number
  reason: string
  timestamp: string
  game_id?: string
}

export interface StrategyWithSignals extends Strategy {
  recent_signals: Signal[]
}

// ============================================================================
// Execution Types
// ============================================================================

export interface ExecutionStats {
  total_orders: number
  filled_orders: number
  rejected_orders: number
  open_positions: number
  total_volume: number
}

export interface Position {
  id?: string
  market_ticker: string
  game_id?: string
  side: 'yes' | 'no'
  quantity: number
  avg_entry_price: number
  total_cost: number
  unrealized_pnl?: number
  realized_pnl?: number
  is_open?: boolean
}

export interface PositionsResponse {
  count: number
  positions: Position[] | Record<string, Position>
}

export interface Order {
  id: string
  strategy_id: string | null
  strategy_name?: string
  game_id: string
  market_id: string | null
  market_ticker: string
  order_type: string
  side: 'yes' | 'no'
  quantity: number
  limit_price: number | null
  filled_price: number | null
  status: 'pending' | 'filled' | 'rejected' | 'cancelled'
  placed_at: string
  filled_at: string | null
  signal_data: Record<string, unknown> | null
  created_at: string
}

export interface OrdersResponse {
  count: number
  orders: Order[]
}

export interface ManualOrderRequest {
  game_id: string
  market_ticker: string
  side: 'yes' | 'no'
  quantity: number
  reason?: string
}

export interface ClosePositionResponse {
  status: string
  market_ticker: string
  realized_pnl: number
  position: {
    side: string
    quantity: number
    avg_entry: number
    realized_pnl: number
  }
}

// ============================================================================
// P&L Types
// ============================================================================

export interface PortfolioPnL {
  total_pnl: number
  unrealized_pnl: number
  realized_pnl: number
  total_cost: number
  open_positions: number
}

export interface StrategyPerformance {
  total_orders: number
  filled_orders: number
  rejected_orders: number
  total_volume: number
  win_count: number
  loss_count: number
  win_rate: number
  total_profit: number
  total_loss: number
  profit_factor: number
  avg_win: number
  avg_loss: number
}

export interface PerformanceResponse {
  order_stats: StrategyPerformance
  portfolio: PortfolioPnL
}

// ============================================================================
// Risk Types
// ============================================================================

export interface RiskStatus {
  enabled: boolean
  daily_loss: number
  weekly_loss: number
  orders_today: number
  orders_this_hour: number
  loss_streak: number
  in_cooldown: boolean
  cooldown_ends_at: string | null
  total_exposure: number
  last_reset: string
}

export interface RiskLimits {
  limits: Record<string, number>
  enabled: boolean
}

export interface SetLimitRequest {
  limit_type: string
  value: number
}

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WebSocketMessage {
  type: 'signal' | 'order_filled' | 'order_rejected' | 'pnl_update' | 'market_update' | 'nba_update'
  data: unknown
  timestamp: string
}

// ============================================================================
// MOCK DATA - Kalshi NBA Paper Trading Dashboard
// All data is hardcoded for static UI demonstration
// ============================================================================

// ----- GAMES DATA -----

export interface Market {
  ticker: string;
  type: 'moneyline' | 'spread' | 'total';
  name: string;
  yesBid: number;
  yesAsk: number;
  spread: number;
  volume: number;
}

export interface GameOdds {
  vendor: string;
  homeOdds: number;
  awayOdds: number;
  spread: number;
  total: number;
}

export interface ActiveGame {
  id: string;
  eventTicker: string;
  homeTeam: string;
  awayTeam: string;
  homeAbbr: string;
  awayAbbr: string;
  gameTime: string;
  status: 'scheduled' | 'live' | 'finished';
  homeScore?: number;
  awayScore?: number;
  period?: string;
  markets: Market[];
  consensusOdds: GameOdds[];
}

export const activeGames: ActiveGame[] = [
  {
    id: 'game-001',
    eventTicker: 'KXNBAGAME-26JAN15MILLAL',
    homeTeam: 'Los Angeles Lakers',
    awayTeam: 'Milwaukee Bucks',
    homeAbbr: 'LAL',
    awayAbbr: 'MIL',
    gameTime: '2026-01-15T19:30:00Z',
    status: 'live',
    homeScore: 54,
    awayScore: 61,
    period: 'Q3 8:42',
    markets: [
      { ticker: 'KXNBAGAME-26JAN15MILLAL-LAL', type: 'moneyline', name: 'Lakers ML', yesBid: 42, yesAsk: 44, spread: 2, volume: 15420 },
      { ticker: 'KXNBAGAME-26JAN15MILLAL-MIL', type: 'moneyline', name: 'Bucks ML', yesBid: 56, yesAsk: 58, spread: 2, volume: 14890 },
      { ticker: 'KXNBASPREAD-26JAN15MILLAL-LAL3', type: 'spread', name: 'Lakers +3.5', yesBid: 48, yesAsk: 51, spread: 3, volume: 8750 },
      { ticker: 'KXNBASPREAD-26JAN15MILLAL-MIL3', type: 'spread', name: 'Bucks -3.5', yesBid: 49, yesAsk: 52, spread: 3, volume: 8230 },
      { ticker: 'KXNBATOTAL-26JAN15MILLAL-O225', type: 'total', name: 'Over 225.5', yesBid: 52, yesAsk: 54, spread: 2, volume: 6120 },
      { ticker: 'KXNBATOTAL-26JAN15MILLAL-U225', type: 'total', name: 'Under 225.5', yesBid: 46, yesAsk: 48, spread: 2, volume: 5980 },
    ],
    consensusOdds: [
      { vendor: 'FanDuel', homeOdds: -125, awayOdds: +105, spread: 2.5, total: 226.5 },
      { vendor: 'DraftKings', homeOdds: -130, awayOdds: +110, spread: 3.0, total: 225.5 },
      { vendor: 'BetMGM', homeOdds: -120, awayOdds: +100, spread: 2.5, total: 227.0 },
    ],
  },
  {
    id: 'game-002',
    eventTicker: 'KXNBAGAME-26JAN15BOSNYK',
    homeTeam: 'New York Knicks',
    awayTeam: 'Boston Celtics',
    homeAbbr: 'NYK',
    awayAbbr: 'BOS',
    gameTime: '2026-01-15T22:00:00Z',
    status: 'scheduled',
    markets: [
      { ticker: 'KXNBAGAME-26JAN15BOSNYK-NYK', type: 'moneyline', name: 'Knicks ML', yesBid: 38, yesAsk: 40, spread: 2, volume: 22100 },
      { ticker: 'KXNBAGAME-26JAN15BOSNYK-BOS', type: 'moneyline', name: 'Celtics ML', yesBid: 60, yesAsk: 62, spread: 2, volume: 21850 },
      { ticker: 'KXNBASPREAD-26JAN15BOSNYK-NYK5', type: 'spread', name: 'Knicks +5.5', yesBid: 51, yesAsk: 53, spread: 2, volume: 12300 },
      { ticker: 'KXNBASPREAD-26JAN15BOSNYK-BOS5', type: 'spread', name: 'Celtics -5.5', yesBid: 47, yesAsk: 49, spread: 2, volume: 11980 },
    ],
    consensusOdds: [
      { vendor: 'FanDuel', homeOdds: +165, awayOdds: -195, spread: -5.5, total: 218.0 },
      { vendor: 'DraftKings', homeOdds: +160, awayOdds: -190, spread: -5.0, total: 217.5 },
      { vendor: 'BetMGM', homeOdds: +170, awayOdds: -200, spread: -5.5, total: 218.5 },
    ],
  },
];

export interface AvailableGame {
  eventTicker: string;
  homeTeam: string;
  awayTeam: string;
  homeAbbr: string;
  awayAbbr: string;
  gameTime: string;
  marketCount: number;
}

export const availableGames: AvailableGame[] = [
  { eventTicker: 'KXNBAGAME-26JAN15PHXDEN', homeTeam: 'Denver Nuggets', awayTeam: 'Phoenix Suns', homeAbbr: 'DEN', awayAbbr: 'PHX', gameTime: '2026-01-15T21:00:00Z', marketCount: 8 },
  { eventTicker: 'KXNBAGAME-26JAN15GSWSAC', homeTeam: 'Sacramento Kings', awayTeam: 'Golden State Warriors', homeAbbr: 'SAC', awayAbbr: 'GSW', gameTime: '2026-01-15T22:00:00Z', marketCount: 6 },
  { eventTicker: 'KXNBAGAME-26JAN15DALHOU', homeTeam: 'Houston Rockets', awayTeam: 'Dallas Mavericks', homeAbbr: 'HOU', awayAbbr: 'DAL', gameTime: '2026-01-15T20:00:00Z', marketCount: 8 },
  { eventTicker: 'KXNBAGAME-26JAN15MIACHI', homeTeam: 'Chicago Bulls', awayTeam: 'Miami Heat', homeAbbr: 'CHI', awayAbbr: 'MIA', gameTime: '2026-01-15T20:30:00Z', marketCount: 6 },
  { eventTicker: 'KXNBAGAME-26JAN15ATLORL', homeTeam: 'Orlando Magic', awayTeam: 'Atlanta Hawks', homeAbbr: 'ORL', awayAbbr: 'ATL', gameTime: '2026-01-15T19:00:00Z', marketCount: 6 },
];

// ----- STRATEGIES DATA -----

export interface Strategy {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  signalCount: number;
  lastEvaluation: string;
  config: Record<string, unknown>;
}

export const strategies: Strategy[] = [
  {
    id: 'strat-001',
    name: 'Sharp Line Detection',
    type: 'sharp_line',
    enabled: true,
    signalCount: 12,
    lastEvaluation: '2026-01-15T14:32:18Z',
    config: {
      threshold_percent: 5.0,
      min_sample_sportsbooks: 3,
      position_size: 10,
      cooldown_minutes: 5,
      min_ev_percent: 2.0,
      market_types: ['moneyline'],
    },
  },
  {
    id: 'strat-002',
    name: 'Momentum Scalping',
    type: 'momentum',
    enabled: true,
    signalCount: 8,
    lastEvaluation: '2026-01-15T14:32:18Z',
    config: {
      lookback_seconds: 120,
      min_price_change_cents: 5,
      position_size: 10,
      cooldown_minutes: 3,
      max_spread_cents: 3,
    },
  },
  {
    id: 'strat-003',
    name: 'EV Multi-Book Arbitrage',
    type: 'ev_multibook',
    enabled: false,
    signalCount: 3,
    lastEvaluation: '2026-01-15T14:30:05Z',
    config: {
      min_ev_percent: 3.0,
      min_sportsbooks_agreeing: 2,
      position_size: 10,
      cooldown_minutes: 5,
    },
  },
  {
    id: 'strat-004',
    name: 'Mean Reversion',
    type: 'mean_reversion',
    enabled: true,
    signalCount: 5,
    lastEvaluation: '2026-01-15T14:32:18Z',
    config: {
      min_reversion_percent: 15.0,
      max_reversion_percent: 40.0,
      min_time_remaining_pct: 25.0,
      only_first_half: true,
    },
  },
  {
    id: 'strat-005',
    name: 'Cross-Market Correlation',
    type: 'correlation',
    enabled: false,
    signalCount: 2,
    lastEvaluation: '2026-01-15T14:28:45Z',
    config: {
      min_discrepancy_percent: 5.0,
      complementary_max_sum: 105.0,
      check_complementary: true,
      check_moneyline_spread: true,
    },
  },
];

export interface Signal {
  id: string;
  strategyId: string;
  strategyName: string;
  marketTicker: string;
  side: 'YES' | 'NO';
  quantity: number;
  confidence: number;
  reason: string;
  timestamp: string;
  executed: boolean;
}

export const recentSignals: Signal[] = [
  {
    id: 'sig-001',
    strategyId: 'strat-001',
    strategyName: 'Sharp Line',
    marketTicker: 'KXNBAGAME-26JAN15MILLAL-LAL',
    side: 'YES',
    quantity: 10,
    confidence: 0.82,
    reason: 'Kalshi undervalued by 6.2% vs consensus. FanDuel/DraftKings agree.',
    timestamp: '2026-01-15T14:32:18Z',
    executed: true,
  },
  {
    id: 'sig-002',
    strategyId: 'strat-002',
    strategyName: 'Momentum',
    marketTicker: 'KXNBAGAME-26JAN15MILLAL-MIL',
    side: 'YES',
    quantity: 10,
    confidence: 0.75,
    reason: 'Price moved +4¢ in 90 seconds. Following upward momentum.',
    timestamp: '2026-01-15T14:30:45Z',
    executed: true,
  },
  {
    id: 'sig-003',
    strategyId: 'strat-004',
    strategyName: 'Mean Reversion',
    marketTicker: 'KXNBAGAME-26JAN15MILLAL-LAL',
    side: 'YES',
    quantity: 10,
    confidence: 0.68,
    reason: 'Lakers dropped 18% from pregame. Q3 swing expected.',
    timestamp: '2026-01-15T14:28:12Z',
    executed: false,
  },
  {
    id: 'sig-004',
    strategyId: 'strat-001',
    strategyName: 'Sharp Line',
    marketTicker: 'KXNBAGAME-26JAN15BOSNYK-BOS',
    side: 'NO',
    quantity: 10,
    confidence: 0.71,
    reason: 'Celtics overpriced by 4.8%. Sell the hype.',
    timestamp: '2026-01-15T14:25:33Z',
    executed: true,
  },
  {
    id: 'sig-005',
    strategyId: 'strat-002',
    strategyName: 'Momentum',
    marketTicker: 'KXNBATOTAL-26JAN15MILLAL-O225',
    side: 'YES',
    quantity: 5,
    confidence: 0.65,
    reason: 'Over price rising +3¢. Fast-paced Q3.',
    timestamp: '2026-01-15T14:22:08Z',
    executed: true,
  },
];

// ----- TRADING DATA -----

export interface Position {
  id: string;
  marketTicker: string;
  marketName: string;
  side: 'YES' | 'NO';
  quantity: number;
  avgEntryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  costBasis: number;
}

export const openPositions: Position[] = [
  {
    id: 'pos-001',
    marketTicker: 'KXNBAGAME-26JAN15MILLAL-LAL',
    marketName: 'Lakers ML',
    side: 'YES',
    quantity: 20,
    avgEntryPrice: 41,
    currentPrice: 44,
    unrealizedPnl: 60,
    unrealizedPnlPercent: 7.32,
    costBasis: 820,
  },
  {
    id: 'pos-002',
    marketTicker: 'KXNBAGAME-26JAN15MILLAL-MIL',
    marketName: 'Bucks ML',
    side: 'YES',
    quantity: 15,
    avgEntryPrice: 55,
    currentPrice: 58,
    unrealizedPnl: 45,
    unrealizedPnlPercent: 5.45,
    costBasis: 825,
  },
  {
    id: 'pos-003',
    marketTicker: 'KXNBAGAME-26JAN15BOSNYK-BOS',
    marketName: 'Celtics ML',
    side: 'NO',
    quantity: 10,
    avgEntryPrice: 38,
    currentPrice: 40,
    unrealizedPnl: -20,
    unrealizedPnlPercent: -5.26,
    costBasis: 380,
  },
];

export interface Order {
  id: string;
  timestamp: string;
  marketTicker: string;
  marketName: string;
  side: 'YES' | 'NO';
  quantity: number;
  fillPrice: number;
  status: 'filled' | 'rejected' | 'cancelled' | 'pending';
  strategyId?: string;
  strategyName?: string;
}

export const orderHistory: Order[] = [
  { id: 'ord-001', timestamp: '2026-01-15T14:32:20Z', marketTicker: 'KXNBAGAME-26JAN15MILLAL-LAL', marketName: 'Lakers ML', side: 'YES', quantity: 10, fillPrice: 44, status: 'filled', strategyId: 'strat-001', strategyName: 'Sharp Line' },
  { id: 'ord-002', timestamp: '2026-01-15T14:30:47Z', marketTicker: 'KXNBAGAME-26JAN15MILLAL-MIL', marketName: 'Bucks ML', side: 'YES', quantity: 10, fillPrice: 57, status: 'filled', strategyId: 'strat-002', strategyName: 'Momentum' },
  { id: 'ord-003', timestamp: '2026-01-15T14:28:15Z', marketTicker: 'KXNBAGAME-26JAN15MILLAL-LAL', marketName: 'Lakers ML', side: 'YES', quantity: 10, fillPrice: 41, status: 'filled', strategyId: 'strat-004', strategyName: 'Mean Reversion' },
  { id: 'ord-004', timestamp: '2026-01-15T14:25:35Z', marketTicker: 'KXNBAGAME-26JAN15BOSNYK-BOS', marketName: 'Celtics ML', side: 'NO', quantity: 10, fillPrice: 38, status: 'filled', strategyId: 'strat-001', strategyName: 'Sharp Line' },
  { id: 'ord-005', timestamp: '2026-01-15T14:22:10Z', marketTicker: 'KXNBATOTAL-26JAN15MILLAL-O225', marketName: 'Over 225.5', side: 'YES', quantity: 5, fillPrice: 53, status: 'filled', strategyId: 'strat-002', strategyName: 'Momentum' },
  { id: 'ord-006', timestamp: '2026-01-15T14:18:30Z', marketTicker: 'KXNBAGAME-26JAN15MILLAL-MIL', marketName: 'Bucks ML', side: 'YES', quantity: 5, fillPrice: 54, status: 'filled' },
  { id: 'ord-007', timestamp: '2026-01-15T14:15:22Z', marketTicker: 'KXNBASPREAD-26JAN15MILLAL-LAL3', marketName: 'Lakers +3.5', side: 'NO', quantity: 10, fillPrice: 0, status: 'rejected' },
  { id: 'ord-008', timestamp: '2026-01-15T14:12:08Z', marketTicker: 'KXNBAGAME-26JAN15BOSNYK-NYK', marketName: 'Knicks ML', side: 'YES', quantity: 10, fillPrice: 39, status: 'filled' },
  { id: 'ord-009', timestamp: '2026-01-15T14:08:45Z', marketTicker: 'KXNBATOTAL-26JAN15BOSNYK-U218', marketName: 'Under 218', side: 'YES', quantity: 5, fillPrice: 0, status: 'cancelled' },
  { id: 'ord-010', timestamp: '2026-01-15T14:05:12Z', marketTicker: 'KXNBASPREAD-26JAN15BOSNYK-NYK5', marketName: 'Knicks +5.5', side: 'YES', quantity: 10, fillPrice: 51, status: 'filled' },
];

// ----- P&L DATA -----

export interface PnLSummary {
  totalPnl: number;
  unrealizedPnl: number;
  realizedPnl: number;
  totalCost: number;
  tradingVolume: number;
  totalOrders: number;
  openPositionCount: number;
  winRate: number;
  profitFactor: number;
}

export const pnlSummary: PnLSummary = {
  totalPnl: 285,
  unrealizedPnl: 85,
  realizedPnl: 200,
  totalCost: 2025,
  tradingVolume: 4850,
  totalOrders: 10,
  openPositionCount: 3,
  winRate: 72.5,
  profitFactor: 2.4,
};

// ----- RISK DATA -----

export interface RiskStatus {
  enabled: boolean;
  dailyLoss: number;
  weeklyLoss: number;
  ordersToday: number;
  ordersThisHour: number;
  lossStreak: number;
  inCooldown: boolean;
  cooldownEndsAt?: string;
  totalExposure: number;
}

export const riskStatus: RiskStatus = {
  enabled: true,
  dailyLoss: 120,
  weeklyLoss: 340,
  ordersToday: 10,
  ordersThisHour: 4,
  lossStreak: 1,
  inCooldown: false,
  totalExposure: 2025,
};

export interface RiskLimit {
  type: string;
  name: string;
  value: number;
  description: string;
  unit: string;
}

export const riskLimits: RiskLimit[] = [
  { type: 'max_contracts_per_market', name: 'Max Contracts/Market', value: 100, description: 'Maximum contracts allowed in a single market', unit: 'contracts' },
  { type: 'max_contracts_per_game', name: 'Max Contracts/Game', value: 200, description: 'Maximum contracts across all markets for one game', unit: 'contracts' },
  { type: 'max_total_contracts', name: 'Max Total Contracts', value: 500, description: 'Maximum total open contracts across all positions', unit: 'contracts' },
  { type: 'max_daily_loss', name: 'Max Daily Loss', value: 1000, description: 'Maximum loss allowed per day before trading stops', unit: '¢' },
  { type: 'max_weekly_loss', name: 'Max Weekly Loss', value: 5000, description: 'Maximum loss allowed per week before trading stops', unit: '¢' },
  { type: 'max_per_trade_risk', name: 'Max Per-Trade Risk', value: 500, description: 'Maximum risk exposure per individual trade', unit: '¢' },
  { type: 'max_total_exposure', name: 'Max Total Exposure', value: 10000, description: 'Maximum total capital at risk', unit: '¢' },
  { type: 'max_exposure_per_game', name: 'Max Exposure/Game', value: 2000, description: 'Maximum exposure per game', unit: '¢' },
  { type: 'max_exposure_per_strategy', name: 'Max Exposure/Strategy', value: 3000, description: 'Maximum exposure per strategy', unit: '¢' },
  { type: 'max_orders_per_day', name: 'Max Orders/Day', value: 50, description: 'Maximum orders allowed per day', unit: 'orders' },
  { type: 'max_orders_per_hour', name: 'Max Orders/Hour', value: 20, description: 'Maximum orders allowed per hour', unit: 'orders' },
  { type: 'loss_streak_cooldown', name: 'Loss Streak Cooldown', value: 3, description: 'Consecutive losses before 5-min pause', unit: 'losses' },
];

// ----- CONNECTION STATUS -----

export interface ConnectionStatus {
  backend: 'connected' | 'disconnected' | 'connecting';
  websocket: 'connected' | 'disconnected' | 'connecting';
  kalshi: 'connected' | 'disconnected' | 'connecting';
  lastUpdate: string;
}

export const connectionStatus: ConnectionStatus = {
  backend: 'connected',
  websocket: 'connected',
  kalshi: 'connected',
  lastUpdate: '2026-01-15T14:32:45Z',
};

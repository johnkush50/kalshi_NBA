# Frontend API Integration Guide

This document maps all UI components to their corresponding backend API endpoints.
Use this checklist when connecting the static frontend to the live backend.

---

## Games Page (`/`)

### Data Displayed

- [ ] **Active games list** - `GET /api/aggregator/states`
- [ ] **Game details & markets** - `GET /api/aggregator/state/{game_id}`
- [ ] **Available games for date** - `GET /api/games/available?date=YYYY-MM-DD`
- [ ] **Consensus odds per game** - Included in aggregator state response
- [ ] **Market bid/ask prices** - Included in aggregator state response

### User Actions

- [ ] **Load game** - `POST /api/aggregator/load/{game_id}`
- [ ] **Unload game** - `POST /api/aggregator/unload/{game_id}`
- [ ] **Refresh all games** - Call `GET /api/aggregator/states` again
- [ ] **Search games by date** - `GET /api/games/available?date=YYYY-MM-DD`
- [ ] **Place order (Buy Yes/No)** - `POST /api/execution/execute/manual`
  ```json
  {
    "game_id": "uuid",
    "market_ticker": "KXNBAGAME-...",
    "side": "yes" | "no",
    "quantity": 10
  }
  ```

---

## Strategies Page (`/strategies`)

### Data Displayed

- [ ] **Available strategy types** - `GET /api/strategies/types`
- [ ] **Loaded strategies list** - `GET /api/strategies/`
- [ ] **Strategy configuration** - Included in strategies response
- [ ] **Strategy signal count** - Included in strategies response
- [ ] **Live signals feed** - WebSocket channel `signals`

### User Actions

- [ ] **Load new strategy** - `POST /api/strategies/load`
  ```json
  {
    "strategy_type": "sharp_line",
    "config": { ... },
    "enable": true
  }
  ```
- [ ] **Enable strategy** - `POST /api/strategies/{id}/enable`
- [ ] **Disable strategy** - `POST /api/strategies/{id}/disable`
- [ ] **Update config** - `PUT /api/strategies/{id}/config`

---

## Trading Page (`/trading`)

### Data Displayed

- [ ] **Open positions** - `GET /api/execution/positions/open`
- [ ] **All positions** - `GET /api/execution/positions`
- [ ] **Order history** - `GET /api/execution/orders`
- [ ] **Position P&L** - Calculated from positions data or `GET /api/execution/pnl`

### User Actions

- [ ] **Close position** - `POST /api/execution/positions/{ticker}/close`
  ```json
  {
    "exit_price": 55  // Optional, uses market bid if omitted
  }
  ```
- [ ] **Refresh positions** - Call `GET /api/execution/positions/open` again

---

## P&L Page (`/pnl`)

### Data Displayed

- [ ] **Portfolio P&L summary** - `GET /api/execution/pnl`
  - Total P&L
  - Unrealized P&L
  - Realized P&L
  - Total cost basis
- [ ] **Trading performance** - `GET /api/execution/performance`
  - Win rate
  - Profit factor
  - Total orders
  - Volume
- [ ] **Position breakdown** - `GET /api/execution/positions`

### User Actions

- [ ] **Refresh P&L** - `POST /api/execution/pnl/refresh`
- [ ] **Close position from table** - `POST /api/execution/positions/{ticker}/close`

---

## Risk Page (`/risk`)

### Data Displayed

- [ ] **Risk status** - `GET /api/risk/status`
  - enabled/disabled
  - Daily loss
  - Weekly loss
  - Orders today
  - Orders this hour
  - Loss streak count
  - Cooldown status
  - Total exposure
- [ ] **Risk limits** - `GET /api/risk/limits`
  - All 12 limit types with current values

### User Actions

- [ ] **Enable risk management** - `POST /api/risk/enable`
- [ ] **Disable risk management** - `POST /api/risk/disable`
- [ ] **Update limit** - `PUT /api/risk/limits`
  ```json
  {
    "limit_type": "max_daily_loss",
    "value": 2000
  }
  ```
- [ ] **Reset counters** - `POST /api/risk/reset`

---

## Header Component

### Data Displayed

- [ ] **Backend connection status** - Health check `GET /health`
- [ ] **WebSocket connection status** - WebSocket connected event
- [ ] **Kalshi connection status** - Included in health or status endpoint
- [ ] **Total P&L** - `GET /api/execution/pnl` (totalPnl field)
- [ ] **Position count** - `GET /api/execution/positions/open` (array length)
- [ ] **Orders today** - `GET /api/execution/stats` or from orders count

---

## WebSocket Integration

### Connection

```typescript
const ws = new WebSocket('ws://localhost:8000/ws?channels=all');
```

### Channels

- [ ] **`orderbook`** - Market price updates
  - Update market bid/ask prices in Games page
  - Trigger P&L recalculation

- [ ] **`nba`** - NBA game score updates
  - Update game scores in Games page
  - Update game status (live/finished)

- [ ] **`signals`** - Trading signal notifications
  - Append to live signals feed on Strategies page
  - Show notification/toast

- [ ] **`orders`** - Order execution updates
  - Append to order history on Trading page
  - Update header order count

- [ ] **`positions`** - Position changes
  - Update positions table
  - Update P&L values

### Message Format

```typescript
interface WebSocketMessage {
  type: 'orderbook_update' | 'nba_update' | 'signal' | 'order' | 'position_update';
  data: unknown;
  timestamp: string;
}
```

---

## Recommended State Management

Use Zustand stores for:

```typescript
// stores/games.ts
interface GamesStore {
  activeGames: ActiveGame[];
  availableGames: AvailableGame[];
  fetchActiveGames: () => Promise<void>;
  loadGame: (id: string) => Promise<void>;
  unloadGame: (id: string) => Promise<void>;
}

// stores/strategies.ts
interface StrategiesStore {
  strategies: Strategy[];
  signals: Signal[];
  fetchStrategies: () => Promise<void>;
  enableStrategy: (id: string) => Promise<void>;
  disableStrategy: (id: string) => Promise<void>;
  addSignal: (signal: Signal) => void;
}

// stores/trading.ts
interface TradingStore {
  positions: Position[];
  orders: Order[];
  fetchPositions: () => Promise<void>;
  fetchOrders: () => Promise<void>;
  closePosition: (ticker: string) => Promise<void>;
}

// stores/pnl.ts
interface PnLStore {
  summary: PnLSummary | null;
  performance: Performance | null;
  fetchPnL: () => Promise<void>;
  refreshPnL: () => Promise<void>;
}

// stores/risk.ts
interface RiskStore {
  status: RiskStatus | null;
  limits: RiskLimit[];
  fetchStatus: () => Promise<void>;
  fetchLimits: () => Promise<void>;
  updateLimit: (type: string, value: number) => Promise<void>;
  toggleRisk: (enable: boolean) => Promise<void>;
}

// stores/connection.ts
interface ConnectionStore {
  backendStatus: 'connected' | 'disconnected' | 'connecting';
  wsStatus: 'connected' | 'disconnected' | 'connecting';
  connect: () => void;
  disconnect: () => void;
}
```

---

## API Client Setup

```typescript
// lib/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Games
  getActiveGames: () => apiFetch('/api/aggregator/states'),
  getGameState: (id: string) => apiFetch(`/api/aggregator/state/${id}`),
  getAvailableGames: (date: string) => apiFetch(`/api/games/available?date=${date}`),
  loadGame: (id: string) => apiFetch(`/api/aggregator/load/${id}`, { method: 'POST' }),
  unloadGame: (id: string) => apiFetch(`/api/aggregator/unload/${id}`, { method: 'POST' }),

  // Strategies
  getStrategyTypes: () => apiFetch('/api/strategies/types'),
  getStrategies: () => apiFetch('/api/strategies/'),
  loadStrategy: (data: unknown) => apiFetch('/api/strategies/load', { method: 'POST', body: JSON.stringify(data) }),
  enableStrategy: (id: string) => apiFetch(`/api/strategies/${id}/enable`, { method: 'POST' }),
  disableStrategy: (id: string) => apiFetch(`/api/strategies/${id}/disable`, { method: 'POST' }),

  // Execution
  getStats: () => apiFetch('/api/execution/stats'),
  getOrders: () => apiFetch('/api/execution/orders'),
  getPositions: () => apiFetch('/api/execution/positions'),
  getOpenPositions: () => apiFetch('/api/execution/positions/open'),
  executeOrder: (data: unknown) => apiFetch('/api/execution/execute/manual', { method: 'POST', body: JSON.stringify(data) }),

  // P&L
  getPnL: () => apiFetch('/api/execution/pnl'),
  refreshPnL: () => apiFetch('/api/execution/pnl/refresh', { method: 'POST' }),
  closePosition: (ticker: string, exitPrice?: number) => apiFetch(`/api/execution/positions/${ticker}/close`, {
    method: 'POST',
    body: JSON.stringify({ exit_price: exitPrice }),
  }),
  getPerformance: () => apiFetch('/api/execution/performance'),

  // Risk
  getRiskStatus: () => apiFetch('/api/risk/status'),
  getRiskLimits: () => apiFetch('/api/risk/limits'),
  setRiskLimit: (data: unknown) => apiFetch('/api/risk/limits', { method: 'PUT', body: JSON.stringify(data) }),
  enableRisk: () => apiFetch('/api/risk/enable', { method: 'POST' }),
  disableRisk: () => apiFetch('/api/risk/disable', { method: 'POST' }),
};
```

---

## Environment Variables

Create `.env` file:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Testing Integration

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Test each endpoint with the browser Network tab
4. Verify WebSocket connection in browser console

---

## Notes

- All currency values are in cents (¢)
- Timestamps are ISO 8601 format
- IDs are UUIDs
- Market tickers follow Kalshi format: `KXNBA{TYPE}-{DATE}{TEAMS}-{OPTION}`

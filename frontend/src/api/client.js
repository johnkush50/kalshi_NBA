const API_BASE = '/api'

async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

// Games & Aggregator
export const getAvailableGames = (date) => 
  fetchApi(`/games/available?date=${date}`)

export const getLoadedGames = () => 
  fetchApi('/aggregator/states')

export const getGameState = (gameId) => 
  fetchApi(`/aggregator/state/${gameId}`)

export const loadGameByTicker = async (eventTicker) => {
  // First load game into database
  const result = await fetchApi('/games/load', {
    method: 'POST',
    body: JSON.stringify({ event_ticker: eventTicker }),
  })
  
  // Then load into aggregator for real-time tracking
  if (result.game_id) {
    await fetchApi(`/aggregator/load/${result.game_id}`, { method: 'POST' })
  }
  
  return result
}

export const loadGameToAggregator = (gameId) => 
  fetchApi(`/aggregator/load/${gameId}`, { method: 'POST' })

export const unloadGame = (gameId) => 
  fetchApi(`/aggregator/unload/${gameId}`, { method: 'POST' })

// Strategies
export const getStrategyTypes = () => 
  fetchApi('/strategies/types')

export const getStrategies = () => 
  fetchApi('/strategies/')

export const loadStrategy = (strategyType, config = {}, enable = false) => 
  fetchApi('/strategies/load', {
    method: 'POST',
    body: JSON.stringify({ strategy_type: strategyType, config, enable }),
  })

export const enableStrategy = (strategyId) => 
  fetchApi(`/strategies/${strategyId}/enable`, { method: 'POST' })

export const disableStrategy = (strategyId) => 
  fetchApi(`/strategies/${strategyId}/disable`, { method: 'POST' })

export const evaluateStrategy = (strategyId, gameId) => 
  fetchApi(`/strategies/${strategyId}/evaluate?game_id=${gameId}`, { method: 'POST' })

// Execution
export const getExecutionStats = () => 
  fetchApi('/execution/stats')

export const getOrders = (limit = 50) => 
  fetchApi(`/execution/orders?limit=${limit}`)

export const getPositions = () => 
  fetchApi('/execution/positions')

export const getOpenPositions = () => 
  fetchApi('/execution/positions/open')

export const getPnL = () => 
  fetchApi('/execution/pnl')

export const refreshPnL = () => 
  fetchApi('/execution/pnl/refresh', { method: 'POST' })

export const placeManualOrder = (gameId, marketTicker, side, quantity) => 
  fetchApi('/execution/execute/manual', {
    method: 'POST',
    body: JSON.stringify({
      game_id: gameId,
      market_ticker: marketTicker,
      side,
      quantity,
      reason: 'Manual order from dashboard',
    }),
  })

// Risk
export const getRiskStatus = () => 
  fetchApi('/risk/status')

export const getRiskLimits = () => 
  fetchApi('/risk/limits')

export const setRiskLimit = (limitType, value) => 
  fetchApi('/risk/limits', {
    method: 'PUT',
    body: JSON.stringify({ limit_type: limitType, value }),
  })

export const enableRisk = () => 
  fetchApi('/risk/enable', { method: 'POST' })

export const disableRisk = () => 
  fetchApi('/risk/disable', { method: 'POST' })

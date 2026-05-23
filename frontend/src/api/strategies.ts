/**
 * Strategies API Functions
 *
 * Handles all strategy-related API calls including:
 * - Loading/unloading strategies
 * - Enable/disable strategies
 * - Viewing strategy signals
 */

import { fetchApi } from './client'
import type {
  StrategiesResponse,
  StrategyTypesResponse,
  StrategyWithSignals,
  Signal,
} from './types'

/**
 * Get all loaded strategies
 */
export async function getStrategies(): Promise<StrategiesResponse> {
  return fetchApi('/strategies/')
}

/**
 * Get available strategy types
 */
export async function getStrategyTypes(): Promise<StrategyTypesResponse> {
  return fetchApi('/strategies/types')
}

/**
 * Get details for a specific strategy
 */
export async function getStrategy(strategyId: string): Promise<StrategyWithSignals> {
  return fetchApi(`/strategies/${strategyId}`)
}

/**
 * Load a new strategy instance
 */
export async function loadStrategy(
  strategyType: string,
  config?: Record<string, unknown>,
  enable: boolean = false
): Promise<{
  status: string
  strategy_id: string
  strategy_name: string
  is_enabled: boolean
  config: Record<string, unknown>
}> {
  return fetchApi('/strategies/load', {
    method: 'POST',
    body: JSON.stringify({
      strategy_type: strategyType,
      config,
      enable,
    }),
  })
}

/**
 * Unload a strategy
 */
export async function unloadStrategy(strategyId: string): Promise<{ status: string }> {
  return fetchApi(`/strategies/${strategyId}`, { method: 'DELETE' })
}

/**
 * Enable a strategy
 */
export async function enableStrategy(strategyId: string): Promise<{ status: string }> {
  return fetchApi(`/strategies/${strategyId}/enable`, { method: 'POST' })
}

/**
 * Disable a strategy
 */
export async function disableStrategy(strategyId: string): Promise<{ status: string }> {
  return fetchApi(`/strategies/${strategyId}/disable`, { method: 'POST' })
}

/**
 * Update strategy configuration
 */
export async function updateStrategyConfig(
  strategyId: string,
  config: Record<string, unknown>
): Promise<{ status: string; strategy_id: string; config: Record<string, unknown> }> {
  return fetchApi(`/strategies/${strategyId}/config`, {
    method: 'PUT',
    body: JSON.stringify({ config }),
  })
}

/**
 * Get recent signals from a strategy
 */
export async function getStrategySignals(
  strategyId: string,
  limit: number = 20
): Promise<{ strategy_id: string; signal_count: number; signals: Signal[] }> {
  return fetchApi(`/strategies/${strategyId}/signals?limit=${limit}`)
}

/**
 * Run all enabled strategies on all loaded games
 */
export async function evaluateAllStrategies(): Promise<{
  games_evaluated: number
  total_signals: number
  signals_by_game: Record<string, Signal[]>
}> {
  return fetchApi('/strategies/evaluate-all', { method: 'POST' })
}

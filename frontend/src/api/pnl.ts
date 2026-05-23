/**
 * P&L API Functions
 *
 * Handles portfolio P&L and performance metrics:
 * - Portfolio summary
 * - Performance statistics
 * - P&L refresh
 */

import { fetchApi } from './client'
import type { PortfolioPnL, PerformanceResponse } from './types'

/**
 * Get current portfolio P&L summary
 */
export async function getPnL(): Promise<PortfolioPnL> {
  return fetchApi('/execution/pnl')
}

/**
 * Refresh unrealized P&L based on current market prices
 */
export async function refreshPnL(): Promise<{ status: string; portfolio: PortfolioPnL }> {
  return fetchApi('/execution/pnl/refresh', { method: 'POST' })
}

/**
 * Get overall trading performance metrics
 */
export async function getPerformance(): Promise<PerformanceResponse> {
  return fetchApi('/execution/performance')
}

/**
 * Get performance metrics for a specific strategy
 */
export async function getStrategyPerformance(strategyId: string): Promise<{
  strategy_id: string
  performance: PerformanceResponse['order_stats']
}> {
  return fetchApi(`/execution/performance/strategy/${strategyId}`)
}

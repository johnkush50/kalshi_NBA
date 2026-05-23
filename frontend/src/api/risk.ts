/**
 * Risk API Functions
 *
 * Handles risk management operations:
 * - Risk status and limits
 * - Enable/disable risk management
 * - Update risk limits
 */

import { fetchApi } from './client'
import type { RiskStatus, RiskLimits } from './types'

/**
 * Get current risk management status
 */
export async function getRiskStatus(): Promise<RiskStatus> {
  return fetchApi('/risk/status')
}

/**
 * Get all risk limits
 */
export async function getRiskLimits(): Promise<RiskLimits> {
  return fetchApi('/risk/limits')
}

/**
 * Set a specific risk limit
 */
export async function setRiskLimit(
  limitType: string,
  value: number
): Promise<{ status: string; limit_type: string; value: number }> {
  return fetchApi('/risk/limits', {
    method: 'PUT',
    body: JSON.stringify({ limit_type: limitType, value }),
  })
}

/**
 * Set multiple risk limits at once
 */
export async function setBulkLimits(
  limits: Record<string, number>
): Promise<{ updated: string[]; errors: string[] }> {
  return fetchApi('/risk/limits/bulk', {
    method: 'PUT',
    body: JSON.stringify({ limits }),
  })
}

/**
 * Enable risk management
 */
export async function enableRisk(): Promise<{ status: string }> {
  return fetchApi('/risk/enable', { method: 'POST' })
}

/**
 * Disable risk management
 */
export async function disableRisk(): Promise<{ status: string; warning: string }> {
  return fetchApi('/risk/disable', { method: 'POST' })
}

/**
 * Reset all risk tracking counters
 */
export async function resetRiskCounters(): Promise<{ status: string; message: string }> {
  return fetchApi('/risk/reset', { method: 'POST' })
}

/**
 * Check if a hypothetical order would pass risk checks
 */
export async function checkHypotheticalOrder(
  marketTicker: string,
  gameId: string,
  side: 'yes' | 'no',
  quantity: number
): Promise<{
  would_approve: boolean
  reason: string | null
  limit_type: string | null
  current_value: number | null
  limit_value: number | null
}> {
  const params = new URLSearchParams({
    market_ticker: marketTicker,
    game_id: gameId,
    side,
    quantity: quantity.toString(),
  })
  return fetchApi(`/risk/check?${params}`)
}

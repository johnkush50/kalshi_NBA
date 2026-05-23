/**
 * Execution API Functions
 *
 * Handles order execution and position management:
 * - Viewing positions and orders
 * - Manual order placement
 * - Closing positions
 */

import { fetchApi } from './client'
import type {
  ExecutionStats,
  PositionsResponse,
  OrdersResponse,
  ManualOrderRequest,
  ClosePositionResponse,
} from './types'

/**
 * Get execution engine statistics
 */
export async function getExecutionStats(): Promise<ExecutionStats> {
  return fetchApi('/execution/stats')
}

/**
 * Get all positions (open and closed)
 */
export async function getPositions(): Promise<PositionsResponse> {
  return fetchApi('/execution/positions')
}

/**
 * Get only open positions
 */
export async function getOpenPositions(): Promise<PositionsResponse> {
  return fetchApi('/execution/positions/open')
}

/**
 * Get recent orders
 */
export async function getOrders(limit: number = 50): Promise<OrdersResponse> {
  return fetchApi(`/execution/orders?limit=${limit}`)
}

/**
 * Get orders for a specific game
 */
export async function getOrdersByGame(gameId: string): Promise<OrdersResponse> {
  return fetchApi(`/execution/orders/game/${gameId}`)
}

/**
 * Get orders for a specific strategy
 */
export async function getOrdersByStrategy(
  strategyId: string,
  limit: number = 50
): Promise<OrdersResponse> {
  return fetchApi(`/execution/orders/strategy/${strategyId}?limit=${limit}`)
}

/**
 * Place a manual order
 */
export async function placeManualOrder(request: ManualOrderRequest): Promise<{
  status: string
  order_id: string
  fill_price: number | null
  quantity: number
  position: { quantity: number; avg_price: number } | null
}> {
  return fetchApi('/execution/execute/manual', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Close a position
 */
export async function closePosition(
  marketTicker: string,
  exitPrice?: number
): Promise<ClosePositionResponse> {
  const url = `/execution/positions/${encodeURIComponent(marketTicker)}/close`
  return fetchApi(url, {
    method: 'POST',
    body: JSON.stringify({ exit_price: exitPrice }),
  })
}

/**
 * Settle a position at expiry
 */
export async function settlePosition(
  marketTicker: string,
  outcome: boolean
): Promise<{
  status: string
  market_ticker: string
  outcome: string
  realized_pnl: number
}> {
  return fetchApi(`/execution/positions/${encodeURIComponent(marketTicker)}/settle?outcome=${outcome}`, {
    method: 'POST',
  })
}

/**
 * React Query hooks for Execution API
 *
 * Provides data fetching and mutations for order execution and positions.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as executionApi from '../api/execution'
import type { ManualOrderRequest } from '../api/types'

// Query keys for cache management
export const executionKeys = {
  all: ['execution'] as const,
  stats: () => [...executionKeys.all, 'stats'] as const,
  positions: () => [...executionKeys.all, 'positions'] as const,
  openPositions: () => [...executionKeys.all, 'positions', 'open'] as const,
  orders: () => [...executionKeys.all, 'orders'] as const,
  ordersByGame: (gameId: string) => [...executionKeys.all, 'orders', 'game', gameId] as const,
  ordersByStrategy: (strategyId: string) =>
    [...executionKeys.all, 'orders', 'strategy', strategyId] as const,
}

/**
 * Hook to fetch execution statistics
 */
export function useExecutionStats() {
  return useQuery({
    queryKey: executionKeys.stats(),
    queryFn: executionApi.getExecutionStats,
    refetchInterval: 10000,
  })
}

/**
 * Hook to fetch all positions
 */
export function usePositions() {
  return useQuery({
    queryKey: executionKeys.positions(),
    queryFn: executionApi.getPositions,
    refetchInterval: 10000,
  })
}

/**
 * Hook to fetch open positions only
 */
export function useOpenPositions() {
  return useQuery({
    queryKey: executionKeys.openPositions(),
    queryFn: executionApi.getOpenPositions,
    refetchInterval: 10000,
  })
}

/**
 * Hook to fetch recent orders
 */
export function useOrders(limit: number = 50) {
  return useQuery({
    queryKey: [...executionKeys.orders(), limit] as const,
    queryFn: () => executionApi.getOrders(limit),
    refetchInterval: 10000,
  })
}

/**
 * Hook to fetch orders for a specific game
 */
export function useOrdersByGame(gameId: string) {
  return useQuery({
    queryKey: executionKeys.ordersByGame(gameId),
    queryFn: () => executionApi.getOrdersByGame(gameId),
    enabled: !!gameId,
  })
}

/**
 * Hook to fetch orders for a specific strategy
 */
export function useOrdersByStrategy(strategyId: string, limit: number = 50) {
  return useQuery({
    queryKey: executionKeys.ordersByStrategy(strategyId),
    queryFn: () => executionApi.getOrdersByStrategy(strategyId, limit),
    enabled: !!strategyId,
  })
}

/**
 * Hook to place a manual order
 */
export function usePlaceManualOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ManualOrderRequest) => executionApi.placeManualOrder(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: executionKeys.all })
    },
  })
}

/**
 * Hook to close a position
 */
export function useClosePosition() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      marketTicker,
      exitPrice,
    }: {
      marketTicker: string
      exitPrice?: number
    }) => executionApi.closePosition(marketTicker, exitPrice),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: executionKeys.all })
    },
  })
}

/**
 * Hook to settle a position at expiry
 */
export function useSettlePosition() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      marketTicker,
      outcome,
    }: {
      marketTicker: string
      outcome: boolean
    }) => executionApi.settlePosition(marketTicker, outcome),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: executionKeys.all })
    },
  })
}

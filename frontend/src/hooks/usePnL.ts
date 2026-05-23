/**
 * React Query hooks for P&L API
 *
 * Provides data fetching and mutations for P&L and performance.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as pnlApi from '../api/pnl'
import { executionKeys } from './useExecution'

// Query keys for cache management
export const pnlKeys = {
  all: ['pnl'] as const,
  summary: () => [...pnlKeys.all, 'summary'] as const,
  performance: () => [...pnlKeys.all, 'performance'] as const,
  strategyPerformance: (strategyId: string) =>
    [...pnlKeys.all, 'strategy', strategyId] as const,
}

/**
 * Hook to fetch portfolio P&L summary
 */
export function usePnL() {
  return useQuery({
    queryKey: pnlKeys.summary(),
    queryFn: pnlApi.getPnL,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

/**
 * Hook to fetch overall performance metrics
 */
export function usePerformance() {
  return useQuery({
    queryKey: pnlKeys.performance(),
    queryFn: pnlApi.getPerformance,
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

/**
 * Hook to fetch strategy-specific performance
 */
export function useStrategyPerformance(strategyId: string) {
  return useQuery({
    queryKey: pnlKeys.strategyPerformance(strategyId),
    queryFn: () => pnlApi.getStrategyPerformance(strategyId),
    enabled: !!strategyId,
  })
}

/**
 * Hook to refresh P&L based on current market prices
 */
export function useRefreshPnL() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: pnlApi.refreshPnL,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: pnlKeys.all })
      queryClient.invalidateQueries({ queryKey: executionKeys.positions() })
    },
  })
}

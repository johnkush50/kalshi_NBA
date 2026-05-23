/**
 * React Query hooks for Risk API
 *
 * Provides data fetching and mutations for risk management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as riskApi from '../api/risk'

// Query keys for cache management
export const riskKeys = {
  all: ['risk'] as const,
  status: () => [...riskKeys.all, 'status'] as const,
  limits: () => [...riskKeys.all, 'limits'] as const,
}

/**
 * Hook to fetch risk management status
 */
export function useRiskStatus() {
  return useQuery({
    queryKey: riskKeys.status(),
    queryFn: riskApi.getRiskStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

/**
 * Hook to fetch all risk limits
 */
export function useRiskLimits() {
  return useQuery({
    queryKey: riskKeys.limits(),
    queryFn: riskApi.getRiskLimits,
    staleTime: 30000, // Limits don't change often
  })
}

/**
 * Hook to set a risk limit
 */
export function useSetRiskLimit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      limitType,
      value,
    }: {
      limitType: string
      value: number
    }) => riskApi.setRiskLimit(limitType, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: riskKeys.all })
    },
  })
}

/**
 * Hook to set multiple risk limits at once
 */
export function useSetBulkLimits() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (limits: Record<string, number>) => riskApi.setBulkLimits(limits),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: riskKeys.all })
    },
  })
}

/**
 * Hook to enable risk management
 */
export function useEnableRisk() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: riskApi.enableRisk,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: riskKeys.status() })
    },
  })
}

/**
 * Hook to disable risk management
 */
export function useDisableRisk() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: riskApi.disableRisk,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: riskKeys.status() })
    },
  })
}

/**
 * Hook to reset risk counters
 */
export function useResetRiskCounters() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: riskApi.resetRiskCounters,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: riskKeys.status() })
    },
  })
}

/**
 * Hook to check if a hypothetical order would pass risk checks
 */
export function useCheckHypotheticalOrder() {
  return useMutation({
    mutationFn: ({
      marketTicker,
      gameId,
      side,
      quantity,
    }: {
      marketTicker: string
      gameId: string
      side: 'yes' | 'no'
      quantity: number
    }) => riskApi.checkHypotheticalOrder(marketTicker, gameId, side, quantity),
  })
}

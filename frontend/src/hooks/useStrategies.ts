/**
 * React Query hooks for Strategies API
 *
 * Provides data fetching and mutations for strategy management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as strategiesApi from '../api/strategies'

// Query keys for cache management
export const strategiesKeys = {
  all: ['strategies'] as const,
  list: () => [...strategiesKeys.all, 'list'] as const,
  types: () => [...strategiesKeys.all, 'types'] as const,
  detail: (id: string) => [...strategiesKeys.all, 'detail', id] as const,
  signals: (id: string) => [...strategiesKeys.all, 'signals', id] as const,
}

/**
 * Hook to fetch all loaded strategies
 */
export function useStrategies() {
  return useQuery({
    queryKey: strategiesKeys.list(),
    queryFn: strategiesApi.getStrategies,
    refetchInterval: 15000, // Refresh every 15 seconds
  })
}

/**
 * Hook to fetch available strategy types
 */
export function useStrategyTypes() {
  return useQuery({
    queryKey: strategiesKeys.types(),
    queryFn: strategiesApi.getStrategyTypes,
    staleTime: 60000, // Strategy types rarely change
  })
}

/**
 * Hook to fetch a specific strategy with signals
 */
export function useStrategy(strategyId: string) {
  return useQuery({
    queryKey: strategiesKeys.detail(strategyId),
    queryFn: () => strategiesApi.getStrategy(strategyId),
    enabled: !!strategyId,
  })
}

/**
 * Hook to fetch signals for a specific strategy
 */
export function useStrategySignals(strategyId: string, limit: number = 20) {
  return useQuery({
    queryKey: strategiesKeys.signals(strategyId),
    queryFn: () => strategiesApi.getStrategySignals(strategyId, limit),
    enabled: !!strategyId,
    refetchInterval: 10000,
  })
}

/**
 * Hook to load a new strategy
 */
export function useLoadStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      strategyType,
      config,
      enable,
    }: {
      strategyType: string
      config?: Record<string, unknown>
      enable?: boolean
    }) => strategiesApi.loadStrategy(strategyType, config, enable),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.list() })
    },
  })
}

/**
 * Hook to unload a strategy
 */
export function useUnloadStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: strategiesApi.unloadStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.list() })
    },
  })
}

/**
 * Hook to enable a strategy
 */
export function useEnableStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: strategiesApi.enableStrategy,
    onSuccess: (_data, strategyId) => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.list() })
      queryClient.invalidateQueries({ queryKey: strategiesKeys.detail(strategyId) })
    },
  })
}

/**
 * Hook to disable a strategy
 */
export function useDisableStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: strategiesApi.disableStrategy,
    onSuccess: (_data, strategyId) => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.list() })
      queryClient.invalidateQueries({ queryKey: strategiesKeys.detail(strategyId) })
    },
  })
}

/**
 * Hook to update strategy configuration
 */
export function useUpdateStrategyConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      strategyId,
      config,
    }: {
      strategyId: string
      config: Record<string, unknown>
    }) => strategiesApi.updateStrategyConfig(strategyId, config),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.list() })
      queryClient.invalidateQueries({ queryKey: strategiesKeys.detail(variables.strategyId) })
    },
  })
}

/**
 * Hook to evaluate all strategies
 */
export function useEvaluateAllStrategies() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: strategiesApi.evaluateAllStrategies,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategiesKeys.all })
    },
  })
}

/**
 * React Query hooks for Games API
 *
 * Provides data fetching and mutations for game management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as gamesApi from '../api/games'

// Query keys for cache management
export const gamesKeys = {
  all: ['games'] as const,
  loaded: () => [...gamesKeys.all, 'loaded'] as const,
  available: (date: string) => [...gamesKeys.all, 'available', date] as const,
  detail: (id: string) => [...gamesKeys.all, 'detail', id] as const,
}

/**
 * Hook to fetch all loaded games from the aggregator
 */
export function useLoadedGames() {
  return useQuery({
    queryKey: gamesKeys.loaded(),
    queryFn: gamesApi.getLoadedGames,
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

/**
 * Hook to fetch a specific game's state
 */
export function useGameState(gameId: string) {
  return useQuery({
    queryKey: gamesKeys.detail(gameId),
    queryFn: () => gamesApi.getGameState(gameId),
    enabled: !!gameId,
  })
}

/**
 * Hook to fetch available games for a date
 */
export function useAvailableGames(date: string) {
  return useQuery({
    queryKey: gamesKeys.available(date),
    queryFn: () => gamesApi.getAvailableGames(date),
    enabled: !!date,
  })
}

/**
 * Hook to load a game by ID into the aggregator
 */
export function useLoadGame() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.loadGame,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

/**
 * Hook to load a game by event ticker
 */
export function useLoadGameByTicker() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.loadGameByTicker,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

/**
 * Hook to unload a game from the aggregator
 */
export function useUnloadGame() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.unloadGame,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

/**
 * Hook to refresh Kalshi orderbook data
 */
export function useRefreshKalshi() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.refreshKalshi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

/**
 * Hook to refresh NBA live data
 */
export function useRefreshNba() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.refreshNba,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

/**
 * Hook to refresh betting odds
 */
export function useRefreshOdds() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: gamesApi.refreshOdds,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
    },
  })
}

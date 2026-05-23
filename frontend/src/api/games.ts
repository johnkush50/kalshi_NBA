/**
 * Games API Functions
 *
 * Handles all game-related API calls including:
 * - Loading/unloading games
 * - Fetching game states from aggregator
 * - Browsing available games
 */

import { fetchApi } from './client'
import type {
  LoadedGamesResponse,
  GameState,
  AvailableGamesResponse,
  LoadGameResponse,
} from './types'

/**
 * Get all currently loaded games with their full state
 */
export async function getLoadedGames(): Promise<LoadedGamesResponse> {
  return fetchApi('/aggregator/states')
}

/**
 * Get detailed state for a specific game
 */
export async function getGameState(gameId: string): Promise<GameState> {
  return fetchApi(`/aggregator/state/${gameId}`)
}

/**
 * Get games available to load for a specific date
 */
export async function getAvailableGames(date: string): Promise<AvailableGamesResponse> {
  return fetchApi(`/games/available?date=${date}`)
}

/**
 * Load a game into the aggregator for tracking
 */
export async function loadGame(gameId: string): Promise<LoadGameResponse> {
  return fetchApi(`/aggregator/load/${gameId}`, { method: 'POST' })
}

/**
 * Load a game by event ticker
 */
export async function loadGameByTicker(eventTicker: string): Promise<{
  success: boolean
  game_id: string
  event_ticker: string
  market_count: number
}> {
  return fetchApi('/games/load', {
    method: 'POST',
    body: JSON.stringify({ event_ticker: eventTicker }),
  })
}

/**
 * Unload a game from the aggregator
 */
export async function unloadGame(gameId: string): Promise<{ status: string; message: string }> {
  return fetchApi(`/aggregator/unload/${gameId}`, { method: 'POST' })
}

/**
 * Refresh Kalshi orderbook data for a game
 */
export async function refreshKalshi(gameId: string): Promise<LoadGameResponse> {
  return fetchApi(`/aggregator/refresh/${gameId}/kalshi`, { method: 'POST' })
}

/**
 * Refresh NBA live data for a game
 */
export async function refreshNba(gameId: string): Promise<LoadGameResponse> {
  return fetchApi(`/aggregator/refresh/${gameId}/nba`, { method: 'POST' })
}

/**
 * Refresh betting odds for a game
 */
export async function refreshOdds(gameId: string): Promise<LoadGameResponse> {
  return fetchApi(`/aggregator/refresh/${gameId}/odds`, { method: 'POST' })
}

/**
 * Get list of all loaded game IDs
 */
export async function getLoadedGameIds(): Promise<{ count: number; game_ids: string[] }> {
  return fetchApi('/aggregator/game-ids')
}

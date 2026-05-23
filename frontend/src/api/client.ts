/**
 * API Client for Kalshi NBA Paper Trading Backend
 *
 * Provides type-safe fetch wrapper for all API calls.
 * Uses Vite proxy to avoid CORS issues.
 */

const API_BASE = '/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

/**
 * Generic fetch wrapper with error handling
 */
export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new ApiError(response.status, error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Health check - verify backend connection
 */
export async function checkHealth(): Promise<{ status: string }> {
  return fetchApi('/health')
}

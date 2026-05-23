/**
 * WebSocket Hook for Real-time Updates
 *
 * Connects to the backend WebSocket server for:
 * - Trading signals
 * - Order updates
 * - P&L changes
 * - Market price updates
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { gamesKeys } from './useGames'
import { strategiesKeys } from './useStrategies'
import { executionKeys } from './useExecution'
import { pnlKeys } from './usePnL'
import type { Signal, WebSocketMessage } from '../api/types'

const WS_URL = 'ws://localhost:8000/ws'

interface UseWebSocketOptions {
  channels?: string[]
  autoConnect?: boolean
}

interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  lastSignal: Signal | null
  lastMessage: WebSocketMessage | null
  error: string | null
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { channels = ['all'], autoConnect = true } = options

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    lastSignal: null,
    lastMessage: null,
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const queryClient = useQueryClient()

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage

        setState((prev) => ({
          ...prev,
          lastMessage: message,
        }))

        // Handle different message types and invalidate relevant queries
        switch (message.type) {
          case 'signal':
            setState((prev) => ({
              ...prev,
              lastSignal: message.data as Signal,
            }))
            queryClient.invalidateQueries({ queryKey: strategiesKeys.all })
            break

          case 'order_filled':
          case 'order_rejected':
            queryClient.invalidateQueries({ queryKey: executionKeys.orders() })
            queryClient.invalidateQueries({ queryKey: executionKeys.positions() })
            queryClient.invalidateQueries({ queryKey: pnlKeys.all })
            break

          case 'pnl_update':
            queryClient.invalidateQueries({ queryKey: pnlKeys.all })
            queryClient.invalidateQueries({ queryKey: executionKeys.positions() })
            break

          case 'market_update':
            queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
            break

          case 'nba_update':
            queryClient.invalidateQueries({ queryKey: gamesKeys.loaded() })
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    },
    [queryClient]
  )

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setState((prev) => ({ ...prev, isConnecting: true, error: null }))

    const channelsParam = channels.join(',')
    const ws = new WebSocket(`${WS_URL}?channels=${channelsParam}`)
    wsRef.current = ws

    ws.onopen = () => {
      setState((prev) => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null,
      }))
      console.log('WebSocket connected')
    }

    ws.onclose = (event) => {
      setState((prev) => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
      }))
      console.log('WebSocket disconnected:', event.code, event.reason)

      // Auto-reconnect after 3 seconds
      if (autoConnect) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }
    }

    ws.onerror = (event) => {
      setState((prev) => ({
        ...prev,
        error: 'WebSocket connection error',
        isConnecting: false,
      }))
      console.error('WebSocket error:', event)
    }

    ws.onmessage = handleMessage
  }, [channels, autoConnect, handleMessage])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setState((prev) => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }))
  }, [])

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    ...state,
    connect,
    disconnect,
  }
}

export default useWebSocket

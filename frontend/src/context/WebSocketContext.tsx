/**
 * WebSocket Context
 *
 * Provides WebSocket state to the entire application.
 * Use this to access connection status and real-time data.
 */

import { createContext, useContext, ReactNode } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import type { Signal, WebSocketMessage } from '../api/types'

interface WebSocketContextValue {
  isConnected: boolean
  isConnecting: boolean
  lastSignal: Signal | null
  lastMessage: WebSocketMessage | null
  error: string | null
  connect: () => void
  disconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null)

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const ws = useWebSocket({ autoConnect: true })

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider')
  }
  return context
}

export default WebSocketContext

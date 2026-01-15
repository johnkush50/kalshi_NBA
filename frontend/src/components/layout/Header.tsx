import { Zap, Wifi, WifiOff, TrendingUp, TrendingDown, Package, ClipboardList } from 'lucide-react'
import { connectionStatus, pnlSummary, openPositions, orderHistory } from '../../data/mockData'

export default function Header() {
  const formatPnl = (value: number) => {
    const prefix = value >= 0 ? '+' : ''
    return `${prefix}${value}¢`
  }

  const ConnectionIndicator = ({
    status,
    label
  }: {
    status: 'connected' | 'disconnected' | 'connecting'
    label: string
  }) => {
    const colors = {
      connected: 'bg-neon-green',
      disconnected: 'bg-neon-red',
      connecting: 'bg-neon-yellow animate-pulse',
    }
    const Icon = status === 'connected' ? Wifi : WifiOff

    return (
      <div className="flex items-center gap-2">
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${colors[status]}`} />
          {status === 'connected' && (
            <div className={`absolute inset-0 w-2 h-2 rounded-full ${colors[status]} animate-ping opacity-75`} />
          )}
        </div>
        <Icon className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
    )
  }

  const ordersToday = orderHistory.filter(o => o.status === 'filled').length

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-terminal-surface/95 backdrop-blur-sm border-b border-terminal-border z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Logo & Title */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Zap className="w-7 h-7 text-neon-cyan" />
              <div className="absolute inset-0 blur-md bg-neon-cyan/30" />
            </div>
            <span className="font-display font-bold text-xl tracking-wider text-white">
              KALSHI<span className="text-neon-cyan">NBA</span>
            </span>
          </div>
          <div className="h-6 w-px bg-terminal-border" />
          <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Paper Trading Terminal</span>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-6">
          <ConnectionIndicator status={connectionStatus.backend} label="API" />
          <ConnectionIndicator status={connectionStatus.websocket} label="WS" />
          <ConnectionIndicator status={connectionStatus.kalshi} label="Kalshi" />
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-6">
          {/* P&L Display */}
          <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-terminal-bg/50 neon-border">
            {pnlSummary.totalPnl >= 0 ? (
              <TrendingUp className="w-4 h-4 text-neon-green" />
            ) : (
              <TrendingDown className="w-4 h-4 text-neon-red" />
            )}
            <div className="flex flex-col">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Total P&L</span>
              <span className={`text-sm font-mono font-bold ${
                pnlSummary.totalPnl >= 0 ? 'text-neon-green text-glow-green' : 'text-neon-red text-glow-red'
              }`}>
                {formatPnl(pnlSummary.totalPnl)}
              </span>
            </div>
          </div>

          {/* Position Count */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-terminal-bg/50 border border-terminal-border">
            <Package className="w-4 h-4 text-neon-cyan" />
            <div className="flex flex-col">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Positions</span>
              <span className="text-sm font-mono font-semibold text-white">{openPositions.length}</span>
            </div>
          </div>

          {/* Orders Today */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-terminal-bg/50 border border-terminal-border">
            <ClipboardList className="w-4 h-4 text-neon-purple" />
            <div className="flex flex-col">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Orders</span>
              <span className="text-sm font-mono font-semibold text-white">{ordersToday}</span>
            </div>
          </div>

          {/* Time */}
          <div className="text-right">
            <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Local Time</div>
            <div className="text-sm font-mono text-neon-cyan">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>
      </div>
    </header>
  )
}

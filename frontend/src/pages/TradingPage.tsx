import {
  ArrowLeftRight,
  TrendingUp,
  TrendingDown,
  X,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Loading from '../components/ui/Loading'
import ErrorDisplay from '../components/ui/ErrorDisplay'
import { useOpenPositions, useOrders, useClosePosition } from '../hooks/useExecution'
import type { Position, Order } from '../api/types'

function PositionRow({
  position,
  onClose,
  isClosing,
}: {
  position: Position
  onClose: () => void
  isClosing: boolean
}) {
  const unrealizedPnl = position.unrealized_pnl ?? 0
  const isProfitable = unrealizedPnl >= 0
  const pnlPercent = position.total_cost > 0 ? (unrealizedPnl / position.total_cost) * 100 : 0

  // Extract market name from ticker
  const marketName = position.market_ticker.split('-').pop() || position.market_ticker
  const isYes = position.side.toLowerCase() === 'yes'

  return (
    <tr className="group">
      <td>
        <div>
          <div className="font-mono text-sm text-white">{marketName}</div>
          <div className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]">
            {position.market_ticker}
          </div>
        </div>
      </td>
      <td className="text-center">
        <Badge variant={isYes ? 'success' : 'danger'}>{position.side.toUpperCase()}</Badge>
      </td>
      <td className="text-right font-mono text-white">{position.quantity}</td>
      <td className="text-right font-mono text-slate-400">{position.avg_entry_price}¢</td>
      <td className="text-right font-mono text-slate-300">{position.total_cost}¢</td>
      <td
        className={`text-right font-mono font-bold ${
          isProfitable ? 'text-neon-green text-glow-green' : 'text-neon-red text-glow-red'
        }`}
      >
        <div className="flex items-center justify-end gap-1">
          {isProfitable ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {isProfitable ? '+' : ''}
          {unrealizedPnl}¢
        </div>
        <div className="text-xs opacity-70">
          ({isProfitable ? '+' : ''}
          {pnlPercent.toFixed(1)}%)
        </div>
      </td>
      <td className="text-right">
        <Button
          variant="danger"
          size="sm"
          icon={isClosing ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={onClose}
          disabled={isClosing}
        >
          Close
        </Button>
      </td>
    </tr>
  )
}

function OrderRow({ order }: { order: Order }) {
  const statusConfig = {
    filled: { icon: CheckCircle, variant: 'success' as const, label: 'Filled' },
    rejected: { icon: XCircle, variant: 'danger' as const, label: 'Rejected' },
    cancelled: { icon: AlertCircle, variant: 'warning' as const, label: 'Cancelled' },
    pending: { icon: Clock, variant: 'info' as const, label: 'Pending' },
  }

  const status = statusConfig[order.status]
  const StatusIcon = status.icon
  const marketName = order.market_ticker.split('-').pop() || order.market_ticker
  const isYes = order.side.toLowerCase() === 'yes'

  return (
    <tr>
      <td className="font-mono text-xs text-slate-400">
        {new Date(order.placed_at).toLocaleTimeString()}
      </td>
      <td>
        <div className="font-mono text-sm text-white">{marketName}</div>
        {order.strategy_name && <div className="text-[10px] text-slate-500">{order.strategy_name}</div>}
      </td>
      <td className="text-center">
        <Badge variant={isYes ? 'success' : 'danger'} size="sm">
          {order.side.toUpperCase()}
        </Badge>
      </td>
      <td className="text-right font-mono text-white">{order.quantity}</td>
      <td className="text-right font-mono text-slate-300">
        {order.filled_price ? `${order.filled_price}¢` : '—'}
      </td>
      <td>
        <div className="flex items-center gap-1.5">
          <StatusIcon
            className={`w-3.5 h-3.5 ${
              status.variant === 'success'
                ? 'text-neon-green'
                : status.variant === 'danger'
                  ? 'text-neon-red'
                  : status.variant === 'warning'
                    ? 'text-neon-yellow'
                    : 'text-neon-cyan'
            }`}
          />
          <Badge variant={status.variant} size="sm">
            {status.label}
          </Badge>
        </div>
      </td>
    </tr>
  )
}

export default function TradingPage() {
  const { data: positionsData, isLoading: isLoadingPositions, error: positionsError } = useOpenPositions()
  const { data: ordersData, isLoading: isLoadingOrders, error: ordersError } = useOrders(50)
  const closePosition = useClosePosition()

  const positions = Array.isArray(positionsData?.positions) ? positionsData.positions : []
  const orders = ordersData?.orders || []

  const totalUnrealized = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0)
  const totalCost = positions.reduce((sum, p) => sum + p.total_cost, 0)
  const filledOrdersCount = orders.filter((o) => o.status === 'filled').length

  const handleClosePosition = (marketTicker: string) => {
    closePosition.mutate({ marketTicker })
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl tracking-wider text-white">
            Trading <span className="text-neon-cyan">Activity</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">Manage positions and view order history</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Open Positions</div>
          <div className="font-display text-2xl font-bold text-white mt-1">{positions.length}</div>
        </div>
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Total Cost Basis</div>
          <div className="font-display text-2xl font-bold text-white mt-1">{totalCost}¢</div>
        </div>
        <div
          className={`bg-terminal-surface/80 rounded-lg border p-4 ${
            totalUnrealized >= 0 ? 'neon-border-green' : 'neon-border-red'
          }`}
        >
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Unrealized P&L</div>
          <div
            className={`font-display text-2xl font-bold mt-1 ${
              totalUnrealized >= 0 ? 'text-neon-green' : 'text-neon-red'
            }`}
          >
            {totalUnrealized >= 0 ? '+' : ''}
            {totalUnrealized}¢
          </div>
        </div>
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-4">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Orders Today</div>
          <div className="font-display text-2xl font-bold text-white mt-1">{filledOrdersCount}</div>
        </div>
      </div>

      {/* Open Positions */}
      <Panel
        title="Open Positions"
        subtitle={`${positions.length} active positions`}
        icon={<ArrowLeftRight className="w-5 h-5 text-neon-cyan" />}
        neonBorder
      >
        {isLoadingPositions ? (
          <Loading message="Loading positions..." />
        ) : positionsError ? (
          <ErrorDisplay message={positionsError instanceof Error ? positionsError.message : 'Failed to load positions'} />
        ) : positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr>
                  <th>Market</th>
                  <th className="text-center">Side</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Avg Entry</th>
                  <th className="text-right">Cost</th>
                  <th className="text-right">Unrealized P&L</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position, idx) => (
                  <PositionRow
                    key={position.market_ticker || idx}
                    position={position}
                    onClose={() => handleClosePosition(position.market_ticker)}
                    isClosing={closePosition.isPending}
                  />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500">
            <ArrowLeftRight className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="font-mono">No open positions</p>
          </div>
        )}
      </Panel>

      {/* Order History */}
      <Panel
        title="Order History"
        subtitle="Recent order activity"
        icon={<Clock className="w-5 h-5 text-neon-purple" />}
      >
        {isLoadingOrders ? (
          <Loading message="Loading orders..." />
        ) : ordersError ? (
          <ErrorDisplay message={ordersError instanceof Error ? ordersError.message : 'Failed to load orders'} />
        ) : orders.length === 0 ? (
          <div className="py-8 text-center text-slate-500 font-mono text-sm">No orders yet</div>
        ) : (
          <div className="overflow-x-auto max-h-[400px]">
            <table className="w-full data-table">
              <thead className="sticky top-0 bg-terminal-surface">
                <tr>
                  <th>Time</th>
                  <th>Market</th>
                  <th className="text-center">Side</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Fill Price</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <OrderRow key={order.id} order={order} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}

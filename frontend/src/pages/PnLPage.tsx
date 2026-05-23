import {
  DollarSign,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Wallet,
  Target,
  Activity,
  BarChart3,
  PieChart,
  Loader2,
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Loading from '../components/ui/Loading'
import ErrorDisplay from '../components/ui/ErrorDisplay'
import { usePnL, usePerformance, useRefreshPnL } from '../hooks/usePnL'
import { useOpenPositions } from '../hooks/useExecution'

function StatCard({
  label,
  value,
  subValue,
  icon: Icon,
  variant = 'default',
}: {
  label: string
  value: string
  subValue?: string
  icon: typeof DollarSign
  variant?: 'default' | 'success' | 'danger'
}) {
  const borderClass = {
    default: 'border-terminal-border',
    success: 'border-neon-green/30 shadow-neon-green',
    danger: 'border-neon-red/30 shadow-neon-red',
  }

  const iconBg = {
    default: 'bg-terminal-bg',
    success: 'bg-neon-green/10',
    danger: 'bg-neon-red/10',
  }

  const iconColor = {
    default: 'text-neon-cyan',
    success: 'text-neon-green',
    danger: 'text-neon-red',
  }

  const valueColor = {
    default: 'text-white',
    success: 'text-neon-green text-glow-green',
    danger: 'text-neon-red text-glow-red',
  }

  return (
    <div className={`bg-terminal-surface/80 rounded-lg border ${borderClass[variant]} p-5`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">{label}</div>
          <div className={`font-display text-3xl font-bold ${valueColor[variant]}`}>{value}</div>
          {subValue && <div className="text-sm font-mono text-slate-400 mt-1">{subValue}</div>}
        </div>
        <div className={`p-3 rounded-lg ${iconBg[variant]}`}>
          <Icon className={`w-6 h-6 ${iconColor[variant]}`} />
        </div>
      </div>
    </div>
  )
}

export default function PnLPage() {
  const { data: pnlData, isLoading: isLoadingPnL, error: pnlError, refetch: refetchPnL } = usePnL()
  const { data: performanceData, isLoading: isLoadingPerformance } = usePerformance()
  const { data: positionsData, isLoading: isLoadingPositions } = useOpenPositions()
  const refreshPnL = useRefreshPnL()

  const isLoading = isLoadingPnL || isLoadingPerformance || isLoadingPositions

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-2xl tracking-wider text-white">
              Portfolio <span className="text-neon-cyan">Performance</span>
            </h1>
          </div>
        </div>
        <Loading message="Loading P&L data..." />
      </div>
    )
  }

  if (pnlError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-2xl tracking-wider text-white">
              Portfolio <span className="text-neon-cyan">Performance</span>
            </h1>
          </div>
        </div>
        <ErrorDisplay
          message={pnlError instanceof Error ? pnlError.message : 'Failed to load P&L data'}
          onRetry={() => refetchPnL()}
        />
      </div>
    )
  }

  const portfolio = pnlData || { total_pnl: 0, unrealized_pnl: 0, realized_pnl: 0, total_cost: 0 }
  const performance = performanceData?.order_stats || {
    total_orders: 0,
    total_volume: 0,
    win_rate: 0,
    profit_factor: 0,
  }
  const positions = Array.isArray(positionsData?.positions) ? positionsData.positions : []

  const totalPnl = portfolio.total_pnl
  const unrealizedPnl = portfolio.unrealized_pnl
  const realizedPnl = portfolio.realized_pnl
  const totalCost = portfolio.total_cost

  const totalPnlVariant = totalPnl >= 0 ? 'success' : 'danger'
  const unrealizedVariant = unrealizedPnl >= 0 ? 'success' : 'danger'
  const realizedVariant = realizedPnl >= 0 ? 'success' : 'danger'

  const formatPnl = (value: number) => {
    const prefix = value >= 0 ? '+' : ''
    return `${prefix}${value}¢`
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl tracking-wider text-white">
            Portfolio <span className="text-neon-cyan">Performance</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">Track profit & loss across all positions</p>
        </div>
        <Button
          variant="primary"
          icon={refreshPnL.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          onClick={() => refreshPnL.mutate()}
          disabled={refreshPnL.isPending}
        >
          Refresh P&L
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total P&L"
          value={formatPnl(totalPnl)}
          icon={totalPnl >= 0 ? TrendingUp : TrendingDown}
          variant={totalPnlVariant}
        />
        <StatCard
          label="Unrealized P&L"
          value={formatPnl(unrealizedPnl)}
          subValue="Paper gains/losses"
          icon={Activity}
          variant={unrealizedVariant}
        />
        <StatCard
          label="Realized P&L"
          value={formatPnl(realizedPnl)}
          subValue="Closed positions"
          icon={DollarSign}
          variant={realizedVariant}
        />
        <StatCard label="Total Cost" value={`${totalCost}¢`} subValue="Capital deployed" icon={Wallet} />
      </div>

      {/* Second Row Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-terminal-bg rounded-lg">
              <BarChart3 className="w-5 h-5 text-neon-purple" />
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Volume</div>
              <div className="font-mono text-xl font-bold text-white">{performance.total_volume}¢</div>
            </div>
          </div>
        </div>

        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-terminal-bg rounded-lg">
              <Target className="w-5 h-5 text-neon-yellow" />
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Win Rate</div>
              <div className="font-mono text-xl font-bold text-neon-green">
                {(performance.win_rate * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-terminal-bg rounded-lg">
              <PieChart className="w-5 h-5 text-neon-cyan" />
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Profit Factor</div>
              <div className="font-mono text-xl font-bold text-white">{performance.profit_factor.toFixed(2)}x</div>
            </div>
          </div>
        </div>

        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-terminal-bg rounded-lg">
              <Activity className="w-5 h-5 text-slate-400" />
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Total Orders</div>
              <div className="font-mono text-xl font-bold text-white">{performance.total_orders}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Position Breakdown */}
      <Panel
        title="Position Breakdown"
        subtitle="P&L by individual position"
        icon={<DollarSign className="w-5 h-5 text-neon-green" />}
        neonBorder
      >
        {positions.length === 0 ? (
          <div className="py-8 text-center text-slate-500 font-mono text-sm">No open positions</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr>
                  <th>Market</th>
                  <th className="text-center">Side</th>
                  <th className="text-right">Quantity</th>
                  <th className="text-right">Cost Basis</th>
                  <th className="text-right">Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position, idx) => {
                  const posUnrealized = position.unrealized_pnl || 0
                  const isProfitable = posUnrealized >= 0
                  const marketName = position.market_ticker.split('-').pop() || position.market_ticker
                  const isYes = position.side.toLowerCase() === 'yes'

                  return (
                    <tr key={position.market_ticker || idx}>
                      <td>
                        <div className="font-mono text-sm text-white">{marketName}</div>
                        <div className="text-[10px] font-mono text-slate-500">{position.market_ticker}</div>
                      </td>
                      <td className="text-center">
                        <Badge variant={isYes ? 'success' : 'danger'}>{position.side.toUpperCase()}</Badge>
                      </td>
                      <td className="text-right font-mono text-white">{position.quantity}</td>
                      <td className="text-right font-mono text-slate-400">{position.total_cost}¢</td>
                      <td
                        className={`text-right font-mono font-bold ${
                          isProfitable ? 'text-neon-green' : 'text-neon-red'
                        }`}
                      >
                        {isProfitable ? '+' : ''}
                        {posUnrealized}¢
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-terminal-border">
                  <td colSpan={3} className="font-semibold text-white">
                    Portfolio Total
                  </td>
                  <td className="text-right font-mono font-semibold text-white">
                    {positions.reduce((sum, p) => sum + p.total_cost, 0)}¢
                  </td>
                  <td
                    className={`text-right font-mono font-bold ${
                      unrealizedPnl >= 0 ? 'text-neon-green text-glow-green' : 'text-neon-red text-glow-red'
                    }`}
                  >
                    {unrealizedPnl >= 0 ? '+' : ''}
                    {unrealizedPnl}¢
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}

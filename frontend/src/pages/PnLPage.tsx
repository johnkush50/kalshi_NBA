import {
  DollarSign,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Wallet,
  Target,
  Activity,
  BarChart3,
  PieChart
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { pnlSummary, openPositions } from '../data/mockData'

function StatCard({
  label,
  value,
  subValue,
  icon: Icon,
  variant = 'default'
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
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">
            {label}
          </div>
          <div className={`font-display text-3xl font-bold ${valueColor[variant]}`}>
            {value}
          </div>
          {subValue && (
            <div className="text-sm font-mono text-slate-400 mt-1">{subValue}</div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${iconBg[variant]}`}>
          <Icon className={`w-6 h-6 ${iconColor[variant]}`} />
        </div>
      </div>
    </div>
  )
}

export default function PnLPage() {
  const totalPnlVariant = pnlSummary.totalPnl >= 0 ? 'success' : 'danger'
  const unrealizedVariant = pnlSummary.unrealizedPnl >= 0 ? 'success' : 'danger'
  const realizedVariant = pnlSummary.realizedPnl >= 0 ? 'success' : 'danger'

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
        <Button variant="primary" icon={<RefreshCw className="w-4 h-4" />}>
          Refresh P&L
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total P&L"
          value={formatPnl(pnlSummary.totalPnl)}
          icon={pnlSummary.totalPnl >= 0 ? TrendingUp : TrendingDown}
          variant={totalPnlVariant}
        />
        <StatCard
          label="Unrealized P&L"
          value={formatPnl(pnlSummary.unrealizedPnl)}
          subValue="Paper gains/losses"
          icon={Activity}
          variant={unrealizedVariant}
        />
        <StatCard
          label="Realized P&L"
          value={formatPnl(pnlSummary.realizedPnl)}
          subValue="Closed positions"
          icon={DollarSign}
          variant={realizedVariant}
        />
        <StatCard
          label="Total Cost"
          value={`${pnlSummary.totalCost}¢`}
          subValue="Capital deployed"
          icon={Wallet}
        />
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
              <div className="font-mono text-xl font-bold text-white">{pnlSummary.tradingVolume}¢</div>
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
              <div className="font-mono text-xl font-bold text-neon-green">{pnlSummary.winRate}%</div>
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
              <div className="font-mono text-xl font-bold text-white">{pnlSummary.profitFactor}x</div>
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
              <div className="font-mono text-xl font-bold text-white">{pnlSummary.totalOrders}</div>
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
        <div className="overflow-x-auto">
          <table className="w-full data-table">
            <thead>
              <tr>
                <th>Market</th>
                <th className="text-center">Side</th>
                <th className="text-right">Quantity</th>
                <th className="text-right">Cost Basis</th>
                <th className="text-right">Current Value</th>
                <th className="text-right">Unrealized P&L</th>
                <th className="text-right">% Return</th>
              </tr>
            </thead>
            <tbody>
              {openPositions.map((position) => {
                const currentValue = position.quantity * position.currentPrice
                const isProfitable = position.unrealizedPnl >= 0

                return (
                  <tr key={position.id}>
                    <td>
                      <div className="font-mono text-sm text-white">{position.marketName}</div>
                      <div className="text-[10px] font-mono text-slate-500">{position.marketTicker}</div>
                    </td>
                    <td className="text-center">
                      <Badge variant={position.side === 'YES' ? 'success' : 'danger'}>
                        {position.side}
                      </Badge>
                    </td>
                    <td className="text-right font-mono text-white">{position.quantity}</td>
                    <td className="text-right font-mono text-slate-400">{position.costBasis}¢</td>
                    <td className="text-right font-mono text-neon-cyan">{currentValue}¢</td>
                    <td className={`text-right font-mono font-bold ${
                      isProfitable ? 'text-neon-green' : 'text-neon-red'
                    }`}>
                      {isProfitable ? '+' : ''}{position.unrealizedPnl}¢
                    </td>
                    <td className={`text-right font-mono ${
                      isProfitable ? 'text-neon-green' : 'text-neon-red'
                    }`}>
                      {isProfitable ? '+' : ''}{position.unrealizedPnlPercent.toFixed(1)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-terminal-border">
                <td colSpan={3} className="font-semibold text-white">Portfolio Total</td>
                <td className="text-right font-mono font-semibold text-white">
                  {openPositions.reduce((sum, p) => sum + p.costBasis, 0)}¢
                </td>
                <td className="text-right font-mono font-semibold text-neon-cyan">
                  {openPositions.reduce((sum, p) => sum + p.quantity * p.currentPrice, 0)}¢
                </td>
                <td className={`text-right font-mono font-bold ${
                  pnlSummary.unrealizedPnl >= 0 ? 'text-neon-green text-glow-green' : 'text-neon-red text-glow-red'
                }`}>
                  {pnlSummary.unrealizedPnl >= 0 ? '+' : ''}{pnlSummary.unrealizedPnl}¢
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Panel>
    </div>
  )
}

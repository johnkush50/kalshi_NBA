import {
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  AlertTriangle,
  Clock,
  Activity,
  DollarSign,
  Package,
  Flame
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { riskStatus, riskLimits } from '../data/mockData'

function ProgressBar({
  current,
  max,
  label,
  variant = 'default'
}: {
  current: number
  max: number
  label: string
  variant?: 'default' | 'warning' | 'danger'
}) {
  const percentage = Math.min((current / max) * 100, 100)

  const barColor = {
    default: 'bg-neon-cyan',
    warning: 'bg-neon-yellow',
    danger: 'bg-neon-red',
  }

  const getVariant = () => {
    if (percentage >= 90) return 'danger'
    if (percentage >= 70) return 'warning'
    return variant
  }

  const actualVariant = getVariant()

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <span className="font-mono text-sm text-slate-400">
          {current} / {max}
        </span>
      </div>
      <div className="h-2 bg-terminal-bg rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor[actualVariant]} transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-right">
        <span className={`text-xs font-mono ${
          actualVariant === 'danger' ? 'text-neon-red' :
          actualVariant === 'warning' ? 'text-neon-yellow' :
          'text-slate-500'
        }`}>
          {percentage.toFixed(1)}% used
        </span>
      </div>
    </div>
  )
}

function RiskLimitRow({ limit }: { limit: typeof riskLimits[0] }) {
  return (
    <tr>
      <td>
        <div className="font-medium text-white">{limit.name}</div>
        <div className="text-xs text-slate-500 mt-0.5">{limit.description}</div>
      </td>
      <td className="text-right">
        <span className="font-mono text-lg font-bold text-neon-cyan">
          {limit.value.toLocaleString()}
        </span>
        <span className="font-mono text-xs text-slate-500 ml-1">{limit.unit}</span>
      </td>
    </tr>
  )
}

export default function RiskPage() {
  const dailyLossPercent = (riskStatus.dailyLoss / 1000) * 100
  const weeklyLossPercent = (riskStatus.weeklyLoss / 5000) * 100
  const ordersPercent = (riskStatus.ordersToday / 50) * 100
  const exposurePercent = (riskStatus.totalExposure / 10000) * 100

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl tracking-wider text-white">
            Risk <span className="text-neon-cyan">Management</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">Monitor and configure trading safeguards</p>
        </div>
        <div className="flex items-center gap-3">
          {riskStatus.enabled ? (
            <>
              <Badge variant="success" pulse>
                <ShieldCheck className="w-3 h-3" />
                Risk Controls Active
              </Badge>
              <Button variant="danger" icon={<ShieldOff className="w-4 h-4" />}>
                Disable
              </Button>
            </>
          ) : (
            <>
              <Badge variant="danger" pulse>
                <ShieldAlert className="w-3 h-3" />
                Risk Controls Disabled
              </Badge>
              <Button variant="success" icon={<ShieldCheck className="w-4 h-4" />}>
                Enable
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Risk Status Overview */}
      <div className="grid grid-cols-4 gap-4">
        {/* Daily Loss */}
        <div className={`bg-terminal-surface/80 rounded-lg border p-5 ${
          dailyLossPercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
        }`}>
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className={`w-5 h-5 ${
              dailyLossPercent >= 80 ? 'text-neon-red' : 'text-slate-400'
            }`} />
            <span className="text-sm font-medium text-slate-300">Daily Loss</span>
          </div>
          <ProgressBar
            current={riskStatus.dailyLoss}
            max={1000}
            label=""
            variant={dailyLossPercent >= 80 ? 'danger' : 'default'}
          />
        </div>

        {/* Weekly Loss */}
        <div className={`bg-terminal-surface/80 rounded-lg border p-5 ${
          weeklyLossPercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
        }`}>
          <div className="flex items-center gap-2 mb-4">
            <Activity className={`w-5 h-5 ${
              weeklyLossPercent >= 80 ? 'text-neon-red' : 'text-slate-400'
            }`} />
            <span className="text-sm font-medium text-slate-300">Weekly Loss</span>
          </div>
          <ProgressBar
            current={riskStatus.weeklyLoss}
            max={5000}
            label=""
          />
        </div>

        {/* Orders Today */}
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">Orders Today</span>
          </div>
          <ProgressBar
            current={riskStatus.ordersToday}
            max={50}
            label=""
          />
        </div>

        {/* Total Exposure */}
        <div className={`bg-terminal-surface/80 rounded-lg border p-5 ${
          exposurePercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
        }`}>
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">Total Exposure</span>
          </div>
          <ProgressBar
            current={riskStatus.totalExposure}
            max={10000}
            label=""
          />
        </div>
      </div>

      {/* Loss Streak & Cooldown */}
      <div className="grid grid-cols-2 gap-4">
        <div className={`bg-terminal-surface/80 rounded-lg border p-5 ${
          riskStatus.lossStreak >= 2 ? 'neon-border-red' : 'border-terminal-border'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${
                riskStatus.lossStreak >= 2 ? 'bg-neon-red/10' : 'bg-terminal-bg'
              }`}>
                <Flame className={`w-6 h-6 ${
                  riskStatus.lossStreak >= 2 ? 'text-neon-red' : 'text-slate-500'
                }`} />
              </div>
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  Loss Streak
                </div>
                <div className={`font-display text-3xl font-bold ${
                  riskStatus.lossStreak >= 2 ? 'text-neon-red' : 'text-white'
                }`}>
                  {riskStatus.lossStreak}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Cooldown triggers at</div>
              <div className="font-mono text-lg font-bold text-white">3 losses</div>
            </div>
          </div>
        </div>

        <div className={`bg-terminal-surface/80 rounded-lg border p-5 ${
          riskStatus.inCooldown ? 'neon-border-red animate-pulse' : 'border-terminal-border'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${
                riskStatus.inCooldown ? 'bg-neon-red/10' : 'bg-terminal-bg'
              }`}>
                <AlertTriangle className={`w-6 h-6 ${
                  riskStatus.inCooldown ? 'text-neon-red' : 'text-slate-500'
                }`} />
              </div>
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  Cooldown Status
                </div>
                <div className={`font-display text-xl font-bold ${
                  riskStatus.inCooldown ? 'text-neon-red' : 'text-neon-green'
                }`}>
                  {riskStatus.inCooldown ? 'IN COOLDOWN' : 'TRADING ACTIVE'}
                </div>
              </div>
            </div>
            {riskStatus.inCooldown && riskStatus.cooldownEndsAt && (
              <div className="text-right">
                <div className="text-xs text-slate-500">Resumes at</div>
                <div className="font-mono text-lg text-neon-red">
                  {new Date(riskStatus.cooldownEndsAt).toLocaleTimeString()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Risk Limits Table */}
      <Panel
        title="Risk Limits Configuration"
        subtitle="All active trading limits"
        icon={<ShieldAlert className="w-5 h-5 text-neon-yellow" />}
        neonBorder
      >
        <div className="overflow-x-auto">
          <table className="w-full data-table">
            <thead>
              <tr>
                <th>Limit Type</th>
                <th className="text-right">Current Value</th>
              </tr>
            </thead>
            <tbody>
              {riskLimits.map((limit) => (
                <RiskLimitRow key={limit.type} limit={limit} />
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}

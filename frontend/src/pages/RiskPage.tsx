import {
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  AlertTriangle,
  Clock,
  Activity,
  DollarSign,
  Package,
  Flame,
  Loader2,
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Loading from '../components/ui/Loading'
import ErrorDisplay from '../components/ui/ErrorDisplay'
import { useRiskStatus, useRiskLimits, useEnableRisk, useDisableRisk } from '../hooks/useRisk'

function ProgressBar({
  current,
  max,
  label,
  variant = 'default',
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
        <span
          className={`text-xs font-mono ${
            actualVariant === 'danger'
              ? 'text-neon-red'
              : actualVariant === 'warning'
                ? 'text-neon-yellow'
                : 'text-slate-500'
          }`}
        >
          {percentage.toFixed(1)}% used
        </span>
      </div>
    </div>
  )
}

function RiskLimitRow({ name, value, unit }: { name: string; value: number; unit?: string }) {
  return (
    <tr>
      <td>
        <div className="font-medium text-white">{name}</div>
      </td>
      <td className="text-right">
        <span className="font-mono text-lg font-bold text-neon-cyan">{value.toLocaleString()}</span>
        {unit && <span className="font-mono text-xs text-slate-500 ml-1">{unit}</span>}
      </td>
    </tr>
  )
}

// Human-readable labels for limit types
const limitLabels: Record<string, { name: string; unit: string }> = {
  max_contracts_per_market: { name: 'Max Contracts/Market', unit: 'contracts' },
  max_contracts_per_game: { name: 'Max Contracts/Game', unit: 'contracts' },
  max_total_contracts: { name: 'Max Total Contracts', unit: 'contracts' },
  max_daily_loss: { name: 'Max Daily Loss', unit: '¢' },
  max_weekly_loss: { name: 'Max Weekly Loss', unit: '¢' },
  max_per_trade_risk: { name: 'Max Per-Trade Risk', unit: '¢' },
  max_total_exposure: { name: 'Max Total Exposure', unit: '¢' },
  max_exposure_per_game: { name: 'Max Exposure/Game', unit: '¢' },
  max_exposure_per_strategy: { name: 'Max Exposure/Strategy', unit: '¢' },
  max_orders_per_day: { name: 'Max Orders/Day', unit: 'orders' },
  max_orders_per_hour: { name: 'Max Orders/Hour', unit: 'orders' },
  loss_streak_cooldown: { name: 'Loss Streak Cooldown', unit: 'losses' },
}

export default function RiskPage() {
  const { data: statusData, isLoading: isLoadingStatus, error: statusError, refetch: refetchStatus } = useRiskStatus()
  const { data: limitsData, isLoading: isLoadingLimits } = useRiskLimits()
  const enableRisk = useEnableRisk()
  const disableRisk = useDisableRisk()

  const isLoading = isLoadingStatus || isLoadingLimits

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-2xl tracking-wider text-white">
              Risk <span className="text-neon-cyan">Management</span>
            </h1>
          </div>
        </div>
        <Loading message="Loading risk data..." />
      </div>
    )
  }

  if (statusError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display font-bold text-2xl tracking-wider text-white">
              Risk <span className="text-neon-cyan">Management</span>
            </h1>
          </div>
        </div>
        <ErrorDisplay
          message={statusError instanceof Error ? statusError.message : 'Failed to load risk data'}
          onRetry={() => refetchStatus()}
        />
      </div>
    )
  }

  const riskStatus = statusData || {
    enabled: false,
    daily_loss: 0,
    weekly_loss: 0,
    orders_today: 0,
    orders_this_hour: 0,
    loss_streak: 0,
    in_cooldown: false,
    cooldown_ends_at: null,
    total_exposure: 0,
  }

  const limits = limitsData?.limits || {}

  // Get limits with fallbacks
  const maxDailyLoss = limits.max_daily_loss || 1000
  const maxWeeklyLoss = limits.max_weekly_loss || 5000
  const maxOrdersDay = limits.max_orders_per_day || 50
  const maxExposure = limits.max_total_exposure || 10000
  const lossStreakCooldown = limits.loss_streak_cooldown || 3

  const dailyLossPercent = (riskStatus.daily_loss / maxDailyLoss) * 100
  const weeklyLossPercent = (riskStatus.weekly_loss / maxWeeklyLoss) * 100
  const exposurePercent = (riskStatus.total_exposure / maxExposure) * 100

  const handleToggleRisk = () => {
    if (riskStatus.enabled) {
      disableRisk.mutate()
    } else {
      enableRisk.mutate()
    }
  }

  const isTogglingRisk = enableRisk.isPending || disableRisk.isPending

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
              <Button
                variant="danger"
                icon={isTogglingRisk ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldOff className="w-4 h-4" />}
                onClick={handleToggleRisk}
                disabled={isTogglingRisk}
              >
                Disable
              </Button>
            </>
          ) : (
            <>
              <Badge variant="danger" pulse>
                <ShieldAlert className="w-3 h-3" />
                Risk Controls Disabled
              </Badge>
              <Button
                variant="success"
                icon={isTogglingRisk ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                onClick={handleToggleRisk}
                disabled={isTogglingRisk}
              >
                Enable
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Risk Status Overview */}
      <div className="grid grid-cols-4 gap-4">
        {/* Daily Loss */}
        <div
          className={`bg-terminal-surface/80 rounded-lg border p-5 ${
            dailyLossPercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
          }`}
        >
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className={`w-5 h-5 ${dailyLossPercent >= 80 ? 'text-neon-red' : 'text-slate-400'}`} />
            <span className="text-sm font-medium text-slate-300">Daily Loss</span>
          </div>
          <ProgressBar
            current={riskStatus.daily_loss}
            max={maxDailyLoss}
            label=""
            variant={dailyLossPercent >= 80 ? 'danger' : 'default'}
          />
        </div>

        {/* Weekly Loss */}
        <div
          className={`bg-terminal-surface/80 rounded-lg border p-5 ${
            weeklyLossPercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
          }`}
        >
          <div className="flex items-center gap-2 mb-4">
            <Activity className={`w-5 h-5 ${weeklyLossPercent >= 80 ? 'text-neon-red' : 'text-slate-400'}`} />
            <span className="text-sm font-medium text-slate-300">Weekly Loss</span>
          </div>
          <ProgressBar current={riskStatus.weekly_loss} max={maxWeeklyLoss} label="" />
        </div>

        {/* Orders Today */}
        <div className="bg-terminal-surface/80 rounded-lg border border-terminal-border p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">Orders Today</span>
          </div>
          <ProgressBar current={riskStatus.orders_today} max={maxOrdersDay} label="" />
        </div>

        {/* Total Exposure */}
        <div
          className={`bg-terminal-surface/80 rounded-lg border p-5 ${
            exposurePercent >= 80 ? 'neon-border-red' : 'border-terminal-border'
          }`}
        >
          <div className="flex items-center gap-2 mb-4">
            <Package className="w-5 h-5 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">Total Exposure</span>
          </div>
          <ProgressBar current={riskStatus.total_exposure} max={maxExposure} label="" />
        </div>
      </div>

      {/* Loss Streak & Cooldown */}
      <div className="grid grid-cols-2 gap-4">
        <div
          className={`bg-terminal-surface/80 rounded-lg border p-5 ${
            riskStatus.loss_streak >= lossStreakCooldown - 1 ? 'neon-border-red' : 'border-terminal-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={`p-3 rounded-lg ${
                  riskStatus.loss_streak >= lossStreakCooldown - 1 ? 'bg-neon-red/10' : 'bg-terminal-bg'
                }`}
              >
                <Flame
                  className={`w-6 h-6 ${
                    riskStatus.loss_streak >= lossStreakCooldown - 1 ? 'text-neon-red' : 'text-slate-500'
                  }`}
                />
              </div>
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Loss Streak</div>
                <div
                  className={`font-display text-3xl font-bold ${
                    riskStatus.loss_streak >= lossStreakCooldown - 1 ? 'text-neon-red' : 'text-white'
                  }`}
                >
                  {riskStatus.loss_streak}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">Cooldown triggers at</div>
              <div className="font-mono text-lg font-bold text-white">{lossStreakCooldown} losses</div>
            </div>
          </div>
        </div>

        <div
          className={`bg-terminal-surface/80 rounded-lg border p-5 ${
            riskStatus.in_cooldown ? 'neon-border-red animate-pulse' : 'border-terminal-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${riskStatus.in_cooldown ? 'bg-neon-red/10' : 'bg-terminal-bg'}`}>
                <AlertTriangle className={`w-6 h-6 ${riskStatus.in_cooldown ? 'text-neon-red' : 'text-slate-500'}`} />
              </div>
              <div>
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Cooldown Status</div>
                <div
                  className={`font-display text-xl font-bold ${riskStatus.in_cooldown ? 'text-neon-red' : 'text-neon-green'}`}
                >
                  {riskStatus.in_cooldown ? 'IN COOLDOWN' : 'TRADING ACTIVE'}
                </div>
              </div>
            </div>
            {riskStatus.in_cooldown && riskStatus.cooldown_ends_at && (
              <div className="text-right">
                <div className="text-xs text-slate-500">Resumes at</div>
                <div className="font-mono text-lg text-neon-red">
                  {new Date(riskStatus.cooldown_ends_at).toLocaleTimeString()}
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
              {Object.entries(limits).map(([type, value]) => {
                const label = limitLabels[type] || { name: type, unit: '' }
                return <RiskLimitRow key={type} name={label.name} value={value as number} unit={label.unit} />
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}

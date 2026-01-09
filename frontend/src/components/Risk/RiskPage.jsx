import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Settings
} from 'lucide-react'
import { getRiskStatus, getRiskLimits, enableRisk, disableRisk } from '../../api/client'
import { formatCents } from '../../utils/formatters'

export default function RiskPage() {
  const queryClient = useQueryClient()
  
  const { data: statusData, isLoading: loadingStatus } = useQuery({
    queryKey: ['riskStatus'],
    queryFn: getRiskStatus,
  })
  
  const { data: limitsData, isLoading: loadingLimits } = useQuery({
    queryKey: ['riskLimits'],
    queryFn: getRiskLimits,
  })
  
  const enableMutation = useMutation({
    mutationFn: enableRisk,
    onSuccess: () => queryClient.invalidateQueries(['riskStatus']),
  })
  
  const disableMutation = useMutation({
    mutationFn: disableRisk,
    onSuccess: () => queryClient.invalidateQueries(['riskStatus']),
  })
  
  const status = statusData || {}
  const limits = limitsData?.limits || {}
  const isEnabled = status.enabled
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className={`w-8 h-8 ${isEnabled ? 'text-green-400' : 'text-red-400'}`} />
          <div>
            <h2 className="text-2xl font-bold">Risk Management</h2>
            <p className="text-gray-400">
              {isEnabled ? 'Risk controls are active' : 'Risk controls are disabled'}
            </p>
          </div>
        </div>
        
        {isEnabled ? (
          <button
            onClick={() => disableMutation.mutate()}
            disabled={disableMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded"
          >
            <XCircle className="w-4 h-4" />
            Disable Risk Controls
          </button>
        ) : (
          <button
            onClick={() => enableMutation.mutate()}
            disabled={enableMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded"
          >
            <CheckCircle className="w-4 h-4" />
            Enable Risk Controls
          </button>
        )}
      </div>
      
      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatusCard
          title="Daily Loss"
          current={status.daily_loss || 0}
          limit={limits.max_daily_loss}
          format="cents"
        />
        <StatusCard
          title="Weekly Loss"
          current={status.weekly_loss || 0}
          limit={limits.max_weekly_loss}
          format="cents"
        />
        <StatusCard
          title="Orders Today"
          current={status.orders_today || 0}
          limit={limits.max_orders_per_day}
        />
        <StatusCard
          title="Total Exposure"
          current={status.total_exposure || 0}
          limit={limits.max_total_exposure}
          format="cents"
        />
      </div>
      
      {/* Cooldown Warning */}
      {status.cooldown_active && (
        <div className="bg-yellow-600/20 border border-yellow-600 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-yellow-400" />
          <div>
            <p className="font-semibold text-yellow-400">Loss Streak Cooldown Active</p>
            <p className="text-sm text-gray-300">
              {status.consecutive_losses} consecutive losses. Trading paused until{' '}
              {new Date(status.cooldown_until).toLocaleTimeString()}
            </p>
          </div>
        </div>
      )}
      
      {/* Risk Limits Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h3 className="font-semibold">Risk Limits Configuration</h3>
        </div>
        
        {loadingLimits ? (
          <div className="p-8 text-center text-gray-400">Loading limits...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                <th className="px-4 py-3">Limit Type</th>
                <th className="px-4 py-3 text-right">Value</th>
                <th className="px-4 py-3">Description</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(limits).map(([key, value]) => (
                <tr key={key} className="border-b border-gray-700 last:border-0 hover:bg-gray-750">
                  <td className="px-4 py-3 font-mono text-sm">{key}</td>
                  <td className="px-4 py-3 text-right">
                    {key.includes('loss') || key.includes('exposure') || key.includes('risk')
                      ? formatCents(value)
                      : value}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-sm">
                    {getLimitDescription(key)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function StatusCard({ title, current, limit, format }) {
  const percentage = limit > 0 ? (current / limit) * 100 : 0
  const isWarning = percentage >= 80
  const isDanger = percentage >= 100
  
  const barColor = isDanger ? 'bg-red-500' : isWarning ? 'bg-yellow-500' : 'bg-green-500'
  
  const displayCurrent = format === 'cents' ? formatCents(current) : current
  const displayLimit = format === 'cents' ? formatCents(limit) : limit
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{title}</span>
        <span className={`text-xs ${isDanger ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-gray-400'}`}>
          {percentage.toFixed(0)}%
        </span>
      </div>
      <p className="text-xl font-bold mb-2">
        {displayCurrent} <span className="text-gray-500 text-sm">/ {displayLimit}</span>
      </p>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColor} transition-all`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

function getLimitDescription(key) {
  const descriptions = {
    max_contracts_per_market: 'Maximum contracts in a single market',
    max_contracts_per_game: 'Maximum contracts across all markets in a game',
    max_total_contracts: 'Maximum total contracts across all positions',
    max_daily_loss: 'Maximum loss allowed per day',
    max_weekly_loss: 'Maximum loss allowed per week',
    max_per_trade_risk: 'Maximum risk per individual trade',
    max_total_exposure: 'Maximum total capital at risk',
    max_exposure_per_game: 'Maximum exposure in a single game',
    max_exposure_per_strategy: 'Maximum exposure per strategy',
    max_orders_per_day: 'Maximum orders per day',
    max_orders_per_hour: 'Maximum orders per hour',
    loss_streak_cooldown: 'Consecutive losses before trading pause',
  }
  return descriptions[key] || ''
}

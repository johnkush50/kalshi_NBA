import { useState } from 'react'
import {
  Brain,
  Plus,
  Power,
  PowerOff,
  ChevronDown,
  ChevronRight,
  Zap,
  Target,
  ArrowUp,
  ArrowDown,
  Loader2,
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Loading from '../components/ui/Loading'
import ErrorDisplay from '../components/ui/ErrorDisplay'
import {
  useStrategies,
  useEnableStrategy,
  useDisableStrategy,
  useStrategyTypes,
  useLoadStrategy,
} from '../hooks/useStrategies'
import { useWebSocketContext } from '../context/WebSocketContext'
import type { Strategy, Signal, StrategyType } from '../api/types'

function StrategyCard({
  strategy,
  onEnable,
  onDisable,
  isTogglingId,
}: {
  strategy: Strategy
  onEnable: () => void
  onDisable: () => void
  isTogglingId: string | null
}) {
  const [expanded, setExpanded] = useState(false)
  const isToggling = isTogglingId === strategy.strategy_id

  return (
    <div
      className={`bg-terminal-bg/50 rounded-lg border ${
        strategy.is_enabled ? 'border-neon-green/30' : 'border-terminal-border'
      } overflow-hidden transition-all`}
    >
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-4">
          <button className="p-1" onClick={() => setExpanded(!expanded)}>
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>

          <div
            className={`p-2 rounded-md ${strategy.is_enabled ? 'bg-neon-green/10' : 'bg-terminal-bg'}`}
          >
            <Brain className={`w-5 h-5 ${strategy.is_enabled ? 'text-neon-green' : 'text-slate-500'}`} />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">{strategy.strategy_name}</span>
              {strategy.is_enabled ? (
                <Badge variant="success" pulse>
                  Active
                </Badge>
              ) : (
                <Badge variant="default">Disabled</Badge>
              )}
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
              <span className="font-mono">{strategy.strategy_type}</span>
              <span>•</span>
              <span className="font-mono">{strategy.strategy_id.slice(0, 8)}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {strategy.is_enabled ? (
            <Button
              variant="danger"
              size="sm"
              icon={isToggling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PowerOff className="w-3.5 h-3.5" />}
              onClick={onDisable}
              disabled={isToggling}
            >
              Disable
            </Button>
          ) : (
            <Button
              variant="success"
              size="sm"
              icon={isToggling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Power className="w-3.5 h-3.5" />}
              onClick={onEnable}
              disabled={isToggling}
            >
              Enable
            </Button>
          )}
        </div>
      </div>

      {/* Configuration */}
      {expanded && (
        <div className="px-4 py-3 bg-terminal-bg/30 border-t border-terminal-border/50">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2">
            Configuration
          </div>
          <pre className="font-mono text-xs text-slate-300 bg-terminal-bg rounded-md p-3 overflow-x-auto">
            {JSON.stringify(strategy.config, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function SignalRow({ signal }: { signal: Signal }) {
  const timeAgo = (timestamp: string) => {
    const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ago`
  }

  const isYes = signal.side.toLowerCase() === 'yes'

  return (
    <div className="flex items-center gap-4 p-3 rounded-lg border bg-terminal-bg/30 border-terminal-border/50">
      {/* Side indicator */}
      <div
        className={`flex items-center justify-center w-10 h-10 rounded-md ${
          isYes ? 'bg-neon-green/10' : 'bg-neon-red/10'
        }`}
      >
        {isYes ? (
          <ArrowUp className="w-5 h-5 text-neon-green" />
        ) : (
          <ArrowDown className="w-5 h-5 text-neon-red" />
        )}
      </div>

      {/* Signal details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">{signal.strategy_name}</span>
          <span className="text-slate-600">•</span>
          <span className={`font-mono font-bold ${isYes ? 'text-neon-green' : 'text-neon-red'}`}>
            {signal.side.toUpperCase()} {signal.quantity}
          </span>
        </div>
        <div className="text-xs font-mono text-slate-500 truncate mt-0.5">{signal.market_ticker}</div>
        <div className="text-xs text-slate-400 mt-1 line-clamp-1">{signal.reason}</div>
      </div>

      {/* Confidence & Status */}
      <div className="flex flex-col items-end gap-1">
        <div className="flex items-center gap-2">
          <Target className="w-3 h-3 text-slate-500" />
          <span className="font-mono text-sm text-neon-cyan">{(signal.confidence * 100).toFixed(0)}%</span>
        </div>
        <span className="text-[10px] font-mono text-slate-600">{timeAgo(signal.timestamp)}</span>
      </div>
    </div>
  )
}

function LoadStrategyModal({
  isOpen,
  onClose,
  strategyTypes,
  onLoad,
  isLoading,
}: {
  isOpen: boolean
  onClose: () => void
  strategyTypes: StrategyType[]
  onLoad: (type: string, enable: boolean) => void
  isLoading: boolean
}) {
  const [selectedType, setSelectedType] = useState('')
  const [enableOnLoad, setEnableOnLoad] = useState(false)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-terminal-surface border border-terminal-border rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="font-display font-bold text-lg text-white mb-4">Load Strategy</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2">Strategy Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full bg-terminal-bg border border-terminal-border rounded-md px-3 py-2 font-mono text-sm text-white focus:border-neon-cyan focus:outline-none"
            >
              <option value="">Select a strategy...</option>
              {strategyTypes.map((type) => (
                <option key={type.type} value={type.type}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          {selectedType && (
            <div className="bg-terminal-bg/50 rounded-md p-3">
              <div className="text-xs text-slate-400">
                {strategyTypes.find((t) => t.type === selectedType)?.description}
              </div>
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableOnLoad}
              onChange={(e) => setEnableOnLoad(e.target.checked)}
              className="w-4 h-4 rounded border-terminal-border bg-terminal-bg"
            />
            <span className="text-sm text-slate-300">Enable immediately after loading</span>
          </label>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!selectedType || isLoading}
            onClick={() => onLoad(selectedType, enableOnLoad)}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Load Strategy'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function StrategiesPage() {
  const [showLoadModal, setShowLoadModal] = useState(false)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const { data: strategiesData, isLoading, error, refetch } = useStrategies()
  const { data: typesData } = useStrategyTypes()
  const enableStrategy = useEnableStrategy()
  const disableStrategy = useDisableStrategy()
  const loadStrategy = useLoadStrategy()
  const { isConnected, lastSignal } = useWebSocketContext()

  const strategies = strategiesData?.strategies || []
  const strategyTypes = typesData?.strategy_types || []
  const activeCount = strategies.filter((s) => s.is_enabled).length

  // Collect signals from WebSocket
  const [signals, setSignals] = useState<Signal[]>([])

  // Add new signal when received
  if (lastSignal && !signals.find((s) => s.id === lastSignal.id)) {
    setSignals((prev) => [lastSignal, ...prev.slice(0, 19)])
  }

  const handleEnable = async (strategyId: string) => {
    setTogglingId(strategyId)
    try {
      await enableStrategy.mutateAsync(strategyId)
    } finally {
      setTogglingId(null)
    }
  }

  const handleDisable = async (strategyId: string) => {
    setTogglingId(strategyId)
    try {
      await disableStrategy.mutateAsync(strategyId)
    } finally {
      setTogglingId(null)
    }
  }

  const handleLoadStrategy = async (type: string, enable: boolean) => {
    await loadStrategy.mutateAsync({ strategyType: type, enable })
    setShowLoadModal(false)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl tracking-wider text-white">
            Trading <span className="text-neon-cyan">Strategies</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">Manage automated trading algorithms</p>
        </div>
        <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={() => setShowLoadModal(true)}>
          Load Strategy
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Strategies List */}
        <div className="col-span-7">
          <Panel
            title="Loaded Strategies"
            subtitle={`${activeCount} active of ${strategies.length}`}
            icon={<Brain className="w-5 h-5 text-neon-purple" />}
            neonBorder
          >
            {isLoading ? (
              <Loading message="Loading strategies..." />
            ) : error ? (
              <ErrorDisplay
                message={error instanceof Error ? error.message : 'Failed to load strategies'}
                onRetry={() => refetch()}
              />
            ) : strategies.length === 0 ? (
              <div className="py-8 text-center text-slate-500 font-mono text-sm">
                No strategies loaded. Click "Load Strategy" to add one.
              </div>
            ) : (
              <div className="space-y-3">
                {strategies.map((strategy) => (
                  <StrategyCard
                    key={strategy.strategy_id}
                    strategy={strategy}
                    onEnable={() => handleEnable(strategy.strategy_id)}
                    onDisable={() => handleDisable(strategy.strategy_id)}
                    isTogglingId={togglingId}
                  />
                ))}
              </div>
            )}
          </Panel>
        </div>

        {/* Live Signals Feed */}
        <div className="col-span-5">
          <Panel
            title="Live Signals"
            subtitle="Real-time strategy output"
            icon={<Zap className="w-5 h-5 text-neon-yellow" />}
            headerAction={
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${isConnected ? 'bg-neon-green animate-pulse' : 'bg-neon-red'}`}
                />
                <span className="text-xs font-mono text-slate-500">
                  {isConnected ? 'Streaming' : 'Disconnected'}
                </span>
              </div>
            }
          >
            {signals.length === 0 ? (
              <div className="py-8 text-center text-slate-500 font-mono text-sm">
                Waiting for signals...
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {signals.map((signal, idx) => (
                  <SignalRow key={signal.id || idx} signal={signal} />
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>

      {/* Load Strategy Modal */}
      <LoadStrategyModal
        isOpen={showLoadModal}
        onClose={() => setShowLoadModal(false)}
        strategyTypes={strategyTypes}
        onLoad={handleLoadStrategy}
        isLoading={loadStrategy.isPending}
      />
    </div>
  )
}

import { useState } from 'react'
import {
  Brain,
  Plus,
  Power,
  PowerOff,
  ChevronDown,
  ChevronRight,
  Zap,
  Clock,
  Target,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { strategies, recentSignals, type Strategy, type Signal } from '../data/mockData'

function StrategyCard({ strategy }: { strategy: Strategy }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`bg-terminal-bg/50 rounded-lg border ${
      strategy.enabled ? 'border-neon-green/30' : 'border-terminal-border'
    } overflow-hidden transition-all`}>
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-4">
          <button
            className="p-1"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>

          <div className={`p-2 rounded-md ${
            strategy.enabled ? 'bg-neon-green/10' : 'bg-terminal-bg'
          }`}>
            <Brain className={`w-5 h-5 ${
              strategy.enabled ? 'text-neon-green' : 'text-slate-500'
            }`} />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">{strategy.name}</span>
              {strategy.enabled ? (
                <Badge variant="success" pulse>Active</Badge>
              ) : (
                <Badge variant="default">Disabled</Badge>
              )}
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
              <span className="font-mono">{strategy.type}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                {strategy.signalCount} signals
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right mr-4">
            <div className="text-[10px] font-mono text-slate-500 uppercase">Last Eval</div>
            <div className="text-xs font-mono text-slate-400">
              {new Date(strategy.lastEvaluation).toLocaleTimeString()}
            </div>
          </div>

          {strategy.enabled ? (
            <Button variant="danger" size="sm" icon={<PowerOff className="w-3.5 h-3.5" />}>
              Disable
            </Button>
          ) : (
            <Button variant="success" size="sm" icon={<Power className="w-3.5 h-3.5" />}>
              Enable
            </Button>
          )}
        </div>
      </div>

      {/* Configuration */}
      {expanded && (
        <div className="px-4 py-3 bg-terminal-bg/30 border-t border-terminal-border/50">
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2">Configuration</div>
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

  return (
    <div className={`flex items-center gap-4 p-3 rounded-lg border ${
      signal.executed ? 'bg-terminal-bg/30 border-terminal-border/50' : 'bg-neon-cyan/5 border-neon-cyan/20'
    }`}>
      {/* Side indicator */}
      <div className={`flex items-center justify-center w-10 h-10 rounded-md ${
        signal.side === 'YES' ? 'bg-neon-green/10' : 'bg-neon-red/10'
      }`}>
        {signal.side === 'YES' ? (
          <ArrowUp className="w-5 h-5 text-neon-green" />
        ) : (
          <ArrowDown className="w-5 h-5 text-neon-red" />
        )}
      </div>

      {/* Signal details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">{signal.strategyName}</span>
          <span className="text-slate-600">•</span>
          <span className={`font-mono font-bold ${
            signal.side === 'YES' ? 'text-neon-green' : 'text-neon-red'
          }`}>
            {signal.side} {signal.quantity}
          </span>
        </div>
        <div className="text-xs font-mono text-slate-500 truncate mt-0.5">
          {signal.marketTicker}
        </div>
        <div className="text-xs text-slate-400 mt-1 line-clamp-1">
          {signal.reason}
        </div>
      </div>

      {/* Confidence & Status */}
      <div className="flex flex-col items-end gap-1">
        <div className="flex items-center gap-2">
          <Target className="w-3 h-3 text-slate-500" />
          <span className="font-mono text-sm text-neon-cyan">{(signal.confidence * 100).toFixed(0)}%</span>
        </div>
        {signal.executed ? (
          <Badge variant="success" size="sm">Executed</Badge>
        ) : (
          <Badge variant="warning" size="sm">Pending</Badge>
        )}
        <span className="text-[10px] font-mono text-slate-600">{timeAgo(signal.timestamp)}</span>
      </div>
    </div>
  )
}

export default function StrategiesPage() {
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
        <Button variant="primary" icon={<Plus className="w-4 h-4" />}>
          Load Strategy
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Strategies List */}
        <div className="col-span-7">
          <Panel
            title="Loaded Strategies"
            subtitle={`${strategies.filter(s => s.enabled).length} active of ${strategies.length}`}
            icon={<Brain className="w-5 h-5 text-neon-purple" />}
            neonBorder
          >
            <div className="space-y-3">
              {strategies.map((strategy) => (
                <StrategyCard key={strategy.id} strategy={strategy} />
              ))}
            </div>
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
                <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
                <span className="text-xs font-mono text-slate-500">Streaming</span>
              </div>
            }
          >
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {recentSignals.map((signal) => (
                <SignalRow key={signal.id} signal={signal} />
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}

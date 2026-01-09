import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Brain, 
  Play, 
  Pause, 
  Plus, 
  ChevronDown,
  ChevronUp,
  Settings
} from 'lucide-react'
import { 
  getStrategies, 
  getStrategyTypes, 
  loadStrategy,
  enableStrategy,
  disableStrategy
} from '../../api/client'

export default function StrategyList() {
  const [showLoader, setShowLoader] = useState(false)
  const [selectedType, setSelectedType] = useState('')
  const queryClient = useQueryClient()
  
  const { data: strategiesData, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
  })
  
  const { data: typesData } = useQuery({
    queryKey: ['strategyTypes'],
    queryFn: getStrategyTypes,
  })
  
  const loadMutation = useMutation({
    mutationFn: ({ type, enable }) => loadStrategy(type, {}, enable),
    onSuccess: () => {
      queryClient.invalidateQueries(['strategies'])
      setShowLoader(false)
      setSelectedType('')
    },
  })
  
  const enableMutation = useMutation({
    mutationFn: enableStrategy,
    onSuccess: () => queryClient.invalidateQueries(['strategies']),
  })
  
  const disableMutation = useMutation({
    mutationFn: disableStrategy,
    onSuccess: () => queryClient.invalidateQueries(['strategies']),
  })
  
  const strategies = strategiesData?.strategies || []
  const strategyTypes = typesData?.strategy_types || []
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Trading Strategies</h2>
          <p className="text-gray-400">{strategies.length} strategies loaded</p>
        </div>
        <button
          onClick={() => setShowLoader(!showLoader)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
        >
          <Plus className="w-4 h-4" />
          Load Strategy
        </button>
      </div>
      
      {/* Strategy Loader */}
      {showLoader && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <h3 className="font-semibold mb-4">Load New Strategy</h3>
          <div className="flex gap-4">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2"
            >
              <option value="">Select strategy type...</option>
              {strategyTypes.map((st) => (
                <option key={st.type} value={st.type}>{st.name}</option>
              ))}
            </select>
            <button
              onClick={() => loadMutation.mutate({ type: selectedType, enable: false })}
              disabled={!selectedType || loadMutation.isPending}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
            >
              Load
            </button>
            <button
              onClick={() => loadMutation.mutate({ type: selectedType, enable: true })}
              disabled={!selectedType || loadMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
            >
              Load & Enable
            </button>
          </div>
        </div>
      )}
      
      {/* Strategies List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading strategies...</div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-12 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
          <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg">No strategies loaded</p>
          <p className="text-sm mt-2">Click "Load Strategy" to add one</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {strategies.map((strategy) => (
            <StrategyCard
              key={strategy.strategy_id}
              strategy={strategy}
              onEnable={() => enableMutation.mutate(strategy.strategy_id)}
              onDisable={() => disableMutation.mutate(strategy.strategy_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function StrategyCard({ strategy, onEnable, onDisable }) {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className={`w-6 h-6 ${strategy.is_enabled ? 'text-green-400' : 'text-gray-400'}`} />
            <div>
              <h3 className="font-semibold">{strategy.strategy_name}</h3>
              <p className="text-sm text-gray-400">{strategy.strategy_type}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 text-xs rounded ${
              strategy.is_enabled 
                ? 'bg-green-600/20 text-green-400' 
                : 'bg-gray-600/20 text-gray-400'
            }`}>
              {strategy.is_enabled ? 'Enabled' : 'Disabled'}
            </span>
            
            {strategy.is_enabled ? (
              <button
                onClick={onDisable}
                className="p-2 hover:bg-gray-700 rounded"
                title="Disable"
              >
                <Pause className="w-4 h-4 text-yellow-400" />
              </button>
            ) : (
              <button
                onClick={onEnable}
                className="p-2 hover:bg-gray-700 rounded"
                title="Enable"
              >
                <Play className="w-4 h-4 text-green-400" />
              </button>
            )}
            
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 hover:bg-gray-700 rounded"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>
        
        {/* Recent Signals */}
        {strategy.recent_signals?.length > 0 && (
          <div className="mt-3 text-sm text-gray-400">
            Recent signals: {strategy.recent_signals.length}
          </div>
        )}
      </div>
      
      {/* Expanded Config */}
      {expanded && (
        <div className="border-t border-gray-700 p-4 bg-gray-750">
          <h4 className="text-sm font-medium text-gray-400 mb-2 flex items-center gap-1">
            <Settings className="w-4 h-4" /> Configuration
          </h4>
          <pre className="text-xs bg-gray-900 p-3 rounded overflow-x-auto">
            {JSON.stringify(strategy.config, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

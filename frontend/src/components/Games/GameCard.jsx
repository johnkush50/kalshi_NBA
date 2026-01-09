import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Square, ChevronDown, ChevronUp } from 'lucide-react'
import { loadGame, unloadGame } from '../../api/client'
import { formatPercent } from '../../utils/formatters'
import MarketTable from './MarketTable'

export default function GameCard({ game, isLoaded = false }) {
  const [expanded, setExpanded] = useState(false)
  const queryClient = useQueryClient()
  
  const loadMutation = useMutation({
    mutationFn: () => loadGame(game.game_id || game.id),
    onSuccess: () => queryClient.invalidateQueries(['loadedGames']),
  })
  
  const unloadMutation = useMutation({
    mutationFn: () => unloadGame(game.game_id),
    onSuccess: () => queryClient.invalidateQueries(['loadedGames']),
  })
  
  const homeTeam = game.home_team
  const awayTeam = game.away_team
  const consensus = game.consensus
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">
              {awayTeam} @ {homeTeam}
            </h3>
            <p className="text-sm text-gray-400">{game.event_ticker}</p>
          </div>
          
          <div className="flex items-center gap-2">
            {isLoaded ? (
              <button
                onClick={() => unloadMutation.mutate()}
                disabled={unloadMutation.isPending}
                className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded text-sm"
              >
                <Square className="w-4 h-4" />
                Unload
              </button>
            ) : (
              <button
                onClick={() => loadMutation.mutate()}
                disabled={loadMutation.isPending}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded text-sm"
              >
                <Play className="w-4 h-4" />
                Load
              </button>
            )}
          </div>
        </div>
        
        {consensus && (
          <div className="mt-3 flex gap-4 text-sm">
            <div className="bg-gray-700 px-3 py-1 rounded">
              <span className="text-gray-400">Home:</span>{' '}
              <span className="font-medium">{formatPercent(consensus.home_win_probability * 100)}</span>
            </div>
            <div className="bg-gray-700 px-3 py-1 rounded">
              <span className="text-gray-400">Away:</span>{' '}
              <span className="font-medium">{formatPercent(consensus.away_win_probability * 100)}</span>
            </div>
            <div className="bg-gray-700 px-3 py-1 rounded">
              <span className="text-gray-400">Books:</span>{' '}
              <span className="font-medium">{consensus.num_sportsbooks}</span>
            </div>
          </div>
        )}
        
        {isLoaded && game.markets && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-3 flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {Object.keys(game.markets).length} Markets
          </button>
        )}
      </div>
      
      {expanded && game.markets && (
        <div className="border-t border-gray-700">
          <MarketTable markets={game.markets} gameId={game.game_id} />
        </div>
      )}
    </div>
  )
}

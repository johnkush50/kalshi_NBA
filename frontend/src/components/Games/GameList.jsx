import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Calendar, Plus, Loader2 } from 'lucide-react'
import { getLoadedGames, getAvailableGames, loadGameByTicker } from '../../api/client'
import GameCard from './GameCard'

export default function GameList() {
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [showAvailable, setShowAvailable] = useState(false)
  const queryClient = useQueryClient()
  
  const { data: loadedData, isLoading: loadingGames, refetch } = useQuery({
    queryKey: ['loadedGames'],
    queryFn: getLoadedGames,
  })
  
  const { data: availableData, isLoading: loadingAvailable } = useQuery({
    queryKey: ['availableGames', selectedDate],
    queryFn: () => getAvailableGames(selectedDate),
    enabled: showAvailable,
  })
  
  const loadMutation = useMutation({
    mutationFn: (eventTicker) => loadGameByTicker(eventTicker),
    onSuccess: () => {
      queryClient.invalidateQueries(['loadedGames'])
      queryClient.invalidateQueries(['availableGames'])
    },
  })
  
  const loadedGames = loadedData?.games ? Object.values(loadedData.games) : []
  const availableGames = availableData?.games || []
  
  return (
    <div className="space-y-8">
      {/* Active Games Section */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Active Games</h2>
            <p className="text-gray-400">{loadedGames.length} games loaded</p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
        
        {loadingGames ? (
          <div className="text-center py-12 text-gray-400">Loading games...</div>
        ) : loadedGames.length === 0 ? (
          <div className="text-center py-12 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-lg">No games loaded</p>
            <p className="text-sm mt-2">Browse available games below to get started</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {loadedGames.map((game) => (
              <GameCard key={game.game_id} game={game} isLoaded={true} />
            ))}
          </div>
        )}
      </section>
      
      {/* Browse Available Games Section */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Browse Games</h2>
            <p className="text-gray-400">Find and load games from Kalshi</p>
          </div>
          <button
            onClick={() => setShowAvailable(!showAvailable)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
          >
            {showAvailable ? 'Hide' : 'Show'} Available Games
          </button>
        </div>
        
        {showAvailable && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            {/* Date Picker */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-gray-400" />
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
              <span className="text-gray-400">
                {availableGames.length} games found
              </span>
            </div>
            
            {/* Available Games List */}
            {loadingAvailable ? (
              <div className="flex items-center justify-center py-8 text-gray-400">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Loading available games...
              </div>
            ) : availableGames.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No games found for this date
              </div>
            ) : (
              <div className="space-y-2">
                {availableGames.map((game) => {
                  const isAlreadyLoaded = loadedGames.some(
                    (lg) => lg.event_ticker === game.event_ticker
                  )
                  
                  return (
                    <div
                      key={game.event_ticker || game.id}
                      className="flex items-center justify-between p-3 bg-gray-750 rounded hover:bg-gray-700"
                    >
                      <div>
                        <p className="font-medium">
                          {game.away_team || game.subtitle?.split(' @ ')[0]} @{' '}
                          {game.home_team || game.subtitle?.split(' @ ')[1]}
                        </p>
                        <p className="text-sm text-gray-400">
                          {game.event_ticker}
                        </p>
                      </div>
                      
                      {isAlreadyLoaded ? (
                        <span className="px-3 py-1 text-sm bg-green-600/20 text-green-400 rounded">
                          Loaded
                        </span>
                      ) : (
                        <button
                          onClick={() => loadMutation.mutate(game.event_ticker)}
                          disabled={loadMutation.isPending}
                          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm disabled:opacity-50"
                        >
                          {loadMutation.isPending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Plus className="w-4 h-4" />
                          )}
                          Load
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

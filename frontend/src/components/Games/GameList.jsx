import { useQuery } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { getLoadedGames } from '../../api/client'
import GameCard from './GameCard'

export default function GameList() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['loadedGames'],
    queryFn: getLoadedGames,
  })
  
  const games = data?.games ? Object.values(data.games) : []
  
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Active Games</h2>
          <p className="text-gray-400">{games.length} games loaded</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
      
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading games...</div>
      ) : games.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No games loaded</p>
          <p className="text-sm mt-2">Use the CLI to load games or add a game loader UI</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {games.map((game) => (
            <GameCard key={game.game_id} game={game} isLoaded={true} />
          ))}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import {
  Gamepad2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Calendar,
  Clock,
  Plus,
  Minus,
  Radio,
  Loader2,
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Loading from '../components/ui/Loading'
import ErrorDisplay from '../components/ui/ErrorDisplay'
import {
  useLoadedGames,
  useAvailableGames,
  useUnloadGame,
  useLoadGameByTicker,
} from '../hooks/useGames'
import { usePlaceManualOrder } from '../hooks/useExecution'
import type { GameState, MarketState } from '../api/types'

function MarketRow({
  market,
  onPlaceOrder,
  isPlacingOrder,
}: {
  market: MarketState
  onPlaceOrder: (marketTicker: string, side: 'yes' | 'no') => void
  isPlacingOrder: boolean
}) {
  const yesBid = market.orderbook?.yes_bid ?? 0
  const yesAsk = market.orderbook?.yes_ask ?? 0
  const spread = market.orderbook?.spread ?? 0
  const volume = market.orderbook?.volume ?? 0

  // Derive market name from ticker
  const marketName = market.ticker.split('-').pop() || market.market_type

  return (
    <tr className="group">
      <td className="font-mono text-xs text-slate-300">{marketName}</td>
      <td className="text-center">
        <Badge variant="default" size="sm">
          {market.market_type}
        </Badge>
      </td>
      <td className="text-right font-mono text-neon-green">{yesBid}¢</td>
      <td className="text-right font-mono text-neon-red">{yesAsk}¢</td>
      <td className="text-right font-mono text-slate-500">{spread}¢</td>
      <td className="text-right font-mono text-slate-400">{volume.toLocaleString()}</td>
      <td className="text-right">
        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="success"
            size="sm"
            onClick={() => onPlaceOrder(market.ticker, 'yes')}
            disabled={isPlacingOrder}
          >
            {isPlacingOrder ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Buy Yes'}
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => onPlaceOrder(market.ticker, 'no')}
            disabled={isPlacingOrder}
          >
            {isPlacingOrder ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Buy No'}
          </Button>
        </div>
      </td>
    </tr>
  )
}

function GameCard({
  game,
  onUnload,
  isUnloading,
}: {
  game: GameState
  onUnload: () => void
  isUnloading: boolean
}) {
  const [expanded, setExpanded] = useState(true)
  const placeOrder = usePlaceManualOrder()

  const handlePlaceOrder = (marketTicker: string, side: 'yes' | 'no') => {
    placeOrder.mutate({
      game_id: game.game_id,
      market_ticker: marketTicker,
      side,
      quantity: 10, // Default quantity
      reason: 'Manual order from dashboard',
    })
  }

  const markets = Object.values(game.markets)
  const isLive = game.status === 'live'

  return (
    <div
      className={`bg-terminal-bg/50 rounded-lg border ${
        isLive ? 'border-neon-green/30' : 'border-terminal-border'
      } overflow-hidden`}
    >
      {/* Game Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-terminal-hover transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <button className="p-1">
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {/* Teams */}
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end">
              <span className="font-display font-bold text-lg text-white">{game.away_team}</span>
              {game.nba_live && (
                <span className="font-mono text-sm text-slate-400">{game.nba_live.away_score}</span>
              )}
            </div>
            <span className="text-slate-600 font-mono text-sm">@</span>
            <div className="flex flex-col">
              <span className="font-display font-bold text-lg text-white">{game.home_team}</span>
              {game.nba_live && (
                <span className="font-mono text-sm text-slate-400">{game.nba_live.home_score}</span>
              )}
            </div>
          </div>

          {/* Status Badge */}
          {isLive ? (
            <Badge variant="success" pulse>
              <Radio className="w-3 h-3" />
              Live{game.nba_live ? ` • Q${game.nba_live.period} ${game.nba_live.time_remaining}` : ''}
            </Badge>
          ) : (
            <Badge variant="info">
              <Clock className="w-3 h-3" />
              {new Date(game.game_date).toLocaleDateString()}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-slate-500">{game.event_ticker}</span>
          <Button
            variant="danger"
            size="sm"
            icon={isUnloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Minus className="w-3 h-3" />}
            onClick={(e) => {
              e.stopPropagation()
              onUnload()
            }}
            disabled={isUnloading}
          >
            Unload
          </Button>
        </div>
      </div>

      {/* Consensus Odds */}
      {expanded && game.odds.length > 0 && (
        <div className="px-4 py-2 bg-terminal-bg/30 border-y border-terminal-border/50">
          <div className="flex items-center gap-6">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
              Consensus:
            </span>
            {game.odds.slice(0, 3).map((odds, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs font-mono">
                <span className="text-slate-500">{odds.vendor}:</span>
                {odds.moneyline_home !== null && (
                  <>
                    <span className={odds.moneyline_home < 0 ? 'text-neon-green' : 'text-neon-red'}>
                      {odds.moneyline_home > 0 ? '+' : ''}
                      {odds.moneyline_home}
                    </span>
                    <span className="text-slate-600">/</span>
                    <span className={(odds.moneyline_away ?? 0) < 0 ? 'text-neon-green' : 'text-neon-red'}>
                      {(odds.moneyline_away ?? 0) > 0 ? '+' : ''}
                      {odds.moneyline_away}
                    </span>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Markets Table */}
      {expanded && markets.length > 0 && (
        <div className="p-4">
          <table className="w-full data-table">
            <thead>
              <tr>
                <th>Market</th>
                <th className="text-center">Type</th>
                <th className="text-right">Yes Bid</th>
                <th className="text-right">Yes Ask</th>
                <th className="text-right">Spread</th>
                <th className="text-right">Volume</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {markets.map((market) => (
                <MarketRow
                  key={market.ticker}
                  market={market}
                  onPlaceOrder={handlePlaceOrder}
                  isPlacingOrder={placeOrder.isPending}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty Markets */}
      {expanded && markets.length === 0 && (
        <div className="p-4 text-center text-slate-500 font-mono text-sm">No markets loaded</div>
      )}
    </div>
  )
}

export default function GamesPage() {
  const [selectedDate, setSelectedDate] = useState(() => {
    const today = new Date()
    return today.toISOString().split('T')[0]
  })

  const { data: loadedGamesData, isLoading: isLoadingGames, error: gamesError, refetch: refetchGames } = useLoadedGames()
  const { data: availableGamesData, isLoading: isLoadingAvailable, error: availableError } = useAvailableGames(selectedDate)
  const unloadGame = useUnloadGame()
  const loadGame = useLoadGameByTicker()

  const games = loadedGamesData?.games ? Object.values(loadedGamesData.games) : []
  const availableGames = availableGamesData?.games || []

  const handleLoadGame = (eventTicker: string) => {
    loadGame.mutate(eventTicker)
  }

  const handleUnloadGame = (gameId: string) => {
    unloadGame.mutate(gameId)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl tracking-wider text-white">
            Game <span className="text-neon-cyan">Management</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">Load and monitor NBA games from Kalshi</p>
        </div>
        <Button
          variant="primary"
          icon={isLoadingGames ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          onClick={() => refetchGames()}
          disabled={isLoadingGames}
        >
          Refresh All
        </Button>
      </div>

      {/* Active Games */}
      <Panel
        title="Active Games"
        subtitle={`${games.length} games loaded`}
        icon={<Gamepad2 className="w-5 h-5 text-neon-cyan" />}
        neonBorder
      >
        {isLoadingGames ? (
          <Loading message="Loading games..." />
        ) : gamesError ? (
          <ErrorDisplay
            message={gamesError instanceof Error ? gamesError.message : 'Failed to load games'}
            onRetry={() => refetchGames()}
          />
        ) : games.length === 0 ? (
          <div className="py-8 text-center text-slate-500 font-mono text-sm">
            No games loaded. Browse below to load games.
          </div>
        ) : (
          <div className="space-y-4">
            {games.map((game) => (
              <GameCard
                key={game.game_id}
                game={game}
                onUnload={() => handleUnloadGame(game.game_id)}
                isUnloading={unloadGame.isPending}
              />
            ))}
          </div>
        )}
      </Panel>

      {/* Browse Games */}
      <Panel
        title="Browse Games"
        subtitle="Find and load games by date"
        icon={<Calendar className="w-5 h-5 text-neon-purple" />}
        headerAction={
          <div className="flex items-center gap-3">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-terminal-bg border border-terminal-border rounded-md px-3 py-1.5 font-mono text-sm text-white focus:border-neon-cyan focus:outline-none"
            />
          </div>
        }
      >
        {isLoadingAvailable ? (
          <Loading message="Searching games..." />
        ) : availableError ? (
          <ErrorDisplay
            message={availableError instanceof Error ? availableError.message : 'Failed to search games'}
          />
        ) : availableGames.length === 0 ? (
          <div className="py-8 text-center text-slate-500 font-mono text-sm">
            No games found for {selectedDate}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableGames.map((game) => (
              <div
                key={game.event_ticker}
                className="bg-terminal-bg/50 rounded-lg border border-terminal-border p-4 hover:border-neon-cyan/30 transition-colors group"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-display font-bold text-white">{game.away_team}</span>
                    <span className="text-slate-600">@</span>
                    <span className="font-display font-bold text-white">{game.home_team}</span>
                  </div>
                  <Badge variant="default">{game.market_count} mkts</Badge>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-4">
                  <Clock className="w-3 h-3" />
                  {game.game_date}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-600 truncate max-w-[60%]">
                    {game.event_ticker}
                  </span>
                  <Button
                    variant="success"
                    size="sm"
                    icon={loadGame.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                    onClick={() => handleLoadGame(game.event_ticker)}
                    disabled={loadGame.isPending}
                  >
                    Load
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}

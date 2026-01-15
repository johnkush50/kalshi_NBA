import { useState } from 'react'
import {
  Gamepad2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Calendar,
  Clock,
  TrendingUp,
  Loader,
  Plus,
  Minus,
  Radio
} from 'lucide-react'
import Panel from '../components/ui/Panel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { activeGames, availableGames, type ActiveGame, type Market } from '../data/mockData'

function MarketRow({ market }: { market: Market }) {
  return (
    <tr className="group">
      <td className="font-mono text-xs text-slate-300">{market.name}</td>
      <td className="text-center">
        <Badge variant="default" size="sm">{market.type}</Badge>
      </td>
      <td className="text-right font-mono text-neon-green">{market.yesBid}¢</td>
      <td className="text-right font-mono text-neon-red">{market.yesAsk}¢</td>
      <td className="text-right font-mono text-slate-500">{market.spread}¢</td>
      <td className="text-right font-mono text-slate-400">{market.volume.toLocaleString()}</td>
      <td className="text-right">
        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="success" size="sm">Buy Yes</Button>
          <Button variant="danger" size="sm">Buy No</Button>
        </div>
      </td>
    </tr>
  )
}

function GameCard({ game }: { game: ActiveGame }) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className={`bg-terminal-bg/50 rounded-lg border ${
      game.status === 'live' ? 'border-neon-green/30' : 'border-terminal-border'
    } overflow-hidden`}>
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
              <span className="font-display font-bold text-lg text-white">{game.awayAbbr}</span>
              {game.status === 'live' && (
                <span className="font-mono text-sm text-slate-400">{game.awayScore}</span>
              )}
            </div>
            <span className="text-slate-600 font-mono text-sm">@</span>
            <div className="flex flex-col">
              <span className="font-display font-bold text-lg text-white">{game.homeAbbr}</span>
              {game.status === 'live' && (
                <span className="font-mono text-sm text-slate-400">{game.homeScore}</span>
              )}
            </div>
          </div>

          {/* Status Badge */}
          {game.status === 'live' ? (
            <Badge variant="success" pulse>
              <Radio className="w-3 h-3" />
              Live • {game.period}
            </Badge>
          ) : (
            <Badge variant="info">
              <Clock className="w-3 h-3" />
              {new Date(game.gameTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-slate-500">{game.eventTicker}</span>
          <Button variant="danger" size="sm" icon={<Minus className="w-3 h-3" />}>
            Unload
          </Button>
        </div>
      </div>

      {/* Consensus Odds */}
      {expanded && (
        <div className="px-4 py-2 bg-terminal-bg/30 border-y border-terminal-border/50">
          <div className="flex items-center gap-6">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Consensus:</span>
            {game.consensusOdds.map((odds, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs font-mono">
                <span className="text-slate-500">{odds.vendor}:</span>
                <span className={odds.homeOdds < 0 ? 'text-neon-green' : 'text-neon-red'}>
                  {odds.homeOdds > 0 ? '+' : ''}{odds.homeOdds}
                </span>
                <span className="text-slate-600">/</span>
                <span className={odds.awayOdds < 0 ? 'text-neon-green' : 'text-neon-red'}>
                  {odds.awayOdds > 0 ? '+' : ''}{odds.awayOdds}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Markets Table */}
      {expanded && (
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
              {game.markets.map((market) => (
                <MarketRow key={market.ticker} market={market} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function GamesPage() {
  const [selectedDate, setSelectedDate] = useState('2026-01-15')

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
        <Button variant="primary" icon={<RefreshCw className="w-4 h-4" />}>
          Refresh All
        </Button>
      </div>

      {/* Active Games */}
      <Panel
        title="Active Games"
        subtitle={`${activeGames.length} games loaded`}
        icon={<Gamepad2 className="w-5 h-5 text-neon-cyan" />}
        neonBorder
      >
        <div className="space-y-4">
          {activeGames.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </div>
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
            <Button variant="secondary" icon={<RefreshCw className="w-3.5 h-3.5" />}>
              Search
            </Button>
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableGames.map((game) => (
            <div
              key={game.eventTicker}
              className="bg-terminal-bg/50 rounded-lg border border-terminal-border p-4 hover:border-neon-cyan/30 transition-colors group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-display font-bold text-white">{game.awayAbbr}</span>
                  <span className="text-slate-600">@</span>
                  <span className="font-display font-bold text-white">{game.homeAbbr}</span>
                </div>
                <Badge variant="default">
                  {game.marketCount} mkts
                </Badge>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-4">
                <Clock className="w-3 h-3" />
                {new Date(game.gameTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-600 truncate max-w-[60%]">
                  {game.eventTicker}
                </span>
                <Button variant="success" size="sm" icon={<Plus className="w-3 h-3" />}>
                  Load
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}

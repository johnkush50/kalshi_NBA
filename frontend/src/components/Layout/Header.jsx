import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, TrendingDown } from 'lucide-react'
import { getPnL, getExecutionStats } from '../../api/client'
import { formatCurrency, getPnLColor } from '../../utils/formatters'

export default function Header() {
  const { data: pnl } = useQuery({
    queryKey: ['pnl'],
    queryFn: getPnL,
  })
  
  const { data: stats } = useQuery({
    queryKey: ['executionStats'],
    queryFn: getExecutionStats,
  })
  
  const totalPnL = pnl?.total_pnl || 0
  
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-xl font-bold">Kalshi NBA Paper Trading</h1>
            <p className="text-sm text-gray-400">Real-time strategy dashboard</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className="text-sm text-gray-400">Total P&L</p>
            <div className={`text-2xl font-bold flex items-center gap-1 ${getPnLColor(totalPnL)}`}>
              {totalPnL >= 0 ? (
                <TrendingUp className="w-5 h-5" />
              ) : (
                <TrendingDown className="w-5 h-5" />
              )}
              {formatCurrency(totalPnL, true)}
            </div>
          </div>
          
          <div className="flex gap-4 pl-6 border-l border-gray-700">
            <div className="text-center">
              <p className="text-2xl font-bold">{pnl?.open_positions || 0}</p>
              <p className="text-xs text-gray-400">Positions</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">{stats?.daily_order_count || 0}</p>
              <p className="text-xs text-gray-400">Orders Today</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

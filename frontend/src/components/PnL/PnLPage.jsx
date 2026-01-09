import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw,
  PieChart,
  BarChart3,
  ShoppingCart,
  Package
} from 'lucide-react'
import { getPnL, refreshPnL, getOrders } from '../../api/client'
import { formatCurrency, formatCents, getPnLColor, getPnLBgColor } from '../../utils/formatters'

export default function PnLPage() {
  const queryClient = useQueryClient()
  
  const { data: pnlData, isLoading } = useQuery({
    queryKey: ['pnl'],
    queryFn: getPnL,
  })
  
  const { data: ordersData } = useQuery({
    queryKey: ['orders'],
    queryFn: () => getOrders(100),
  })
  
  const refreshMutation = useMutation({
    mutationFn: refreshPnL,
    onSuccess: () => {
      queryClient.invalidateQueries(['pnl'])
    },
  })
  
  const totalPnL = pnlData?.total_pnl || 0
  const unrealizedPnL = pnlData?.total_unrealized_pnl || 0
  const realizedPnL = pnlData?.total_realized_pnl || 0
  const totalCost = pnlData?.total_cost || 0
  const positions = pnlData?.positions || []
  
  const orders = ordersData?.orders || []
  const filledOrders = orders.filter(o => o.status === 'filled')
  const totalVolume = filledOrders.reduce((sum, o) => sum + (o.fill_price || 0) * (o.filled_quantity || 0), 0)
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolio P&L</h2>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
        >
          <RefreshCw className={`w-4 h-4 ${refreshMutation.isPending ? 'animate-spin' : ''}`} />
          Refresh P&L
        </button>
      </div>
      
      {/* P&L Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <PnLCard
          title="Total P&L"
          value={totalPnL}
          icon={totalPnL >= 0 ? TrendingUp : TrendingDown}
          isPrimary
        />
        <PnLCard
          title="Unrealized P&L"
          value={unrealizedPnL}
          icon={DollarSign}
          subtitle="Open positions"
        />
        <PnLCard
          title="Realized P&L"
          value={realizedPnL}
          icon={DollarSign}
          subtitle="Closed positions"
        />
        <PnLCard
          title="Total Cost"
          value={totalCost}
          icon={PieChart}
          subtitle="Capital deployed"
          isNeutral
        />
      </div>
      
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-2">
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm">Trading Volume</span>
          </div>
          <p className="text-2xl font-bold">{formatCents(totalVolume)}</p>
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-2">
            <ShoppingCart className="w-4 h-4" />
            <span className="text-sm">Total Orders</span>
          </div>
          <p className="text-2xl font-bold">{filledOrders.length}</p>
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="flex items-center gap-2 text-gray-400 mb-2">
            <Package className="w-4 h-4" />
            <span className="text-sm">Open Positions</span>
          </div>
          <p className="text-2xl font-bold">{positions.length}</p>
        </div>
      </div>
      
      {/* Position Details */}
      {positions.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700">
            <h3 className="font-semibold">Position P&L Breakdown</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                <th className="px-4 py-3">Market</th>
                <th className="px-4 py-3">Side</th>
                <th className="px-4 py-3 text-right">Qty</th>
                <th className="px-4 py-3 text-right">Entry</th>
                <th className="px-4 py-3 text-right">Cost</th>
                <th className="px-4 py-3 text-right">Unrealized P&L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos, i) => (
                <tr key={i} className="border-b border-gray-700 last:border-0">
                  <td className="px-4 py-3 font-mono text-sm">{pos.ticker}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded ${
                      pos.side === 'yes' 
                        ? 'bg-green-600/20 text-green-400' 
                        : 'bg-red-600/20 text-red-400'
                    }`}>
                      {pos.side?.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{pos.quantity}</td>
                  <td className="px-4 py-3 text-right">{formatCents(pos.avg_entry)}</td>
                  <td className="px-4 py-3 text-right">{formatCents(pos.cost)}</td>
                  <td className={`px-4 py-3 text-right font-medium ${getPnLColor(pos.unrealized_pnl)}`}>
                    {formatCents(pos.unrealized_pnl, true)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function PnLCard({ title, value, icon: Icon, subtitle, isPrimary, isNeutral }) {
  const colorClass = isNeutral ? 'text-gray-100' : getPnLColor(value)
  const bgClass = isPrimary ? getPnLBgColor(value) : ''
  
  return (
    <div className={`bg-gray-800 rounded-lg border border-gray-700 p-4 ${bgClass}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{title}</span>
        <Icon className={`w-5 h-5 ${colorClass}`} />
      </div>
      <p className={`text-2xl font-bold ${colorClass}`}>
        {isNeutral ? formatCents(value) : formatCents(value, true)}
      </p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}

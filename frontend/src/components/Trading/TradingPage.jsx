import { useQuery } from '@tanstack/react-query'
import { ShoppingCart, Package } from 'lucide-react'
import { getOrders, getOpenPositions } from '../../api/client'
import { formatCents, formatTime } from '../../utils/formatters'

export default function TradingPage() {
  const { data: ordersData, isLoading: loadingOrders } = useQuery({
    queryKey: ['orders'],
    queryFn: () => getOrders(50),
  })
  
  const { data: positionsData, isLoading: loadingPositions } = useQuery({
    queryKey: ['positions'],
    queryFn: getOpenPositions,
  })
  
  const orders = ordersData?.orders || []
  const positions = positionsData?.positions || []
  
  return (
    <div className="space-y-8">
      {/* Open Positions */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Package className="w-6 h-6 text-blue-400" />
          <h2 className="text-2xl font-bold">Open Positions</h2>
          <span className="text-gray-400">({positions.length})</span>
        </div>
        
        {loadingPositions ? (
          <div className="text-center py-8 text-gray-400">Loading positions...</div>
        ) : positions.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
            No open positions
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                  <th className="px-4 py-3">Market</th>
                  <th className="px-4 py-3">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Avg Entry</th>
                  <th className="px-4 py-3 text-right">Total Cost</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => (
                  <tr key={i} className="border-b border-gray-700 last:border-0 hover:bg-gray-750">
                    <td className="px-4 py-3 font-mono text-sm">{pos.market_ticker}</td>
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
                    <td className="px-4 py-3 text-right">{formatCents(pos.avg_entry_price)}</td>
                    <td className="px-4 py-3 text-right">{formatCents(pos.total_cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      
      {/* Order History */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <ShoppingCart className="w-6 h-6 text-purple-400" />
          <h2 className="text-2xl font-bold">Order History</h2>
          <span className="text-gray-400">({orders.length})</span>
        </div>
        
        {loadingOrders ? (
          <div className="text-center py-8 text-gray-400">Loading orders...</div>
        ) : orders.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-gray-800 rounded-lg border border-gray-700">
            No orders yet
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Market</th>
                  <th className="px-4 py-3">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Fill Price</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id} className="border-b border-gray-700 last:border-0 hover:bg-gray-750">
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {formatTime(order.created_at)}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">
                      {order.market_ticker?.split('-').pop()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        order.side === 'yes' 
                          ? 'bg-green-600/20 text-green-400' 
                          : 'bg-red-600/20 text-red-400'
                      }`}>
                        {order.side?.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">{order.filled_quantity || order.quantity}</td>
                    <td className="px-4 py-3 text-right">
                      {order.fill_price ? formatCents(order.fill_price) : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        order.status === 'filled' 
                          ? 'bg-green-600/20 text-green-400'
                          : order.status === 'rejected'
                          ? 'bg-red-600/20 text-red-400'
                          : 'bg-yellow-600/20 text-yellow-400'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ShoppingCart } from 'lucide-react'
import { placeManualOrder } from '../../api/client'
import { formatCents } from '../../utils/formatters'

export default function MarketTable({ markets, gameId }) {
  const [orderTicker, setOrderTicker] = useState(null)
  const [orderSide, setOrderSide] = useState('yes')
  const [orderQty, setOrderQty] = useState(5)
  const queryClient = useQueryClient()
  
  const orderMutation = useMutation({
    mutationFn: ({ ticker, side, qty }) => placeManualOrder(gameId, ticker, side, qty),
    onSuccess: () => {
      queryClient.invalidateQueries(['positions'])
      queryClient.invalidateQueries(['pnl'])
      setOrderTicker(null)
    },
  })
  
  const grouped = Object.entries(markets).reduce((acc, [ticker, market]) => {
    const type = market.market_type || 'other'
    if (!acc[type]) acc[type] = []
    acc[type].push({ ticker, ...market })
    return acc
  }, {})
  
  return (
    <div className="overflow-x-auto">
      {Object.entries(grouped).map(([type, typeMarkets]) => (
        <div key={type} className="mb-4">
          <h4 className="px-4 py-2 text-sm font-medium text-gray-400 bg-gray-750 uppercase">
            {type}
          </h4>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left">
                <th className="px-4 py-2">Market</th>
                <th className="px-4 py-2 text-right">Yes Bid</th>
                <th className="px-4 py-2 text-right">Yes Ask</th>
                <th className="px-4 py-2 text-right">Spread</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {typeMarkets.map(({ ticker, orderbook }) => {
                const yesBid = orderbook?.yes_bid || 0
                const yesAsk = orderbook?.yes_ask || 0
                const spread = yesAsk - yesBid
                
                return (
                  <tr key={ticker} className="border-t border-gray-700 hover:bg-gray-750">
                    <td className="px-4 py-2 font-mono text-xs">{ticker.split('-').pop()}</td>
                    <td className="px-4 py-2 text-right text-green-400">{formatCents(yesBid)}</td>
                    <td className="px-4 py-2 text-right text-red-400">{formatCents(yesAsk)}</td>
                    <td className="px-4 py-2 text-right text-gray-400">{formatCents(spread)}</td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => setOrderTicker(orderTicker === ticker ? null : ticker)}
                        className="p-1 hover:bg-gray-600 rounded"
                      >
                        <ShoppingCart className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ))}
      
      {orderTicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Place Order</h3>
            <p className="text-sm text-gray-400 mb-4 font-mono">{orderTicker}</p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Side</label>
                <select
                  value={orderSide}
                  onChange={(e) => setOrderSide(e.target.value)}
                  className="w-full bg-gray-700 rounded px-3 py-2"
                >
                  <option value="yes">YES</option>
                  <option value="no">NO</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Quantity</label>
                <input
                  type="number"
                  value={orderQty}
                  onChange={(e) => setOrderQty(parseInt(e.target.value) || 1)}
                  min="1"
                  max="100"
                  className="w-full bg-gray-700 rounded px-3 py-2"
                />
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setOrderTicker(null)}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={() => orderMutation.mutate({ 
                    ticker: orderTicker, 
                    side: orderSide, 
                    qty: orderQty 
                  })}
                  disabled={orderMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded"
                >
                  {orderMutation.isPending ? 'Placing...' : 'Place Order'}
                </button>
              </div>
              
              {orderMutation.isError && (
                <p className="text-red-400 text-sm">{orderMutation.error.message}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

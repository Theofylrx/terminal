import React, { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react'

interface Position {
  symbol: string
  quantity: number
  avg_entry_price: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
  broker: string
}

interface PositionsData {
  success: boolean
  positions: Position[]
  total_value: number
  total_pnl: number
  total_pnl_percent: number
  count: number
}

const Portfolio: React.FC = () => {
  const [positionsData, setPositionsData] = useState<PositionsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const response = await fetch('http://localhost:8007/api/v1/positions/demo_user')
        const data = await response.json()
        setPositionsData(data)
      } catch (error) {
        console.error('Failed to fetch positions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPositions()
    // Refresh every 10 seconds
    const interval = setInterval(fetchPositions, 10000)
    return () => clearInterval(interval)
  }, [])

  const positions = positionsData?.positions || []
  const totalValue = positionsData?.total_value || 0
  const totalPnL = positionsData?.total_pnl || 0
  const totalPnLPercent = positionsData?.total_pnl_percent || 0

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Portfolio</h1>
        <p className="text-sm text-slate-600 mt-1">Track your positions and performance</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-6 h-6 border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Total Value</span>
                <DollarSign className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-semibold text-slate-900">${totalValue.toLocaleString()}</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Total P&L</span>
                {totalPnL >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
              </div>
              <p className={`text-2xl font-semibold ${totalPnL >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Return %</span>
                <Percent className="w-4 h-4 text-slate-400" />
              </div>
              <p className={`text-2xl font-semibold ${totalPnLPercent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Positions</span>
              </div>
              <p className="text-2xl font-semibold text-slate-900">{positions.length}</p>
            </div>
          </div>

          {/* Positions Table */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Open Positions</h2>
            </div>

            {positions.length === 0 ? (
              <div className="text-center py-16">
                <p className="text-slate-500 mb-2">No open positions</p>
                <p className="text-sm text-slate-400">Place a trade to see your positions here</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Symbol</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Broker</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Quantity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Avg Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Current Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">P&L</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">P&L %</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {positions.map((position) => (
                      <tr key={`${position.broker}-${position.symbol}`} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-medium text-slate-900">{position.symbol}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            position.broker === 'alpaca' ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'
                          }`}>
                            {position.broker.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{position.quantity}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">${position.avg_entry_price.toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">${position.current_price.toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${position.unrealized_pnl >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                            position.unrealized_pnl_percent >= 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                          }`}>
                            {position.unrealized_pnl_percent >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {position.unrealized_pnl_percent >= 0 ? '+' : ''}{position.unrealized_pnl_percent.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button className="text-sm text-red-600 hover:text-red-700 font-medium transition-colors">Close</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Portfolio

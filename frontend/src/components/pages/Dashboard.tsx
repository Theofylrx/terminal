import React, { useEffect, useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'

const Dashboard: React.FC = () => {
  const [serviceStatus, setServiceStatus] = useState<any>(null)
  const [executorStatus, setExecutorStatus] = useState<any>(null)
  const [accountData, setAccountData] = useState<any>(null)
  const [positionsData, setPositionsData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [marketData, executor, account, positions] = await Promise.all([
          fetch('http://localhost:8003/api/v1/status').then(r => r.json()).catch(() => null),
          fetch('http://localhost:8007/api/v1/health').then(r => r.json()).catch(() => null),
          fetch('http://localhost:8007/api/v1/account/demo_user').then(r => r.json()).catch(() => null),
          fetch('http://localhost:8007/api/v1/positions/demo_user').then(r => r.json()).catch(() => null),
        ])

        setServiceStatus(marketData)
        setExecutorStatus(executor)
        setAccountData(account)
        setPositionsData(positions)
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        setLoading(false)
      }
    }

    fetchData()
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Calculate real stats from account and positions data
  const portfolioValue = accountData?.total_equity || 0
  const totalPnL = positionsData?.total_pnl || 0
  const positionsCount = positionsData?.count || 0
  const profitableCount = positionsData?.positions?.filter((p: any) => p.unrealized_pnl > 0).length || 0

  const stats = [
    {
      label: 'Portfolio Value',
      value: `$${portfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      change: `Alpaca: $${accountData?.alpaca_equity.toLocaleString() || '0'}`,
      changePercent: `Binance: $${accountData?.binance_total_value.toLocaleString() || '0'}`,
      positive: true,
      icon: DollarSign,
      iconBg: 'from-emerald-500 to-teal-500'
    },
    {
      label: 'Total P&L',
      value: `${totalPnL >= 0 ? '+' : ''}$${totalPnL.toFixed(2)}`,
      change: `${positionsData?.total_pnl_percent?.toFixed(2) || '0'}%`,
      changePercent: 'unrealized',
      positive: totalPnL >= 0,
      icon: TrendingUp,
      iconBg: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Active Positions',
      value: `${positionsCount}`,
      change: `${profitableCount} profitable`,
      changePercent: `${positionsCount - profitableCount} loss`,
      positive: true,
      icon: Activity,
      iconBg: 'from-purple-500 to-pink-500'
    },
    {
      label: 'Buying Power',
      value: `$${accountData?.alpaca_buying_power?.toLocaleString() || '0'}`,
      change: 'Alpaca',
      changePercent: '4x leverage',
      positive: true,
      icon: BarChart3,
      iconBg: 'from-orange-500 to-red-500'
    },
  ]

  const topMovers = [
    { symbol: 'AAPL', price: 175.43, change: 2.34, percent: 1.35 },
    { symbol: 'TSLA', price: 242.84, change: -5.12, percent: -2.07 },
    { symbol: 'BTCUSDT', price: 43250, change: 890, percent: 2.10 },
    { symbol: 'MSFT', price: 378.91, change: 4.23, percent: 1.13 },
  ]

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-600 mt-1">Monitor your trading activity and portfolio performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div
              key={i}
              className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{stat.label}</span>
                <Icon className="w-4 h-4 text-slate-400" />
              </div>

              <div className="space-y-1">
                <p className="text-2xl font-semibold text-slate-900">{stat.value}</p>
                <div className="flex items-center gap-2 text-xs">
                  <span className={`font-medium ${stat.positive ? 'text-emerald-600' : 'text-red-600'}`}>
                    {stat.change}
                  </span>
                  <span className="text-slate-500">{stat.changePercent}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Broker Status */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Broker Connections</h2>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${executorStatus?.alpaca_connected ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Alpaca Markets</p>
                    <p className="text-xs text-slate-500">Stocks & ETFs</p>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  executorStatus?.alpaca_connected
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-red-50 text-red-700'
                }`}>
                  {executorStatus?.alpaca_connected ? 'Connected' : 'Offline'}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${executorStatus?.binance_connected ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Binance</p>
                    <p className="text-xs text-slate-500">Cryptocurrency</p>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  executorStatus?.binance_connected
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-red-50 text-red-700'
                }`}>
                  {executorStatus?.binance_connected ? 'Connected' : 'Offline'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Orders Today</span>
              <span className="font-medium text-slate-900">0</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Positions</span>
              <span className="font-medium text-slate-900">{positionsCount}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Status</span>
              <span className="inline-flex items-center gap-1.5 text-emerald-600">
                <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full"></div>
                Active
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Market Data Subscriptions */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-4">Market Data Subscriptions</h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-6 h-6 border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
          </div>
        ) : serviceStatus?.subscriptions ? (
          <div className="space-y-6">
            {serviceStatus.subscriptions.alpaca?.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-700">Stocks</span>
                  <span className="text-xs text-slate-500">{serviceStatus.subscriptions.alpaca.length} symbols</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {serviceStatus.subscriptions.alpaca.map((symbol: string) => (
                    <span
                      key={symbol}
                      className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-700 rounded text-xs font-medium hover:bg-slate-100 transition-colors"
                    >
                      {symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {serviceStatus.subscriptions.binance?.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-700">Crypto</span>
                  <span className="text-xs text-slate-500">{serviceStatus.subscriptions.binance.length} symbols</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {serviceStatus.subscriptions.binance.map((symbol: string) => (
                    <span
                      key={symbol}
                      className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-700 rounded text-xs font-medium hover:bg-slate-100 transition-colors"
                    >
                      {symbol}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500 text-sm">
            No active subscriptions
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard

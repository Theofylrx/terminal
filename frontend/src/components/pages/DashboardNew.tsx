import React, { useEffect, useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const DashboardNew: React.FC = () => {
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
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const portfolioValue = accountData?.total_equity || 0
  const totalPnL = positionsData?.total_pnl || 0
  const positionsCount = positionsData?.count || 0
  const profitableCount = positionsData?.positions?.filter((p: any) => p.unrealized_pnl > 0).length || 0

  const stats = [
    {
      label: 'Portfolio Value',
      value: `$${portfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      subtitle: 'Total Equity',
      change: '+2.4%',
      positive: true,
      icon: DollarSign,
      color: 'emerald'
    },
    {
      label: 'Total P&L',
      value: `${totalPnL >= 0 ? '+' : ''}$${totalPnL.toFixed(2)}`,
      subtitle: 'Unrealized',
      change: `${positionsData?.total_pnl_percent?.toFixed(2) || '0'}%`,
      positive: totalPnL >= 0,
      icon: TrendingUp,
      color: 'blue'
    },
    {
      label: 'Active Positions',
      value: `${positionsCount}`,
      subtitle: `${profitableCount} Profitable`,
      change: `${positionsCount - profitableCount} Loss`,
      positive: profitableCount > (positionsCount - profitableCount),
      icon: Activity,
      color: 'purple'
    },
    {
      label: 'Buying Power',
      value: `$${accountData?.alpaca_buying_power?.toLocaleString() || '0'}`,
      subtitle: 'Available',
      change: '4x Leverage',
      positive: true,
      icon: BarChart3,
      color: 'orange'
    },
  ]

  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Monitor your trading activity and portfolio performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" className="h-6">
            <span className="w-1.5 h-1.5 bg-white rounded-full mr-1.5"></span>
            Live
          </Badge>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <Card key={i} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="flex items-center text-xs text-muted-foreground mt-1">
                  <span className={stat.positive ? 'text-emerald-600' : 'text-red-600'}>
                    {stat.change}
                  </span>
                  <span className="ml-1">· {stat.subtitle}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Broker Connections */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Broker Connections</CardTitle>
            <CardDescription>
              Real-time status of your broker integrations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-primary"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className={`h-3 w-3 rounded-full ${executorStatus?.alpaca_connected ? 'bg-emerald-500' : 'bg-red-500'} animate-pulse`}></div>
                    <div>
                      <p className="text-sm font-medium leading-none">Alpaca Markets</p>
                      <p className="text-sm text-muted-foreground mt-1">Stocks & ETFs</p>
                    </div>
                  </div>
                  <Badge variant={executorStatus?.alpaca_connected ? "success" : "destructive"}>
                    {executorStatus?.alpaca_connected ? 'Connected' : 'Offline'}
                  </Badge>
                </div>

                <div className="flex items-center justify-between rounded-lg border p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className={`h-3 w-3 rounded-full ${executorStatus?.binance_connected ? 'bg-emerald-500' : 'bg-red-500'} animate-pulse`}></div>
                    <div>
                      <p className="text-sm font-medium leading-none">Binance</p>
                      <p className="text-sm text-muted-foreground mt-1">Cryptocurrency</p>
                    </div>
                  </div>
                  <Badge variant={executorStatus?.binance_connected ? "success" : "destructive"}>
                    {executorStatus?.binance_connected ? 'Connected' : 'Offline'}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your trading activity summary
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Orders Today</span>
              <span className="text-sm font-bold">0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Active Positions</span>
              <span className="text-sm font-bold">{positionsCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Win Rate</span>
              <span className="text-sm font-bold">
                {positionsCount > 0 ? `${((profitableCount / positionsCount) * 100).toFixed(0)}%` : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-sm text-muted-foreground">Status</span>
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-sm font-medium text-emerald-600">Active</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Market Data Subscriptions */}
      <Card>
        <CardHeader>
          <CardTitle>Market Data Subscriptions</CardTitle>
          <CardDescription>
            Symbols currently streaming real-time data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-primary"></div>
            </div>
          ) : serviceStatus?.subscriptions ? (
            <div className="space-y-6">
              {serviceStatus.subscriptions.alpaca?.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Stocks</Badge>
                      <span className="text-sm text-muted-foreground">
                        {serviceStatus.subscriptions.alpaca.length} symbols
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {serviceStatus.subscriptions.alpaca.map((symbol: string) => (
                      <Badge
                        key={symbol}
                        variant="outline"
                        className="hover:bg-slate-100 cursor-pointer transition-colors"
                      >
                        {symbol}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {serviceStatus.subscriptions.binance?.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">Crypto</Badge>
                      <span className="text-sm text-muted-foreground">
                        {serviceStatus.subscriptions.binance.length} symbols
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {serviceStatus.subscriptions.binance.map((symbol: string) => (
                      <Badge
                        key={symbol}
                        variant="outline"
                        className="hover:bg-slate-100 cursor-pointer transition-colors"
                      >
                        {symbol}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No active subscriptions
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default DashboardNew

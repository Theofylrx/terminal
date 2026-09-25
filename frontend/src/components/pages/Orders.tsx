import React, { useEffect, useState } from 'react'
import { Clock, CheckCircle2, XCircle, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Order {
  id: string
  symbol: string
  side: string
  type: string
  quantity: number
  filled_qty?: number
  limit_price?: number
  filled_avg_price?: number
  status: string
  created_at: string
  filled_at?: string
  broker: string
}

const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'filled' | 'pending' | 'cancelled'>('all')

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        // Mock orders - replace with actual API call
        const mockOrders: Order[] = [
          {
            id: '69a9602e-ee18-488a-ace3-94549b9b879e',
            symbol: 'AAPL',
            side: 'BUY',
            type: 'MARKET',
            quantity: 1,
            filled_qty: 1,
            filled_avg_price: 335.49,
            status: 'FILLED',
            created_at: new Date().toISOString(),
            filled_at: new Date().toISOString(),
            broker: 'alpaca'
          }
        ]
        setOrders(mockOrders)
      } catch (error) {
        console.error('Failed to fetch orders:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchOrders()
    const interval = setInterval(fetchOrders, 10000)
    return () => clearInterval(interval)
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'FILLED':
        return 'success'
      case 'PENDING':
      case 'NEW':
      case 'PARTIALLY_FILLED':
        return 'secondary'
      case 'CANCELLED':
      case 'REJECTED':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'FILLED':
        return <CheckCircle2 className="w-4 h-4" />
      case 'PENDING':
      case 'NEW':
        return <Clock className="w-4 h-4" />
      case 'CANCELLED':
      case 'REJECTED':
        return <XCircle className="w-4 h-4" />
      default:
        return <AlertCircle className="w-4 h-4" />
    }
  }

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true
    if (filter === 'filled') return order.status === 'FILLED'
    if (filter === 'pending') return ['PENDING', 'NEW', 'PARTIALLY_FILLED'].includes(order.status)
    if (filter === 'cancelled') return ['CANCELLED', 'REJECTED'].includes(order.status)
    return true
  })

  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Order History</h1>
          <p className="text-muted-foreground mt-1">
            Track all your trades and order executions
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <Badge
          variant={filter === 'all' ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilter('all')}
        >
          All Orders
        </Badge>
        <Badge
          variant={filter === 'filled' ? 'success' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilter('filled')}
        >
          Filled
        </Badge>
        <Badge
          variant={filter === 'pending' ? 'secondary' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilter('pending')}
        >
          Pending
        </Badge>
        <Badge
          variant={filter === 'cancelled' ? 'destructive' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilter('cancelled')}
        >
          Cancelled
        </Badge>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Orders</CardTitle>
            <CardDescription>
              {filteredOrders.length} {filter !== 'all' ? filter : ''} orders
            </CardDescription>
          </CardHeader>
          <CardContent>
            {filteredOrders.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500 mb-2 font-medium">No orders found</p>
                <p className="text-sm text-muted-foreground">
                  Your order history will appear here
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Symbol</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Side</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Quantity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Broker</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredOrders.map((order) => (
                      <tr key={order.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {new Date(order.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-medium text-slate-900">{order.symbol}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={order.side === 'BUY' ? 'success' : 'destructive'}>
                            {order.side === 'BUY' && <TrendingUp className="w-3 h-3 mr-1" />}
                            {order.side === 'SELL' && <TrendingDown className="w-3 h-3 mr-1" />}
                            {order.side}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="outline">{order.type}</Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {order.filled_qty || 0} / {order.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                          {order.filled_avg_price ? `$${order.filled_avg_price.toFixed(2)}` :
                           order.limit_price ? `$${order.limit_price.toFixed(2)}` : '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={getStatusBadge(order.status)}>
                            {getStatusIcon(order.status)}
                            <span className="ml-1">{order.status}</span>
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="secondary">
                            {order.broker.toUpperCase()}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Orders

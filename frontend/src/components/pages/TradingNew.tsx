import React, { useState } from 'react'
import { CheckCircle2, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const TradingNew: React.FC = () => {
  const [orderForm, setOrderForm] = useState({
    symbol: 'AAPL',
    assetClass: 'STOCK',
    side: 'BUY',
    orderType: 'MARKET',
    quantity: '',
    limitPrice: '',
    stopLoss: '',
    takeProfit: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{type: 'success' | 'error', message: string} | null>(null)

  const stockSymbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'NFLX', 'DIS']
  const cryptoSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT']

  const availableSymbols = orderForm.assetClass === 'STOCK' ? stockSymbols : cryptoSymbols

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8007/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'demo_user',
          symbol: orderForm.symbol,
          asset_class: orderForm.assetClass,
          side: orderForm.side,
          order_type: orderForm.orderType,
          quantity: parseFloat(orderForm.quantity),
          limit_price: orderForm.limitPrice ? parseFloat(orderForm.limitPrice) : undefined,
          stop_loss_price: orderForm.stopLoss ? parseFloat(orderForm.stopLoss) : undefined,
          take_profit_price: orderForm.takeProfit ? parseFloat(orderForm.takeProfit) : undefined,
        })
      })

      const data = await response.json()

      if (data.success) {
        setResult({ type: 'success', message: `Order executed successfully! Order ID: ${data.broker_order_id}` })
        setOrderForm(prev => ({ ...prev, symbol: '', quantity: '', limitPrice: '', stopLoss: '', takeProfit: '' }))
      } else {
        setResult({ type: 'error', message: data.error_message || 'Order execution failed' })
      }
    } catch (error) {
      setResult({ type: 'error', message: 'Failed to connect to executor service' })
    } finally {
      setSubmitting(false)
    }
  }

  const estimatedCost = orderForm.quantity && (orderForm.orderType === 'MARKET' || orderForm.limitPrice)
    ? (parseFloat(orderForm.quantity) * (orderForm.limitPrice ? parseFloat(orderForm.limitPrice) : 100)).toFixed(2)
    : '0.00'

  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trading</h1>
        <p className="text-muted-foreground mt-1">
          Execute trades across stocks and cryptocurrency
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Trading Form */}
        <div className="md:col-span-2 space-y-4">
          {/* Result Alert */}
          {result && (
            <div className={`flex items-start gap-3 p-4 rounded-lg border ${
              result.type === 'success'
                ? 'bg-emerald-50 border-emerald-200'
                : 'bg-red-50 border-red-200'
            }`}>
              {result.type === 'success' ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <p className={`text-sm ${
                result.type === 'success' ? 'text-emerald-700' : 'text-red-700'
              }`}>
                {result.message}
              </p>
            </div>
          )}

          {/* Order Entry Card */}
          <Card>
            <CardHeader>
              <CardTitle>Place Order</CardTitle>
              <CardDescription>
                Enter your order details below
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Asset Class & Symbol */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium leading-none">
                      Asset Class
                    </label>
                    <Select
                      value={orderForm.assetClass}
                      onChange={(e) => {
                        const newAssetClass = e.target.value
                        const newSymbol = newAssetClass === 'STOCK' ? 'AAPL' : 'BTCUSDT'
                        setOrderForm(prev => ({ ...prev, assetClass: newAssetClass, symbol: newSymbol }))
                      }}
                    >
                      <option value="STOCK">Stock</option>
                      <option value="CRYPTO">Crypto</option>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      Symbol
                    </label>
                    <Select
                      value={orderForm.symbol}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, symbol: e.target.value }))}
                      required
                    >
                      {availableSymbols.map(symbol => (
                        <option key={symbol} value={symbol}>{symbol}</option>
                      ))}
                    </Select>
                  </div>
                </div>

                {/* Order Type & Quantity */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium leading-none">
                      Order Type
                    </label>
                    <Select
                      value={orderForm.orderType}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, orderType: e.target.value }))}
                    >
                      <option value="MARKET">Market Order</option>
                      <option value="LIMIT">Limit Order</option>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium leading-none">
                      Quantity
                    </label>
                    <Input
                      type="number"
                      step="0.001"
                      placeholder="0.00"
                      value={orderForm.quantity}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, quantity: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                {/* Conditional Limit Price */}
                {orderForm.orderType === 'LIMIT' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium leading-none">
                      Limit Price
                    </label>
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={orderForm.limitPrice}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, limitPrice: e.target.value }))}
                    />
                  </div>
                )}

                {/* Buy/Sell Buttons */}
                <div className="grid grid-cols-2 gap-4 pt-4">
                  <Button
                    type="submit"
                    variant="success"
                    size="lg"
                    disabled={submitting}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'BUY' }))}
                    className={orderForm.side !== 'BUY' ? 'opacity-50' : ''}
                  >
                    <TrendingUp className="mr-2 h-4 w-4" />
                    {submitting && orderForm.side === 'BUY' ? 'Buying...' : 'Buy'}
                  </Button>
                  <Button
                    type="submit"
                    variant="destructive"
                    size="lg"
                    disabled={submitting}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'SELL' }))}
                    className={orderForm.side !== 'SELL' ? 'opacity-50' : ''}
                  >
                    <TrendingDown className="mr-2 h-4 w-4" />
                    {submitting && orderForm.side === 'SELL' ? 'Selling...' : 'Sell'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Risk Management */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Risk Management</CardTitle>
              <CardDescription>
                Optional stop loss and take profit levels
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">
                    Stop Loss
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={orderForm.stopLoss}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, stopLoss: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">
                    Take Profit
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={orderForm.takeProfit}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, takeProfit: e.target.value }))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Order Summary Sidebar */}
        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
              <CardDescription>
                Review your order before submitting
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Symbol</span>
                  <span className="text-sm font-medium">
                    {orderForm.symbol || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Side</span>
                  <Badge variant={orderForm.side === 'BUY' ? 'success' : 'destructive'}>
                    {orderForm.side}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Quantity</span>
                  <span className="text-sm font-medium">
                    {orderForm.quantity || '0'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Type</span>
                  <Badge variant="outline">
                    {orderForm.orderType}
                  </Badge>
                </div>
              </div>

              {orderForm.limitPrice && (
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Est. Cost</span>
                    <span className="text-lg font-bold">
                      ${estimatedCost}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default TradingNew

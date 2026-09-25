import React, { useState } from 'react'
import { CheckCircle2, AlertCircle } from 'lucide-react'

const Trading: React.FC = () => {
  const [orderForm, setOrderForm] = useState({
    symbol: '',
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
    <div className="p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Trading</h1>
          <p className="text-sm text-slate-600 mt-1">Execute trades across stocks and cryptocurrency</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-4">
            {/* Result Alert */}
            {result && (
              <div className={`flex items-start gap-3 p-4 rounded-lg border ${
                result.type === 'success'
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                {result.type === 'success' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <p className={`text-sm ${
                  result.type === 'success' ? 'text-emerald-700' : 'text-red-700'
                }`}>
                  {result.message}
                </p>
              </div>
            )}

            {/* Order Form */}
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h2 className="text-base font-semibold text-slate-900 mb-6">Place Order</h2>

              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Symbol & Asset Class */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Symbol</label>
                    <input
                      type="text"
                      placeholder="AAPL, BTCUSDT..."
                      value={orderForm.symbol}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Asset Class</label>
                    <select
                      value={orderForm.assetClass}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, assetClass: e.target.value }))}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="STOCK">Stock</option>
                      <option value="CRYPTO">Crypto</option>
                    </select>
                  </div>
                </div>

                {/* Order Type & Quantity */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Order Type</label>
                    <select
                      value={orderForm.orderType}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, orderType: e.target.value }))}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="MARKET">Market Order</option>
                      <option value="LIMIT">Limit Order</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Quantity</label>
                    <input
                      type="number"
                      step="0.001"
                      placeholder="0.00"
                      value={orderForm.quantity}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, quantity: e.target.value }))}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                {/* Conditional Limit Price */}
                {orderForm.orderType === 'LIMIT' && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Limit Price</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={orderForm.limitPrice}
                      onChange={(e) => setOrderForm(prev => ({ ...prev, limitPrice: e.target.value }))}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                )}

                {/* Buy/Sell Buttons */}
                <div className="grid grid-cols-2 gap-3 pt-4">
                  <button
                    type="submit"
                    disabled={submitting}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'BUY' }))}
                    className={`py-3 rounded-lg font-medium transition-colors ${
                      orderForm.side === 'BUY'
                        ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    } ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {submitting && orderForm.side === 'BUY' ? 'Buying...' : 'Buy'}
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    onClick={() => setOrderForm(prev => ({ ...prev, side: 'SELL' }))}
                    className={`py-3 rounded-lg font-medium transition-colors ${
                      orderForm.side === 'SELL'
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    } ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {submitting && orderForm.side === 'SELL' ? 'Selling...' : 'Sell'}
                  </button>
                </div>
              </form>
            </div>

            {/* Advanced Options */}
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h3 className="text-sm font-medium text-slate-900 mb-4">Risk Management (Optional)</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-600 mb-2">Stop Loss</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={orderForm.stopLoss}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, stopLoss: e.target.value }))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-600 mb-2">Take Profit</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={orderForm.takeProfit}
                    onChange={(e) => setOrderForm(prev => ({ ...prev, takeProfit: e.target.value }))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Order Summary Sidebar */}
          <div>
            <div className="bg-white border border-slate-200 rounded-lg p-6 sticky top-6">
              <h3 className="text-base font-semibold text-slate-900 mb-6">Order Summary</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Symbol</span>
                  <span className="text-sm font-medium text-slate-900">
                    {orderForm.symbol || '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Side</span>
                  <span className={`text-sm font-medium ${
                    orderForm.side === 'BUY' ? 'text-emerald-600' : 'text-red-600'
                  }`}>
                    {orderForm.side}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Quantity</span>
                  <span className="text-sm font-medium text-slate-900">
                    {orderForm.quantity || '0'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Type</span>
                  <span className="text-sm font-medium text-slate-900">
                    {orderForm.orderType}
                  </span>
                </div>
                {orderForm.limitPrice && (
                  <div className="flex justify-between items-center pt-3 border-t border-slate-200">
                    <span className="text-sm text-slate-600">Est. Cost</span>
                    <span className="text-sm font-semibold text-slate-900">
                      ${estimatedCost}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Trading

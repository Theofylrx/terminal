import React, { useState, useEffect } from 'react'
import { Star, TrendingUp, TrendingDown, Plus, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface WatchlistItem {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap?: string
}

const Watchlist: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 341.16,
      change: 5.67,
      changePercent: 1.69,
      volume: 45678900,
      marketCap: '2.8T'
    },
    {
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      price: 242.84,
      change: -3.21,
      changePercent: -1.31,
      volume: 89234500,
      marketCap: '771B'
    },
    {
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      price: 142.55,
      change: 2.15,
      changePercent: 1.53,
      volume: 23456780,
      marketCap: '1.8T'
    },
    {
      symbol: 'BTCUSDT',
      name: 'Bitcoin',
      price: 84110.25,
      change: 1245.67,
      changePercent: 1.50,
      volume: 156789000,
      marketCap: '1.6T'
    },
    {
      symbol: 'ETHUSDT',
      name: 'Ethereum',
      price: 2692.47,
      change: -45.23,
      changePercent: -1.65,
      volume: 89234500,
      marketCap: '323B'
    }
  ])
  const [newSymbol, setNewSymbol] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    const updatePrices = async () => {
      // Fetch real-time prices from Market Data Service
      const updatedWatchlist = await Promise.all(
        watchlist.map(async (item) => {
          try {
            // Try to fetch latest quote
            const response = await fetch(`http://localhost:8003/api/v1/quote/${item.symbol}`)
            if (response.ok) {
              const data = await response.json()
              const newPrice = data.price || item.price
              const change = newPrice - item.price
              const changePercent = (change / item.price) * 100

              return {
                ...item,
                price: newPrice,
                change: change,
                changePercent: changePercent
              }
            }
          } catch (error) {
            // Keep existing data if fetch fails
            console.debug(`Could not update ${item.symbol}`)
          }
          return item
        })
      )
      setWatchlist(updatedWatchlist)
    }

    // Update prices every 5 seconds
    const interval = setInterval(updatePrices, 5000)
    return () => clearInterval(interval)
  }, [watchlist.length]) // Only re-create interval when watchlist size changes

  const handleAddSymbol = () => {
    if (newSymbol.trim()) {
      // In real app, fetch symbol data from API
      const newItem: WatchlistItem = {
        symbol: newSymbol.toUpperCase(),
        name: newSymbol.toUpperCase(),
        price: 0,
        change: 0,
        changePercent: 0,
        volume: 0
      }
      setWatchlist([...watchlist, newItem])
      setNewSymbol('')
      setShowAddForm(false)
    }
  }

  const handleRemoveSymbol = (symbol: string) => {
    setWatchlist(watchlist.filter(item => item.symbol !== symbol))
  }

  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Watchlist</h1>
          <p className="text-muted-foreground mt-1">
            Monitor your favorite symbols in real-time
          </p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Symbol
        </Button>
      </div>

      {/* Add Symbol Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add Symbol to Watchlist</CardTitle>
            <CardDescription>
              Enter a stock or crypto symbol to track
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <Input
                placeholder="Enter symbol (e.g., AAPL, BTCUSDT)"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
              />
              <Button onClick={handleAddSymbol}>Add</Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Watchlist Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {watchlist.map((item) => (
          <Card key={item.symbol} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{item.symbol}</CardTitle>
                  <CardDescription className="text-xs">{item.name}</CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveSymbol(item.symbol)}
                  className="h-8 w-8 p-0"
                >
                  <Trash2 className="w-4 h-4 text-slate-400 hover:text-red-600" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Price */}
                <div>
                  <div className="text-2xl font-bold">
                    ${item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className={`flex items-center gap-1 text-sm font-medium ${
                    item.change >= 0 ? 'text-emerald-600' : 'text-red-600'
                  }`}>
                    {item.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {item.change >= 0 ? '+' : ''}${item.change.toFixed(2)} ({item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-200">
                  <div>
                    <div className="text-xs text-muted-foreground">Volume</div>
                    <div className="text-sm font-medium">{(item.volume / 1000000).toFixed(1)}M</div>
                  </div>
                  {item.marketCap && (
                    <div>
                      <div className="text-xs text-muted-foreground">Market Cap</div>
                      <div className="text-sm font-medium">${item.marketCap}</div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    Chart
                  </Button>
                  <Button size="sm" className="flex-1">
                    Trade
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {watchlist.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Star className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 mb-2 font-medium">No symbols in your watchlist</p>
            <p className="text-sm text-muted-foreground mb-4">
              Add symbols to track your favorite assets
            </p>
            <Button onClick={() => setShowAddForm(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add First Symbol
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Watchlist

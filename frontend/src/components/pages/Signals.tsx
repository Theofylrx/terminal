import React, { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity, AlertCircle, CheckCircle2, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface Signal {
  symbol: string
  direction: string
  confidence: number
  timeframe: string
  patterns: string[]
  indicators: any
  support_levels: number[]
  resistance_levels: number[]
  reasoning: string
  timestamp: string
}

const Signals: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        // Fetch signals for multiple symbols
        const symbols = ['AAPL', 'TSLA', 'GOOGL', 'BTCUSDT', 'ETHUSDT']
        const signalPromises = symbols.map(async (symbol) => {
          try {
            const response = await fetch('http://localhost:8004/api/v1/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                symbol,
                timeframes: ['5m', '15m', '1h'],
                include_reasoning: true
              })
            })
            const data = await response.json()
            return { ...data, timestamp: new Date().toISOString() }
          } catch (error) {
            console.error(`Failed to fetch signal for ${symbol}:`, error)
            return null
          }
        })

        const results = await Promise.all(signalPromises)
        setSignals(results.filter(s => s !== null))
      } catch (error) {
        console.error('Failed to fetch signals:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchSignals()
    const interval = setInterval(fetchSignals, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'BULLISH':
        return 'text-emerald-600'
      case 'BEARISH':
        return 'text-red-600'
      default:
        return 'text-slate-600'
    }
  }

  const getDirectionBadge = (direction: string) => {
    switch (direction) {
      case 'BULLISH':
        return 'success'
      case 'BEARISH':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'text-emerald-600'
    if (confidence >= 50) return 'text-amber-600'
    return 'text-slate-600'
  }

  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trading Signals</h1>
          <p className="text-muted-foreground mt-1">
            AI-powered technical analysis signals across all assets
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" className="h-6">
            <span className="w-1.5 h-1.5 bg-white rounded-full mr-1.5 animate-pulse"></span>
            Live
          </Badge>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
        </div>
      ) : (
        <>
          {/* Signal Strength Overview */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Strong Signals
                </CardTitle>
                <Zap className="h-4 w-4 text-amber-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {signals.filter(s => s.confidence >= 70).length}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  ≥70% confidence
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Bullish
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-emerald-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-600">
                  {signals.filter(s => s.direction === 'BULLISH').length}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Buy opportunities
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Bearish
                </CardTitle>
                <TrendingDown className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {signals.filter(s => s.direction === 'BEARISH').length}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Sell opportunities
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Signals List */}
          <div className="grid gap-4 md:grid-cols-1">
            {signals.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Activity className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500 mb-2 font-medium">No signals available</p>
                  <p className="text-sm text-muted-foreground">
                    Waiting for technical analysis data to generate signals
                  </p>
                </CardContent>
              </Card>
            ) : (
              signals.map((signal, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CardTitle className="text-xl">{signal.symbol}</CardTitle>
                        <Badge variant={getDirectionBadge(signal.direction)}>
                          {signal.direction}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">Confidence</div>
                          <div className={`text-xl font-bold ${getConfidenceColor(signal.confidence)}`}>
                            {signal.confidence}%
                          </div>
                        </div>
                        {signal.confidence >= 70 && (
                          <Button size="sm" variant={signal.direction === 'BULLISH' ? 'default' : 'destructive'}>
                            {signal.direction === 'BULLISH' ? 'Buy' : 'Sell'}
                          </Button>
                        )}
                      </div>
                    </div>
                    <CardDescription>
                      {new Date(signal.timestamp).toLocaleString()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Reasoning */}
                    <div>
                      <div className="text-sm font-medium mb-2">Analysis</div>
                      <p className="text-sm text-muted-foreground">{signal.reasoning}</p>
                    </div>

                    {/* Patterns */}
                    {signal.patterns && signal.patterns.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-2">Patterns Detected</div>
                        <div className="flex flex-wrap gap-2">
                          {signal.patterns.map((pattern, i) => (
                            <Badge key={i} variant="outline">
                              {pattern}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Support/Resistance */}
                    <div className="grid grid-cols-2 gap-4">
                      {signal.support_levels && signal.support_levels.length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-2 flex items-center gap-1">
                            <TrendingDown className="w-4 h-4 text-emerald-600" />
                            Support Levels
                          </div>
                          <div className="space-y-1">
                            {signal.support_levels.map((level, i) => (
                              <div key={i} className="text-sm text-emerald-600 font-mono">
                                ${level.toFixed(2)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {signal.resistance_levels && signal.resistance_levels.length > 0 && (
                        <div>
                          <div className="text-sm font-medium mb-2 flex items-center gap-1">
                            <TrendingUp className="w-4 h-4 text-red-600" />
                            Resistance Levels
                          </div>
                          <div className="space-y-1">
                            {signal.resistance_levels.map((level, i) => (
                              <div key={i} className="text-sm text-red-600 font-mono">
                                ${level.toFixed(2)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Signals

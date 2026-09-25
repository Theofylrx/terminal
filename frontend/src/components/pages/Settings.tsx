import React from 'react'
import { Shield, Key, User, Bell, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const Settings: React.FC = () => {
  return (
    <div className="flex-1 space-y-6 p-8 bg-slate-50">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage your account and trading preferences
          </p>
        </div>

        <div className="space-y-4">
          {/* API Keys */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-blue-600" />
                  <CardTitle>API Keys</CardTitle>
                </div>
                <Badge variant="outline">Encrypted</Badge>
              </div>
              <CardDescription>
                Connect your broker accounts to enable live trading
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Alpaca API Key
                </label>
                <Input
                  type="password"
                  placeholder="••••••••••••••••"
                />
                <p className="text-xs text-muted-foreground">
                  Your Alpaca API key for stock trading
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Alpaca Secret Key
                </label>
                <Input
                  type="password"
                  placeholder="••••••••••••••••"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Binance API Key
                </label>
                <Input
                  type="password"
                  placeholder="••••••••••••••••"
                />
                <p className="text-xs text-muted-foreground">
                  Your Binance API key for cryptocurrency trading
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Binance Secret Key
                </label>
                <Input
                  type="password"
                  placeholder="••••••••••••••••"
                />
              </div>
            </CardContent>
          </Card>

          {/* Risk Management */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-emerald-600" />
                <CardTitle>Risk Management</CardTitle>
              </div>
              <CardDescription>
                Configure your risk limits to protect your capital
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Max Risk Per Trade (%)
                  </label>
                  <Input
                    type="number"
                    defaultValue="1"
                    step="0.1"
                    min="0.1"
                    max="10"
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum % of account to risk per trade
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Max Daily Loss (%)
                  </label>
                  <Input
                    type="number"
                    defaultValue="5"
                    step="0.5"
                    min="1"
                    max="20"
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum daily loss before trading stops
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Auto-Trading Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-amber-600" />
                <CardTitle>Auto-Trading</CardTitle>
              </div>
              <CardDescription>
                Configure autonomous trading behavior
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Min Confidence (%)
                  </label>
                  <Input
                    type="number"
                    defaultValue="70"
                    step="5"
                    min="50"
                    max="95"
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum signal confidence to execute trades
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Max Positions
                  </label>
                  <Input
                    type="number"
                    defaultValue="10"
                    min="1"
                    max="50"
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum concurrent positions allowed
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end gap-3">
            <Button variant="outline">
              Cancel
            </Button>
            <Button>
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings

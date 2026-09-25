import React, { useState } from 'react'
import { Activity, TrendingUp, Shield, Zap, Eye, EyeOff, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface LoginProps {
  onLogin: () => void
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 1200))
    setLoading(false)
    onLogin()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.5))] -z-10"></div>

      <div className="w-full max-w-6xl grid md:grid-cols-2 gap-8 items-center">
        {/* Left Side - Branding */}
        <div className="hidden md:block space-y-6">
          <div className="inline-flex items-center gap-3">
            <div className="flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg">
              <Activity className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Terminal</h1>
              <p className="text-sm text-slate-600">AI-Powered Trading Platform</p>
            </div>
          </div>

          <div className="space-y-4 pt-8">
            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Multi-Asset Trading</h3>
                <p className="text-sm text-slate-600 mt-1">Trade stocks, crypto, and forex from one platform</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center w-10 h-10 bg-emerald-100 rounded-lg flex-shrink-0">
                <Zap className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Autonomous Trading</h3>
                <p className="text-sm text-slate-600 mt-1">AI-powered auto-trading with technical analysis</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center w-10 h-10 bg-purple-100 rounded-lg flex-shrink-0">
                <Shield className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Enterprise Security</h3>
                <p className="text-sm text-slate-600 mt-1">Bank-level encryption and security protocols</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center w-10 h-10 bg-orange-100 rounded-lg flex-shrink-0">
                <BarChart3 className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Real-Time Analytics</h3>
                <p className="text-sm text-slate-600 mt-1">Advanced charting and market data visualization</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <Card className="shadow-xl border-slate-200">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
            <CardDescription>
              Sign in to your account to continue trading
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Email
                </label>
                <Input
                  type="email"
                  value={credentials.email}
                  onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="name@company.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  Password
                </label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={credentials.password}
                    onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={loading}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Signing in...
                  </span>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200"></div>
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-2 bg-white text-slate-500">Or continue with</span>
                </div>
              </div>

              <Button
                type="button"
                onClick={onLogin}
                variant="outline"
                className="w-full mt-4"
                size="lg"
              >
                Demo Account
              </Button>
            </div>

            {/* Footer */}
            <p className="text-center text-xs text-slate-500 mt-6">
              By signing in, you agree to our{' '}
              <a href="#" className="text-blue-600 hover:underline">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-blue-600 hover:underline">Privacy Policy</a>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Login

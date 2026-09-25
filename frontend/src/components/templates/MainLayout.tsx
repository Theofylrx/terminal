import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  Wallet,
  Settings,
  BarChart3,
  Activity,
  LogOut,
  Bell,
  Search,
  ChevronDown,
  Zap,
  FileText,
  Star
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface MainLayoutProps {
  children: React.ReactNode
  onLogout?: () => void
}

const MainLayout: React.FC<MainLayoutProps> = ({ children, onLogout }) => {
  const location = useLocation()
  const [accountData, setAccountData] = useState<any>(null)
  const [notifications, setNotifications] = useState(3) // Mock notification count

  useEffect(() => {
    const fetchAccount = async () => {
      try {
        const response = await fetch('http://localhost:8007/api/v1/account/demo_user')
        const data = await response.json()
        setAccountData(data)
      } catch (error) {
        console.error('Failed to fetch account:', error)
      }
    }

    fetchAccount()
    const interval = setInterval(fetchAccount, 30000)
    return () => clearInterval(interval)
  }, [])

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Trading', href: '/trading', icon: TrendingUp },
    { name: 'Portfolio', href: '/portfolio', icon: Wallet },
    { name: 'Signals', href: '/signals', icon: Zap },
    { name: 'Orders', href: '/orders', icon: FileText },
    { name: 'Watchlist', href: '/watchlist', icon: Star },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  const isActive = (href: string) => {
    if (href === '/') return location.pathname === '/'
    return location.pathname.startsWith(href)
  }

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-900">Terminal</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)

            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-slate-200">
          <div className="space-y-2">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-sm font-semibold">
                U
              </div>
              <div className="flex-1 text-left">
                <div className="text-sm font-medium text-slate-900">User</div>
                <div className="text-xs text-slate-500">demo_user</div>
              </div>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-red-50 text-red-600 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm font-medium">Logout</span>
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search symbols..."
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Balance */}
            <div className="flex items-center gap-3 px-4 py-2 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex flex-col">
                <span className="text-xs text-slate-500">Buying Power</span>
                <span className="text-sm font-semibold text-slate-900">
                  ${accountData?.total_equity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </span>
              </div>
            </div>

            {/* Notifications */}
            <button className="relative p-2 hover:bg-slate-50 rounded-lg transition-colors">
              <Bell className="w-5 h-5 text-slate-600" />
              {notifications > 0 && (
                <Badge
                  variant="destructive"
                  className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                >
                  {notifications}
                </Badge>
              )}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-slate-50">
          {children}
        </main>
      </div>
    </div>
  )
}

export default MainLayout

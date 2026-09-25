import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/templates/MainLayout'
import Login from './components/pages/Login'
import DashboardNew from './components/pages/DashboardNew'
import TradingNew from './components/pages/TradingNew'
import Portfolio from './components/pages/Portfolio'
import Settings from './components/pages/Settings'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<DashboardNew />} />
          <Route path="/trading" element={<TradingNew />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/analysis" element={<DashboardNew />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  )
}

export default App

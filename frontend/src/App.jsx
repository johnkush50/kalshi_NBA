import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import GameList from './components/Games/GameList'

function StrategiesPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Strategies</h2>
      <p className="text-gray-400">Strategy management coming soon...</p>
    </div>
  )
}

function TradingPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Trading</h2>
      <p className="text-gray-400">Order history and positions coming soon...</p>
    </div>
  )
}

function PnLPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">P&L</h2>
      <p className="text-gray-400">P&L dashboard coming soon...</p>
    </div>
  )
}

function RiskPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Risk Management</h2>
      <p className="text-gray-400">Risk controls coming soon...</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<GameList />} />
          <Route path="strategies" element={<StrategiesPage />} />
          <Route path="trading" element={<TradingPage />} />
          <Route path="pnl" element={<PnLPage />} />
          <Route path="risk" element={<RiskPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import GamesPage from './pages/GamesPage'
import StrategiesPage from './pages/StrategiesPage'
import TradingPage from './pages/TradingPage'
import PnLPage from './pages/PnLPage'
import RiskPage from './pages/RiskPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<GamesPage />} />
        <Route path="strategies" element={<StrategiesPage />} />
        <Route path="trading" element={<TradingPage />} />
        <Route path="pnl" element={<PnLPage />} />
        <Route path="risk" element={<RiskPage />} />
      </Route>
    </Routes>
  )
}

export default App

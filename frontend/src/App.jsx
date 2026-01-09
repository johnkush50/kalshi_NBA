import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import GameList from './components/Games/GameList'
import StrategyList from './components/Strategies/StrategyList'
import TradingPage from './components/Trading/TradingPage'
import PnLPage from './components/PnL/PnLPage'
import RiskPage from './components/Risk/RiskPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<GameList />} />
          <Route path="strategies" element={<StrategyList />} />
          <Route path="trading" element={<TradingPage />} />
          <Route path="pnl" element={<PnLPage />} />
          <Route path="risk" element={<RiskPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

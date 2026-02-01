import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import PortfolioOverview from './pages/PortfolioOverview'
import CompanyAnalysis from './pages/CompanyAnalysis'
import Marketplace from './pages/Marketplace'
import Swaps from './pages/Swaps'
import MarketIntel from './pages/MarketIntel'
import Simulator from './pages/Simulator'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/portfolio" replace />} />
          <Route path="portfolio" element={<PortfolioOverview />} />
          <Route path="company" element={<CompanyAnalysis />} />
          <Route path="marketplace" element={<Marketplace />} />
          <Route path="swaps" element={<Swaps />} />
          <Route path="market" element={<MarketIntel />} />
          <Route path="simulator" element={<Simulator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

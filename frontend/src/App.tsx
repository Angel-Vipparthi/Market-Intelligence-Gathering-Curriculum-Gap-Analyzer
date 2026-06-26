import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import URLManagement from './pages/URLManagement'
import DigestReview from './pages/DigestReview'
import GapReview from './pages/GapReview'
import CostAnalytics from './pages/CostAnalytics'
import Skills from './pages/Skills'
import KnowledgeGraph from './pages/KnowledgeGraph'
import GapReport from './pages/GapReport'
import KnowledgeBase from './pages/KnowledgeBase'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/urls" element={<URLManagement />} />
        <Route path="/digests" element={<DigestReview />} />
        <Route path="/gaps" element={<GapReview />} />
        <Route path="/report" element={<GapReport />} />
        <Route path="/kb" element={<KnowledgeBase />} />
        <Route path="/costs" element={<CostAnalytics />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/graph" element={<KnowledgeGraph />} />
      </Route>
    </Routes>
  )
}

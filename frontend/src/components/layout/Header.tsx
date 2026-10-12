import { useLocation, Link } from 'react-router-dom'
import { Bell, Search, DollarSign, Zap } from 'lucide-react'
import { useCostDashboard } from '@/hooks/useCosts'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/urls': 'URL Sources',
  '/digests': 'Digest Review',
  '/gaps': 'Gap Analysis',
  '/report': 'Gap Report',
  '/kb': 'Knowledge Base',
  '/costs': 'Cost Analytics',
  '/skills': 'Skills & Prompts',
  '/graph': 'Knowledge Graph',
}

const descriptions: Record<string, string> = {
  '/': 'Overview of curriculum gaps and system health',
  '/urls': 'Manage monitored URL sources',
  '/digests': 'Review AI-generated market intelligence digests',
  '/gaps': 'Review and act on detected curriculum gaps',
  '/report': 'Consolidated gap findings and recommendations',
  '/kb': 'Curriculum knowledge base documents',
  '/costs': 'Track LLM usage and operational costs',
  '/skills': 'Agent capabilities and performance',
  '/graph': 'Curriculum knowledge graph visualization',
}

function formatCost(cost: number): string {
  if (cost >= 1) return `$${cost.toFixed(2)}`
  if (cost >= 0.01) return `$${cost.toFixed(4)}`
  return `$${cost.toFixed(6)}`
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return String(tokens)
}

export default function Header() {
  const { pathname } = useLocation()
  const { data: costs } = useCostDashboard()

  const totalCost = costs?.summary?.total_cost ?? 0
  const totalTokens = (costs?.summary?.total_input_tokens ?? 0) + (costs?.summary?.total_output_tokens ?? 0)

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-slate-900">{titles[pathname] ?? 'Gap Analyzer'}</h2>
        <p className="text-xs text-slate-400">{descriptions[pathname] ?? ''}</p>
      </div>
      <div className="flex items-center gap-3">
        <Link
          to="/costs"
          className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 transition hover:border-emerald-200 hover:bg-emerald-50"
        >
          <div className="flex items-center gap-1">
            <DollarSign className="h-3.5 w-3.5 text-emerald-600" />
            <span className="text-[12px] font-bold tabular-nums text-emerald-700">{formatCost(totalCost)}</span>
          </div>
          <div className="h-3.5 w-px bg-slate-200" />
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3 text-amber-500" />
            <span className="text-[11px] tabular-nums text-slate-500">{formatTokens(totalTokens)}</span>
          </div>
        </Link>
        <button className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600">
          <Search className="h-4 w-4" />
        </button>
        <button className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600">
          <Bell className="h-4 w-4" />
        </button>
        <div className="h-8 w-8 rounded-full bg-indigo-100 text-center text-sm font-semibold leading-8 text-indigo-700">A</div>
      </div>
    </header>
  )
}

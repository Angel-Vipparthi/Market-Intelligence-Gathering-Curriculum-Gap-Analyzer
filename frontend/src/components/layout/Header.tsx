import { useLocation } from 'react-router-dom'
import { Bell, Search } from 'lucide-react'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/urls': 'URL Sources',
  '/digests': 'Digest Review',
  '/gaps': 'Gap Analysis',
  '/costs': 'Cost Analytics',
  '/skills': 'Skills & Prompts',
  '/graph': 'Knowledge Graph',
}

const descriptions: Record<string, string> = {
  '/': 'Overview of curriculum gaps and system health',
  '/urls': 'Manage monitored URL sources',
  '/digests': 'Review AI-generated market intelligence digests',
  '/gaps': 'Review and act on detected curriculum gaps',
  '/costs': 'Track LLM usage and operational costs',
  '/skills': 'Agent capabilities and performance',
  '/graph': 'Curriculum knowledge graph visualization',
}

export default function Header() {
  const { pathname } = useLocation()
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-slate-900">{titles[pathname] ?? 'Gap Analyzer'}</h2>
        <p className="text-xs text-slate-400">{descriptions[pathname] ?? ''}</p>
      </div>
      <div className="flex items-center gap-3">
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

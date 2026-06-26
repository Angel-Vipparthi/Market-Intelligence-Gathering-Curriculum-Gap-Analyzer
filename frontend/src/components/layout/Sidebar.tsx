import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Link2, FileText, AlertTriangle, DollarSign, Wrench, GitBranch, Zap, ClipboardList, BookOpen } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/urls', label: 'URL Sources', icon: Link2 },
  { to: '/kb', label: 'Knowledge Base', icon: BookOpen },
  { to: '/digests', label: 'Digest Review', icon: FileText },
  { to: '/gaps', label: 'Gap Analysis', icon: AlertTriangle },
  { to: '/report', label: 'Gap Report', icon: ClipboardList },
  { to: '/graph', label: 'Knowledge Graph', icon: GitBranch },
  { to: '/costs', label: 'Cost Analytics', icon: DollarSign },
  { to: '/skills', label: 'Skills', icon: Wrench },
]

export default function Sidebar() {
  return (
    <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2.5 border-b border-slate-200 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-slate-900">Gap Analyzer</h1>
          <p className="text-2xs text-slate-400">Market Intelligence</p>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700 shadow-sm'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
              }`
            }
          >
            <item.icon className="h-[18px] w-[18px]" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-200 px-5 py-3">
        <p className="text-2xs text-slate-400">v1.0 — Curriculum Platform</p>
      </div>
    </aside>
  )
}

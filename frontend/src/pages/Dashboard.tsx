import { useGapSummary } from '@/hooks/useGaps'
import { useCostDashboard } from '@/hooks/useCosts'
import { useDigests } from '@/hooks/useDigests'
import StatCard from '@/components/common/StatCard'
import { AlertTriangle, TrendingUp, Clock, DollarSign } from 'lucide-react'

const sevColors: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-400',
  medium: 'bg-amber-400',
  low: 'bg-emerald-400',
}

export default function Dashboard() {
  const { data: summary } = useGapSummary()
  const { data: costs } = useCostDashboard()
  const { data: digests } = useDigests('')

  const totalGaps = summary?.total ?? 0
  const criticalGaps = summary?.by_severity?.critical ?? 0
  const pendingReview = summary?.by_status?.pending_review ?? 0

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-4 gap-5">
        <StatCard
          title="Total Gaps"
          value={totalGaps}
          color="indigo"
          icon={<AlertTriangle className="h-4 w-4" />}
        />
        <StatCard
          title="Critical Gaps"
          value={criticalGaps}
          color="red"
          icon={<TrendingUp className="h-4 w-4" />}
          subtitle={criticalGaps > 0 ? 'Needs immediate attention' : 'All clear'}
        />
        <StatCard
          title="Pending Review"
          value={pendingReview}
          color="yellow"
          icon={<Clock className="h-4 w-4" />}
        />
        <StatCard
          title="Total Cost"
          value={`$${(costs?.summary?.total_cost ?? 0).toFixed(4)}`}
          color="green"
          icon={<DollarSign className="h-4 w-4" />}
          subtitle={`${((costs?.summary?.total_input_tokens ?? 0) + (costs?.summary?.total_output_tokens ?? 0)).toLocaleString()} tokens`}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
          <h3 className="text-sm font-semibold text-slate-900">Gaps by Severity</h3>
          <p className="mb-4 text-xs text-slate-400">Distribution across severity levels</p>
          <div className="space-y-3">
            {summary?.by_severity && Object.entries(summary.by_severity).map(([sev, count]) => {
              const pct = totalGaps > 0 ? Math.round(((count as number) / totalGaps) * 100) : 0
              return (
                <div key={sev}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-[13px] font-medium capitalize text-slate-600">{sev}</span>
                    <span className="text-[13px] font-bold tabular-nums text-slate-900">{count as number}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className={`h-full rounded-full ${sevColors[sev] ?? 'bg-slate-300'} transition-all duration-500`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
            {!summary?.by_severity && <p className="text-sm text-slate-400">No data yet</p>}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
          <h3 className="text-sm font-semibold text-slate-900">Gaps by Type</h3>
          <p className="mb-4 text-xs text-slate-400">Categorized curriculum gap types</p>
          <div className="space-y-2.5">
            {summary?.by_type && Object.entries(summary.by_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                <span className="text-[13px] text-slate-600">{(type as string).replace(/_/g, ' ')}</span>
                <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-[12px] font-bold tabular-nums text-indigo-700">{count as number}</span>
              </div>
            ))}
            {!summary?.by_type && <p className="text-sm text-slate-400">No data yet</p>}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
        <h3 className="text-sm font-semibold text-slate-900">Recent Digests</h3>
        <p className="mb-4 text-xs text-slate-400">Latest market intelligence digests</p>
        <div className="space-y-2">
          {digests?.items?.slice(0, 5).map((d) => (
            <div key={d.digest_id} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-slate-700">{d.topic || 'Untitled'}</p>
                <p className="mt-0.5 truncate text-xs text-slate-400">{d.url}</p>
              </div>
              <div className="ml-4 flex items-center gap-2">
                <span className={`rounded-md px-2 py-0.5 text-[11px] font-semibold ${d.curriculum_relevant === 'Yes' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                  {d.curriculum_relevant === 'Yes' ? 'Relevant' : 'Not Relevant'}
                </span>
                <span className="text-2xs text-slate-400">{d.market_signal}</span>
              </div>
            </div>
          ))}
          {!digests?.items?.length && <p className="text-sm text-slate-400">No digests processed yet</p>}
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useCostDashboard } from '@/hooks/useCosts'
import {
  DollarSign, Cpu, Activity, TrendingUp, Zap, Clock,
  BarChart3, ArrowUpRight, ArrowDownRight, Loader2,
} from 'lucide-react'

const NODE_COLORS: Record<string, string> = {
  digest_gen: 'bg-blue-500',
  gap_detect: 'bg-amber-500',
  impact_analysis: 'bg-red-500',
  critic: 'bg-purple-500',
  severity_scoring: 'bg-rose-500',
  relevance_check: 'bg-emerald-500',
  signal_extract: 'bg-cyan-500',
  tool_extract: 'bg-indigo-500',
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

export default function CostAnalytics() {
  const { data, isLoading } = useCostDashboard()
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null)

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
    </div>
  )

  const summary = data?.summary
  const byWorkflow = data?.by_workflow ?? []
  const byNode = data?.by_node ?? []
  const daily = data?.daily ?? []

  const totalTokens = (summary?.total_input_tokens ?? 0) + (summary?.total_output_tokens ?? 0)
  const maxDailyCost = Math.max(...daily.map(d => d.total_cost), 0.0001)

  const filteredNodes = selectedWorkflow
    ? byNode.filter(n => n.node_name.toLowerCase().includes(selectedWorkflow.toLowerCase()))
    : byNode

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100">
              <DollarSign className="h-4 w-4 text-emerald-600" />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Spend</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatCost(summary?.total_cost ?? 0)}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100">
              <Cpu className="h-4 w-4 text-indigo-600" />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Tokens</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatTokens(totalTokens)}</p>
          <div className="mt-1 flex gap-3 text-[10px] text-slate-400">
            <span><ArrowUpRight className="inline h-3 w-3 text-blue-400" /> {formatTokens(summary?.total_input_tokens ?? 0)} in</span>
            <span><ArrowDownRight className="inline h-3 w-3 text-amber-400" /> {formatTokens(summary?.total_output_tokens ?? 0)} out</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100">
              <Activity className="h-4 w-4 text-purple-600" />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Runs</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{summary?.total_runs ?? 0}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100">
              <TrendingUp className="h-4 w-4 text-amber-600" />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Avg / Run</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatCost(summary?.avg_cost_per_run ?? 0)}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-100">
              <Zap className="h-4 w-4 text-cyan-600" />
            </div>
            <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Workflows</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{byWorkflow.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Cost by Workflow */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-slate-400" />
              <h3 className="text-sm font-semibold text-slate-900">Cost by Workflow</h3>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">Click to filter nodes</p>
          </div>
          <div className="p-4 space-y-1">
            {byWorkflow.length === 0 ? (
              <p className="text-sm text-slate-300 text-center py-6">No cost data yet. Run gap analysis to see costs.</p>
            ) : (
              byWorkflow
                .sort((a, b) => b.total_cost - a.total_cost)
                .map(w => {
                  const isSelected = selectedWorkflow === w.workflow_type
                  const maxCost = Math.max(...byWorkflow.map(x => x.total_cost), 0.0001)
                  const pct = (w.total_cost / maxCost) * 100
                  return (
                    <button key={w.workflow_type}
                      onClick={() => setSelectedWorkflow(isSelected ? null : w.workflow_type)}
                      className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 transition text-left ${
                        isSelected ? 'bg-indigo-50 ring-1 ring-indigo-200' : 'hover:bg-slate-50'
                      }`}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[13px] font-medium text-slate-700 truncate">{w.workflow_type}</span>
                          <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[12px] font-bold tabular-nums text-emerald-700 flex-shrink-0 ml-2">
                            {formatCost(w.total_cost)}
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div className="h-full rounded-full bg-indigo-400 transition-all duration-500" style={{ width: `${pct}%` }} />
                        </div>
                        <div className="flex justify-between mt-1">
                          <span className="text-[10px] text-slate-400">{w.total_runs} runs</span>
                          <span className="text-[10px] text-slate-400">{formatCost(w.avg_cost_per_run)}/run</span>
                        </div>
                      </div>
                    </button>
                  )
                })
            )}
          </div>
        </div>

        {/* Cost by Node */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-900">Cost by Node</h3>
              </div>
              {selectedWorkflow && (
                <span className="rounded-lg bg-indigo-50 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-600">
                  Filtered: {selectedWorkflow}
                </span>
              )}
            </div>
            <p className="mt-0.5 text-xs text-slate-400">Per-node cost and latency</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50">
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Node</th>
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Model</th>
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 text-right">Cost</th>
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 text-right">Calls</th>
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 text-right">Avg Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredNodes.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-300">No node data</td></tr>
                ) : (
                  filteredNodes
                    .sort((a, b) => b.total_cost - a.total_cost)
                    .map((n, i) => (
                      <tr key={i} className="hover:bg-slate-50/50 transition">
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className={`h-2 w-2 rounded-full ${NODE_COLORS[n.node_name] ?? 'bg-slate-400'}`} />
                            <span className="text-[13px] font-medium text-slate-700">{n.node_name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                            {n.model.split('/').pop()}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="text-[12px] font-bold tabular-nums text-emerald-700">{formatCost(n.total_cost)}</span>
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="text-[12px] tabular-nums text-slate-600">{n.total_calls}</span>
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Clock className="h-3 w-3 text-slate-300" />
                            <span className="text-[12px] tabular-nums text-slate-500">
                              {n.avg_latency_ms != null ? `${n.avg_latency_ms}ms` : '—'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Daily Cost Trend */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-900">Daily Cost Trend</h3>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">Spending over time</p>
        </div>
        <div className="p-6">
          {daily.length === 0 ? (
            <p className="text-sm text-slate-300 text-center py-6">No daily data yet</p>
          ) : (
            <div className="space-y-2">
              {daily.map(d => {
                const pct = (d.total_cost / maxDailyCost) * 100
                return (
                  <div key={d.date} className="flex items-center gap-4">
                    <span className="w-24 text-[12px] font-medium tabular-nums text-slate-500 flex-shrink-0">{d.date}</span>
                    <div className="flex-1">
                      <div className="h-7 overflow-hidden rounded-lg bg-slate-50">
                        <div
                          className="flex h-full items-center rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-400 px-2.5 transition-all duration-700"
                          style={{ width: `${Math.max(3, pct)}%` }}>
                          {pct > 20 && (
                            <span className="text-[10px] font-bold text-white whitespace-nowrap">{formatCost(d.total_cost)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0 w-32 justify-end">
                      {pct <= 20 && (
                        <span className="text-[12px] font-semibold tabular-nums text-slate-700">{formatCost(d.total_cost)}</span>
                      )}
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
                        {d.total_runs} runs
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

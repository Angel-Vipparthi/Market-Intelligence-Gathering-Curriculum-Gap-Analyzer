import { useState, useEffect } from 'react'
import { useGaps, useReviewGap, useRunAllGapAnalysis, useGapSummary, useGapBatchProgress, useSubmitGapFeedback } from '@/hooks/useGaps'
import type { GapBatchItem } from '@/hooks/useGaps'
import SeverityBadge from '@/components/common/SeverityBadge'
import StatusBadge from '@/components/common/StatusBadge'
import type { Gap } from '@/lib/types'
import { CheckCircle, XCircle, Eye, Calendar, Layers, Play, Loader2, AlertTriangle, Zap, X, Check, Clock } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

function GapProgressModal({
  isOpen,
  onClose,
  digestIds,
}: {
  isOpen: boolean
  onClose: () => void
  digestIds: string[]
}) {
  const { data: progress } = useGapBatchProgress(digestIds, isOpen)
  const qc = useQueryClient()
  const completed = progress?.completed ?? 0
  const total = progress?.total ?? digestIds.length
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  const allDone = completed === total && total > 0
  const totalGapsFound = progress?.items?.reduce((sum: number, i: GapBatchItem) => sum + i.gaps_found, 0) ?? 0

  useEffect(() => {
    if (allDone) {
      qc.invalidateQueries({ queryKey: ['gaps'] })
      qc.invalidateQueries({ queryKey: ['gap-summary'] })
    }
  }, [allDone, qc])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl mx-4 rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-amber-50 to-white">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${allDone ? 'bg-emerald-100' : 'bg-amber-100'}`}>
              {allDone ? <Check className="h-5 w-5 text-emerald-600" /> : <Loader2 className="h-5 w-5 text-amber-600 animate-spin" />}
            </div>
            <div>
              <h3 className="text-[15px] font-bold text-slate-900">
                {allDone ? 'Gap Analysis Complete' : 'Gap Analyzer Running...'}
              </h3>
              <p className="text-xs text-slate-400">
                {allDone
                  ? `Found ${totalGapsFound} gaps across ${total} digests`
                  : `Analyzing ${completed} of ${total} digests`}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition" title={allDone ? 'Close' : 'Run in background'}>
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-3 bg-slate-50/50">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-slate-500">Progress</span>
            <span className="text-[11px] font-bold tabular-nums text-slate-700">{pct}% — {completed}/{total}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${allDone ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* Digest List */}
        <div className="max-h-[400px] overflow-y-auto px-2 py-2">
          {progress?.items?.map((item: GapBatchItem, i: number) => (
            <div
              key={item.digest_id}
              className={`rounded-lg px-4 py-3 mb-1 transition-all ${
                item.status === 'done' ? 'bg-white' : 'bg-amber-50/30'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {item.status === 'done' ? (
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100">
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                    </div>
                  ) : (
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-100">
                      <Loader2 className="h-3.5 w-3.5 text-amber-500 animate-spin" />
                    </div>
                  )}
                </div>
                <span className="w-6 text-right text-[11px] font-bold tabular-nums text-slate-400">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-medium text-slate-700">{item.topic || 'Untitled'}</p>
                  <p className="truncate text-[11px] text-slate-400">{item.url}</p>
                </div>
                <div className="flex flex-shrink-0 items-center gap-2">
                  {item.status === 'done' ? (
                    <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${
                      item.gaps_found > 0 ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-400'
                    }`}>
                      {item.gaps_found > 0 ? `${item.gaps_found} gaps` : 'No gaps'}
                    </span>
                  ) : (
                    <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-500">
                      <Clock className="mr-1 inline h-3 w-3" />Analyzing
                    </span>
                  )}
                </div>
              </div>
              {/* Show found gaps inline */}
              {item.status === 'done' && item.gaps.length > 0 && (
                <div className="mt-2 ml-16 space-y-1">
                  {item.gaps.map((g) => (
                    <div key={g.gap_id} className="flex items-center gap-2 rounded bg-slate-50 px-2 py-1">
                      <SeverityBadge severity={g.severity} />
                      <span className="truncate text-[11px] text-slate-600">{g.gap_statement}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {!progress?.items && digestIds.length > 0 && (
            <div className="space-y-2 px-4 py-2">
              {Array.from({ length: Math.min(digestIds.length, 5) }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 rounded-lg bg-slate-50 px-4 py-3">
                  <div className="h-7 w-7 rounded-full bg-slate-200 animate-pulse" />
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3 w-3/4 rounded bg-slate-200 animate-pulse" />
                    <div className="h-2 w-1/2 rounded bg-slate-100 animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-100 px-6 py-3 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-4 text-[11px] text-slate-400">
            <span><span className="font-bold text-amber-600">{totalGapsFound}</span> total gaps found</span>
            <span><span className="font-bold text-slate-500">{progress?.items?.filter((i: GapBatchItem) => i.status === 'done' && i.gaps_found === 0).length ?? 0}</span> no gaps</span>
            <span><span className="font-bold text-amber-500">{total - completed}</span> remaining</span>
          </div>
          {allDone ? (
            <button onClick={onClose} className="rounded-lg bg-amber-600 px-4 py-1.5 text-[12px] font-semibold text-white shadow-sm hover:bg-amber-700 transition active:scale-[0.98]">
              Close & Review
            </button>
          ) : (
            <button onClick={onClose} className="rounded-lg border border-slate-300 bg-white px-4 py-1.5 text-[12px] font-semibold text-slate-600 shadow-sm hover:bg-slate-50 transition active:scale-[0.98]">
              Run in Background
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function GapReview() {
  const [filters, setFilters] = useState<{ decision_status?: string; severity?: string }>({ decision_status: 'pending_review' })
  const [selected, setSelected] = useState<Gap | null>(null)
  const [comments, setComments] = useState('')
  const [feedbackWhat, setFeedbackWhat] = useState('')
  const [feedbackWhy, setFeedbackWhy] = useState('')
  const [feedbackWhen, setFeedbackWhen] = useState('')
  const [showProgress, setShowProgress] = useState(false)
  const [batchDigestIds, setBatchDigestIds] = useState<string[]>([])
  const { data, isLoading } = useGaps(filters)
  const review = useReviewGap()
  const submitFeedback = useSubmitGapFeedback()
  const runAll = useRunAllGapAnalysis()
  const { data: summary } = useGapSummary()

  const handleRunAgent = () => {
    runAll.mutate(undefined, {
      onSuccess: (result: any) => {
        const ids = (result?.batch_results ?? []).map((r: any) => r.digest_id)
        if (ids.length > 0) {
          setBatchDigestIds(ids)
          setShowProgress(true)
        }
      },
    })
  }

  const handleReview = (decision: string) => {
    if (!selected) return
    const feedback = [feedbackWhat, feedbackWhy, feedbackWhen].filter(Boolean).join(' | ') || undefined
    review.mutate({ gapId: selected.gap_id, decision, comments, feedback }, {
      onSuccess: () => {
        if (feedbackWhat || feedbackWhy || feedbackWhen) {
          submitFeedback.mutate({
            gapId: selected!.gap_id,
            feedback_what: feedbackWhat || undefined,
            feedback_why: feedbackWhy || undefined,
            feedback_when: feedbackWhen || undefined,
          })
        }
        setSelected(null); setComments(''); setFeedbackWhat(''); setFeedbackWhy(''); setFeedbackWhen('')
      },
    })
  }

  const isRunning = runAll.isPending

  return (
    <div className="space-y-5">
      <GapProgressModal
        isOpen={showProgress}
        onClose={() => setShowProgress(false)}
        digestIds={batchDigestIds}
      />

      {/* Agent Runner Panel */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-amber-50/50 to-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100">
              <Zap className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Gap Analyzer Agent</h3>
              <p className="text-xs text-slate-400">Analyze curriculum-relevant digests for gaps</p>
            </div>
          </div>
          <button
            onClick={handleRunAgent}
            disabled={isRunning}
            className={`inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-[13px] font-semibold shadow-sm transition active:scale-[0.98] ${
              isRunning
                ? 'bg-amber-400 text-white cursor-not-allowed'
                : 'bg-amber-600 text-white hover:bg-amber-700'
            }`}
          >
            {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isRunning ? 'Starting...' : 'Run Gap Analyzer'}
          </button>
        </div>

        <div className="grid grid-cols-5 divide-x divide-slate-100">
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Gaps</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-slate-900">{summary?.total ?? 0}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Critical</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-red-600">{summary?.by_severity?.critical ?? 0}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">High</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-orange-500">{summary?.by_severity?.high ?? 0}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Medium</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-amber-500">{summary?.by_severity?.medium ?? 0}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Low</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-emerald-600">{summary?.by_severity?.low ?? 0}</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-6" style={{ height: 'calc(100vh - 340px)' }}>
        {/* Queue */}
        <div className="w-[380px] flex-shrink-0 space-y-3">
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Status</p>
            <div className="flex items-center gap-1.5 rounded-lg bg-white p-1 border border-slate-200 shadow-card">
              {['pending_review', 'approved', 'rejected'].map((s) => (
                <button key={s} onClick={() => setFilters({ ...filters, decision_status: s })}
                  className={`flex-1 rounded-md px-2.5 py-1.5 text-[12px] font-semibold transition-all ${
                    filters.decision_status === s ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
                  }`}>
                  {s.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Severity</p>
            <div className="flex gap-1.5">
              {['critical', 'high', 'medium', 'low'].map((s) => (
                <button key={s} onClick={() => setFilters({ ...filters, severity: filters.severity === s ? undefined : s })}
                  className={`rounded-lg px-3 py-1.5 text-[11px] font-semibold uppercase transition-all ${
                    filters.severity === s ? 'bg-indigo-600 text-white shadow-sm' : 'bg-white border border-slate-200 text-slate-500 hover:border-slate-300'
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-400">{data?.total ?? 0} gaps found</p>
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
            </div>
          )}
          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 440px)' }}>
            {data?.items?.map((g) => (
              <div key={g.gap_id} onClick={() => setSelected(g)}
                className={`cursor-pointer rounded-xl border p-4 transition-all duration-150 ${
                  selected?.gap_id === g.gap_id ? 'border-indigo-500 bg-indigo-50/50 shadow-md' : 'border-slate-200 bg-white shadow-card hover:shadow-card-hover hover:border-slate-300'
                }`}>
                <div className="flex items-center justify-between gap-2">
                  <SeverityBadge severity={g.severity} />
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">{g.gap_type.replace(/_/g, ' ')}</span>
                </div>
                <p className="mt-2 text-[13px] font-medium leading-snug text-slate-800">{g.gap_statement}</p>
                {g.when_to_act && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
                    <Calendar className="h-3 w-3" /> Act by {g.when_to_act}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Detail */}
        <div className="min-w-0 flex-1">
          {selected ? (
            <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-y-auto h-full">
              <div className="border-b border-slate-100 px-6 py-5">
                <div className="flex items-start justify-between gap-4">
                  <h3 className="text-lg font-bold tracking-tight text-slate-900">{selected.gap_statement}</h3>
                  <div className="flex flex-shrink-0 items-center gap-2">
                    <SeverityBadge severity={selected.severity} />
                    <StatusBadge status={selected.decision_status} />
                  </div>
                </div>
              </div>
              <div className="px-6 py-5 space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="rounded-lg bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Type</p>
                    <p className="mt-1 text-sm font-semibold capitalize text-slate-700">{selected.gap_type.replace(/_/g, ' ')}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Signal</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">{selected.market_signal}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Act By</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">{selected.when_to_act ?? 'N/A'}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">What To Act</h4>
                    <p className="mt-2 text-[14px] leading-relaxed text-slate-600">{selected.what_to_act}</p>
                  </div>
                  <div>
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Why To Act</h4>
                    <p className="mt-2 text-[14px] leading-relaxed text-slate-600">{selected.why_to_act}</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Curriculum Evidence</h4>
                  <blockquote className="mt-2 rounded-r-lg border-l-[3px] border-amber-300 bg-amber-50/50 py-3 pl-4 pr-3 text-[13px] leading-relaxed text-slate-600">
                    {selected.curriculum_evidence}
                  </blockquote>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Layers className="h-4 w-4 text-slate-400" />
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Impact Analysis</h4>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Courses', items: selected.impacted_courses },
                      { label: 'Sessions', items: selected.impacted_sessions },
                      { label: 'Projects', items: selected.impacted_projects },
                      { label: 'Assessments', items: selected.impacted_assessments },
                      { label: 'Quizzes', items: selected.impacted_quizzes },
                      { label: 'Tools', items: selected.impacted_tools },
                    ].map(({ label, items }) => (
                      <div key={label} className="rounded-lg border border-slate-200 bg-slate-50/50 p-3">
                        <div className="flex items-center justify-between">
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
                          <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-600">{items?.length ?? 0}</span>
                        </div>
                        <ul className="mt-2 space-y-1">
                          {items?.map((item, i) => <li key={i} className="text-xs text-slate-600">{item}</li>)}
                          {(!items || items.length === 0) && <li className="text-xs text-slate-300">None</li>}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="border-t border-slate-100 pt-5">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-3">Review Decision</h4>
                  <textarea value={comments} onChange={(e) => setComments(e.target.value)} placeholder="Review comments..."
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition" rows={2} />
                  <div className="mt-3 grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[10px] font-semibold uppercase tracking-wide text-blue-500 mb-1">What to Act</label>
                      <textarea value={feedbackWhat} onChange={(e) => setFeedbackWhat(e.target.value)} placeholder="What action should be taken?"
                        className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition resize-none" rows={2} />
                    </div>
                    <div>
                      <label className="block text-[10px] font-semibold uppercase tracking-wide text-amber-500 mb-1">Why to Act</label>
                      <textarea value={feedbackWhy} onChange={(e) => setFeedbackWhy(e.target.value)} placeholder="Why is this important?"
                        className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition resize-none" rows={2} />
                    </div>
                    <div>
                      <label className="block text-[10px] font-semibold uppercase tracking-wide text-emerald-500 mb-1">When to Act</label>
                      <input value={feedbackWhen} onChange={(e) => setFeedbackWhen(e.target.value)} placeholder="Timeline — e.g., Next sprint"
                        className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition" />
                    </div>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={() => handleReview('approved')} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-[13px] font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:scale-[0.98]">
                      <CheckCircle className="h-4 w-4" /> Approve
                    </button>
                    <button onClick={() => handleReview('rejected')} className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-[13px] font-semibold text-white shadow-sm transition hover:bg-red-700 active:scale-[0.98]">
                      <XCircle className="h-4 w-4" /> Reject
                    </button>
                    <button onClick={() => handleReview('needs_review')} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-[13px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 active:scale-[0.98]">
                      <Eye className="h-4 w-4" /> Needs Review
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/50">
              <AlertTriangle className="h-10 w-10 text-slate-300" />
              <p className="mt-3 text-sm font-medium text-slate-400">Select a gap to review</p>
              <p className="mt-1 text-xs text-slate-300">Click on any item in the queue</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

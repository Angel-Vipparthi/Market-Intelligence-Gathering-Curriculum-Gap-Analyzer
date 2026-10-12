import { useState, useEffect } from 'react'
import { useDigests, useReviewDigest, useProcessAllDigests, useDigestStatus, useBatchProgress } from '@/hooks/useDigests'
import type { BatchItem } from '@/hooks/useDigests'
import StatusBadge from '@/components/common/StatusBadge'
import type { Digest } from '@/lib/types'
import { CheckCircle, XCircle, Eye, ExternalLink, Play, Loader2, FileText, Zap, X, Check, Clock } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

function ProgressModal({
  isOpen,
  onClose,
  urlIds,
}: {
  isOpen: boolean
  onClose: () => void
  urlIds: string[]
}) {
  const { data: progress } = useBatchProgress(urlIds, isOpen)
  const qc = useQueryClient()
  const completed = progress?.completed ?? 0
  const total = progress?.total ?? urlIds.length
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  const allDone = completed === total && total > 0

  useEffect(() => {
    if (allDone) {
      qc.invalidateQueries({ queryKey: ['digests'] })
      qc.invalidateQueries({ queryKey: ['digest-status'] })
    }
  }, [allDone, qc])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl mx-4 rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-indigo-50 to-white">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${allDone ? 'bg-emerald-100' : 'bg-indigo-100'}`}>
              {allDone ? <Check className="h-5 w-5 text-emerald-600" /> : <Loader2 className="h-5 w-5 text-indigo-600 animate-spin" />}
            </div>
            <div>
              <h3 className="text-[15px] font-bold text-slate-900">
                {allDone ? 'Digest Agent Complete' : 'Digest Agent Running...'}
              </h3>
              <p className="text-xs text-slate-400">
                {allDone
                  ? `All ${total} URLs processed successfully`
                  : `Processing ${completed} of ${total} URLs`}
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
              className={`h-full rounded-full transition-all duration-700 ease-out ${allDone ? 'bg-emerald-500' : 'bg-indigo-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* URL List */}
        <div className="max-h-[400px] overflow-y-auto px-2 py-2">
          {progress?.items?.map((item: BatchItem, i: number) => (
            <div
              key={item.url_id}
              className={`flex items-center gap-3 rounded-lg px-4 py-2.5 transition-all ${
                item.status === 'done' ? 'bg-white' : 'bg-indigo-50/30'
              }`}
            >
              {/* Status Icon */}
              <div className="flex-shrink-0">
                {item.status === 'done' ? (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100">
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                  </div>
                ) : (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100">
                    <Loader2 className="h-3.5 w-3.5 text-indigo-500 animate-spin" />
                  </div>
                )}
              </div>

              {/* Number */}
              <span className="w-6 text-right text-[11px] font-bold tabular-nums text-slate-400">{i + 1}</span>

              {/* Content */}
              <div className="min-w-0 flex-1">
                {item.status === 'done' && item.topic ? (
                  <p className="truncate text-[13px] font-medium text-slate-700">{item.topic}</p>
                ) : (
                  <p className="truncate text-[13px] text-slate-500">{item.url}</p>
                )}
                {item.status === 'done' && (
                  <p className="truncate text-[11px] text-slate-400">{item.url}</p>
                )}
              </div>

              {/* Right badges */}
              <div className="flex flex-shrink-0 items-center gap-2">
                {item.status === 'done' ? (
                  <>
                    <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${
                      item.curriculum_relevant === 'Yes'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-slate-100 text-slate-400'
                    }`}>
                      {item.curriculum_relevant === 'Yes' ? 'Relevant' : 'Not Relevant'}
                    </span>
                    {item.market_signal && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                        {item.market_signal}
                      </span>
                    )}
                  </>
                ) : (
                  <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-500">
                    <Clock className="mr-1 inline h-3 w-3" />Processing
                  </span>
                )}
              </div>
            </div>
          ))}

          {/* Skeleton while loading initial data */}
          {!progress?.items && urlIds.length > 0 && (
            <div className="space-y-2 px-4 py-2">
              {Array.from({ length: Math.min(urlIds.length, 5) }).map((_, i) => (
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
            <span><span className="font-bold text-emerald-600">{progress?.items?.filter((i: BatchItem) => i.status === 'done' && i.curriculum_relevant === 'Yes').length ?? 0}</span> relevant</span>
            <span><span className="font-bold text-slate-500">{progress?.items?.filter((i: BatchItem) => i.status === 'done' && i.curriculum_relevant !== 'Yes').length ?? 0}</span> not relevant</span>
            <span><span className="font-bold text-indigo-500">{(progress?.total ?? 0) - (progress?.completed ?? 0)}</span> remaining</span>
          </div>
          {allDone ? (
            <button onClick={onClose} className="rounded-lg bg-indigo-600 px-4 py-1.5 text-[12px] font-semibold text-white shadow-sm hover:bg-indigo-700 transition active:scale-[0.98]">
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

export default function DigestReview() {
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<Digest | null>(null)
  const [comments, setComments] = useState('')
  const [showProgress, setShowProgress] = useState(false)
  const [batchUrlIds, setBatchUrlIds] = useState<string[]>([])
  const { data, isLoading } = useDigests(filter)
  const review = useReviewDigest()
  const processAll = useProcessAllDigests()
  const { data: statusData } = useDigestStatus()

  const handleRunAgent = () => {
    processAll.mutate(undefined, {
      onSuccess: (result: any) => {
        const ids = (result?.batch_results ?? []).map((r: any) => r.url_id)
        if (ids.length > 0) {
          setBatchUrlIds(ids)
          setShowProgress(true)
        }
      },
    })
  }

  const handleReview = (decision: string) => {
    if (!selected) return
    review.mutate({ digestId: selected.digest_id, decision, comments }, {
      onSuccess: () => { setSelected(null); setComments('') },
    })
  }

  const filters = [
    { value: '', label: 'All' },
    { value: 'pending_review', label: 'Pending' },
    { value: 'approved', label: 'Approved' },
    { value: 'rejected', label: 'Rejected' },
  ]

  const isRunning = processAll.isPending

  return (
    <div className="space-y-5">
      <ProgressModal
        isOpen={showProgress}
        onClose={() => setShowProgress(false)}
        urlIds={batchUrlIds}
      />

      {/* Agent Runner Panel */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-indigo-50/50 to-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100">
              <Zap className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Digest Agent</h3>
              <p className="text-xs text-slate-400">Process URLs through market intelligence pipeline</p>
            </div>
          </div>
          <button
            onClick={handleRunAgent}
            disabled={isRunning}
            className={`inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-[13px] font-semibold shadow-sm transition active:scale-[0.98] ${
              isRunning
                ? 'bg-indigo-400 text-white cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {isRunning ? 'Starting...' : 'Run Digest Agent'}
          </button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-5 divide-x divide-slate-100">
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total URLs</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-slate-900">{statusData?.total_urls ?? '—'}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Digested</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-indigo-600">{statusData?.total_digests ?? '—'}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Relevant</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-emerald-600">{statusData?.curriculum_relevant ?? '—'}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Pending Review</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-amber-600">{statusData?.by_status?.pending_review ?? 0}</p>
          </div>
          <div className="px-5 py-3 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Approved</p>
            <p className="mt-1 text-xl font-bold tabular-nums text-emerald-600">{statusData?.by_status?.approved ?? 0}</p>
          </div>
        </div>

        {/* Progress Bar */}
        {statusData && statusData.total_urls > 0 && (
          <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-500">Processing Progress</span>
              <span className="text-[11px] font-bold tabular-nums text-slate-600">
                {statusData.total_digests}/{statusData.total_urls} URLs
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-700"
                style={{ width: `${Math.round((statusData.total_digests / statusData.total_urls) * 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex gap-6" style={{ height: 'calc(100vh - 340px)' }}>
        {/* Queue Panel */}
        <div className="w-[380px] flex-shrink-0 space-y-3">
          <div className="flex items-center gap-1.5 rounded-lg bg-white p-1 border border-slate-200 shadow-card">
            {filters.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={`flex-1 rounded-md px-3 py-1.5 text-[12px] font-semibold transition-all ${
                  filter === f.value
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <p className="text-xs text-slate-400">{data?.items?.length ?? 0} digests</p>

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
            </div>
          )}

          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 400px)' }}>
            {data?.items?.map((d) => (
              <div
                key={d.digest_id}
                onClick={() => setSelected(d)}
                className={`cursor-pointer rounded-xl border p-4 transition-all duration-150 ${
                  selected?.digest_id === d.digest_id
                    ? 'border-indigo-500 bg-indigo-50/50 shadow-md'
                    : 'border-slate-200 bg-white shadow-card hover:shadow-card-hover hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[13px] font-semibold leading-tight text-slate-800">
                    {d.topic || d.source_title || 'Untitled'}
                  </p>
                  <span className={`flex-shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                    d.curriculum_relevant === 'Yes'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-slate-100 text-slate-400'
                  }`}>
                    {d.curriculum_relevant === 'Yes' ? 'Relevant' : 'N/A'}
                  </span>
                </div>
                <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-slate-500">{d.summary}</p>
                <div className="mt-3 flex items-center gap-2">
                  <StatusBadge status={d.status} />
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                    {d.market_signal}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="min-w-0 flex-1">
          {selected ? (
            <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-y-auto h-full">
              <div className="border-b border-slate-100 px-6 py-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold tracking-tight text-slate-900">{selected.topic || 'Untitled'}</h3>
                    <a href={selected.url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700 transition">
                      {selected.url} <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <StatusBadge status={selected.status} />
                </div>
              </div>

              <div className="px-6 py-5 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Signal</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">{selected.market_signal}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Curriculum Relevant</p>
                    <p className={`mt-1 text-sm font-bold ${selected.curriculum_relevant === 'Yes' ? 'text-emerald-600' : 'text-red-500'}`}>
                      {selected.curriculum_relevant || 'N/A'}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Summary</h4>
                  <p className="mt-2 text-[14px] leading-relaxed text-slate-600">{selected.summary}</p>
                </div>

                <div>
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Evidence</h4>
                  <blockquote className="mt-2 rounded-r-lg border-l-[3px] border-indigo-300 bg-indigo-50/50 py-3 pl-4 pr-3 text-[13px] italic leading-relaxed text-slate-600">
                    {selected.evidence_snippet}
                  </blockquote>
                </div>

                {selected.tools_versions?.length > 0 && (
                  <div>
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Tools & Versions</h4>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selected.tools_versions.map((tv, i) => (
                        <span key={i} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
                          {tv.tool} <span className="text-indigo-600">{tv.version}</span> <span className="text-slate-400">({tv.change_type})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t border-slate-100 pt-5">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-3">Review Decision</h4>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Add review comments (optional)..."
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
                    rows={2}
                  />
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
              <FileText className="h-10 w-10 text-slate-300" />
              <p className="mt-3 text-sm font-medium text-slate-400">Select a digest to review</p>
              <p className="mt-1 text-xs text-slate-300">Click on any item in the queue</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

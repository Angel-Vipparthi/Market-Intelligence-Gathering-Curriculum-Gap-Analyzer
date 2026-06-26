import { useState } from 'react'
import { useGapReport, useSubmitGapFeedback } from '@/hooks/useGaps'
import SeverityBadge from '@/components/common/SeverityBadge'
import {
  Calendar, BookOpen, Layers, Wrench, FileText, AlertTriangle, Download,
  MessageSquarePlus, Check, Pencil, Save, Loader2,
} from 'lucide-react'

function downloadCSV(report: any) {
  const headers = [
    'Severity', 'Gap Type', 'Gap Statement', 'What To Act', 'Why To Act',
    'When To Act', 'Curriculum Evidence', 'Market Signal',
    'Impacted Courses', 'Impacted Sessions', 'Impacted Projects',
    'Impacted Assessments', 'Impacted Quizzes', 'Impacted Tools',
    'Feedback What', 'Feedback Why', 'Feedback When',
  ]

  const escape = (val: any) => {
    if (val == null) return ''
    const str = Array.isArray(val) ? val.join('; ') : String(val)
    return str.includes(',') || str.includes('"') || str.includes('\n')
      ? `"${str.replace(/"/g, '""')}"`
      : str
  }

  const rows = report.gaps.map((g: any) => [
    g.severity, g.gap_type, g.gap_statement, g.what_to_act, g.why_to_act,
    g.when_to_act, g.curriculum_evidence, g.market_signal,
    g.impacted_courses, g.impacted_sessions, g.impacted_projects,
    g.impacted_assessments, g.impacted_quizzes, g.impacted_tools,
    g.feedback_what, g.feedback_why, g.feedback_when,
  ].map(escape).join(','))

  const csv = [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `gap-report-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function GapFeedbackRow({ gap }: { gap: any }) {
  const [editing, setEditing] = useState(false)
  const [feedbackWhat, setFeedbackWhat] = useState(gap.feedback_what || '')
  const [feedbackWhy, setFeedbackWhy] = useState(gap.feedback_why || '')
  const [feedbackWhen, setFeedbackWhen] = useState(gap.feedback_when || '')
  const submit = useSubmitGapFeedback()

  const handleSave = () => {
    submit.mutate({
      gapId: gap.gap_id,
      feedback_what: feedbackWhat || undefined,
      feedback_why: feedbackWhy || undefined,
      feedback_when: feedbackWhen || undefined,
    }, {
      onSuccess: () => setEditing(false),
    })
  }

  const hasFeedback = gap.has_feedback || gap.feedback_what || gap.feedback_why || gap.feedback_when

  return (
    <div className="mt-3 rounded-lg border border-indigo-100 bg-gradient-to-r from-indigo-50/40 to-white p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MessageSquarePlus className="h-4 w-4 text-indigo-500" />
          <span className="text-[12px] font-bold text-indigo-800">Your Feedback</span>
          {hasFeedback && !editing && (
            <span className="inline-flex items-center gap-0.5 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-200">
              <Check className="h-3 w-3" /> Saved
            </span>
          )}
        </div>
        {!editing ? (
          <button onClick={() => setEditing(true)}
            className="inline-flex items-center gap-1 rounded-lg border border-indigo-200 px-2.5 py-1 text-[11px] font-semibold text-indigo-600 hover:bg-indigo-100 transition">
            <Pencil className="h-3 w-3" /> {hasFeedback ? 'Edit' : 'Add Feedback'}
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button onClick={handleSave} disabled={submit.isPending}
              className="inline-flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1 text-[11px] font-semibold text-white hover:bg-indigo-700 transition disabled:opacity-50">
              {submit.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
              {submit.isPending ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => setEditing(false)}
              className="rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-500 hover:bg-slate-50 transition">
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3">
        {/* What to Act */}
        <div>
          <label className="block text-[10px] font-semibold uppercase tracking-wide text-blue-500 mb-1">
            What to Act
          </label>
          {editing ? (
            <textarea value={feedbackWhat} onChange={e => setFeedbackWhat(e.target.value)}
              placeholder={gap.what_to_act ? `AI: ${gap.what_to_act.slice(0, 80)}...` : 'What action should be taken?'}
              rows={3}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-none" />
          ) : (
            <p className="text-[12px] text-slate-600 leading-relaxed min-h-[40px]">
              {feedbackWhat || gap.feedback_what || <span className="text-slate-300 italic">No feedback yet</span>}
            </p>
          )}
        </div>

        {/* Why to Act */}
        <div>
          <label className="block text-[10px] font-semibold uppercase tracking-wide text-amber-500 mb-1">
            Why to Act
          </label>
          {editing ? (
            <textarea value={feedbackWhy} onChange={e => setFeedbackWhy(e.target.value)}
              placeholder={gap.why_to_act ? `AI: ${gap.why_to_act.slice(0, 80)}...` : 'Why is this important?'}
              rows={3}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-none" />
          ) : (
            <p className="text-[12px] text-slate-600 leading-relaxed min-h-[40px]">
              {feedbackWhy || gap.feedback_why || <span className="text-slate-300 italic">No feedback yet</span>}
            </p>
          )}
        </div>

        {/* When to Act */}
        <div>
          <label className="block text-[10px] font-semibold uppercase tracking-wide text-emerald-500 mb-1">
            When to Act
          </label>
          {editing ? (
            <input value={feedbackWhen} onChange={e => setFeedbackWhen(e.target.value)}
              placeholder={gap.when_to_act ? `AI: ${gap.when_to_act}` : 'Timeline — e.g., Next sprint, 2 weeks'}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-[12px] text-slate-700 placeholder:text-slate-300 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100" />
          ) : (
            <p className="text-[12px] text-slate-600 leading-relaxed min-h-[40px]">
              {feedbackWhen || gap.feedback_when || <span className="text-slate-300 italic">No feedback yet</span>}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function GapReport() {
  const { data: report, isLoading } = useGapReport()

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
    </div>
  )

  if (!report || report.total_approved === 0) return (
    <div className="flex flex-col items-center justify-center py-20 rounded-xl border border-dashed border-slate-300 bg-white/50">
      <AlertTriangle className="h-12 w-12 text-slate-300" />
      <p className="mt-4 text-base font-medium text-slate-400">No approved gaps yet</p>
      <p className="mt-1 text-sm text-slate-300">Approve gaps in the Gap Analysis page to see them here</p>
    </div>
  )

  const severityOrder = ['critical', 'high', 'medium', 'low']
  const feedbackCount = report.gaps.filter((g: any) => g.has_feedback).length

  return (
    <div className="space-y-8">
      {/* Summary Header */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-gradient-to-r from-indigo-50/50 to-white">
          <div>
            <h2 className="text-lg font-bold tracking-tight text-slate-900">Curriculum Gap Report</h2>
            <p className="mt-1 text-sm text-slate-400">Approved gaps — add your feedback to improve future analysis</p>
          </div>
          <div className="flex items-center gap-3">
            {feedbackCount > 0 && (
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-[12px] font-semibold text-emerald-700 border border-emerald-200">
                <Check className="h-3.5 w-3.5" />
                {feedbackCount}/{report.total_approved} reviewed
              </span>
            )}
            <button
              onClick={() => downloadCSV(report)}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-[13px] font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 active:scale-[0.98]"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        <div className="grid grid-cols-4 divide-x divide-slate-100">
          <div className="px-6 py-4 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Gaps</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-slate-900">{report.total_approved}</p>
          </div>
          <div className="px-6 py-4 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Courses Affected</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-indigo-600">{report.impact_summary.total_courses_affected}</p>
          </div>
          <div className="px-6 py-4 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Sessions Affected</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-amber-600">{report.impact_summary.total_sessions_affected}</p>
          </div>
          <div className="px-6 py-4 text-center">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Tools Affected</p>
            <p className="mt-1 text-2xl font-bold tabular-nums text-red-600">{report.impact_summary.total_tools_affected}</p>
          </div>
        </div>

        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center gap-3">
          <span className="text-[11px] font-semibold text-slate-400">By Severity:</span>
          <div className="flex gap-2">
            {severityOrder.map((s) => (
              <span key={s} className="text-[11px] text-slate-500">
                <span className="font-bold">{report.by_severity[s] ?? 0}</span> {s}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Impact Summary */}
      <div className="grid grid-cols-3 gap-5">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-indigo-500" />
            <h3 className="text-[13px] font-semibold text-slate-900">Affected Courses</h3>
          </div>
          <div className="space-y-1.5">
            {report.impact_summary.courses.map((c: string) => (
              <div key={c} className="rounded-lg bg-indigo-50 px-3 py-1.5 text-[12px] font-medium text-indigo-700">{c}</div>
            ))}
            {report.impact_summary.courses.length === 0 && <p className="text-xs text-slate-300">None</p>}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="h-4 w-4 text-amber-500" />
            <h3 className="text-[13px] font-semibold text-slate-900">Affected Sessions</h3>
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {report.impact_summary.sessions.map((s: string) => (
              <div key={s} className="rounded-lg bg-amber-50 px-3 py-1.5 text-[11px] font-medium text-amber-700">{s}</div>
            ))}
            {report.impact_summary.sessions.length === 0 && <p className="text-xs text-slate-300">None</p>}
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="flex items-center gap-2 mb-3">
            <Wrench className="h-4 w-4 text-red-500" />
            <h3 className="text-[13px] font-semibold text-slate-900">Affected Tools</h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {report.impact_summary.tools.map((t: string) => (
              <span key={t} className="rounded-lg border border-red-200 bg-red-50 px-2.5 py-1 text-[11px] font-medium text-red-700">{t}</span>
            ))}
            {report.impact_summary.tools.length === 0 && <p className="text-xs text-slate-300">None</p>}
          </div>
        </div>
      </div>

      {/* Action Timeline */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-900">Action Timeline</h3>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">Gaps ordered by action deadline</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="whitespace-nowrap px-6 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Severity</th>
                <th className="whitespace-nowrap px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Act By</th>
                <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Gap</th>
                <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">What To Do</th>
                <th className="whitespace-nowrap px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Tools</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {report.action_timeline.map((item: any) => (
                <tr key={item.gap_id} className="hover:bg-slate-50/50 transition">
                  <td className="whitespace-nowrap px-6 py-3">
                    <SeverityBadge severity={item.severity} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-[12px] font-medium text-slate-500">
                    {item.when_to_act || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-[13px] font-medium text-slate-800 leading-snug">{item.gap_statement}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-[12px] text-slate-500 leading-snug">{item.what_to_act || '—'}</p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {item.impacted_tools?.map((t: string) => (
                        <span key={t} className="whitespace-nowrap rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">{t}</span>
                      ))}
                      {(!item.impacted_tools || item.impacted_tools.length === 0) && (
                        <span className="text-[11px] text-slate-300">—</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Gap Details + Feedback */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-900">Gap Findings & Feedback</h3>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">Review each gap and add your feedback on what/why/when to act</p>
        </div>
        <div className="divide-y divide-slate-100">
          {report.gaps.map((gap: any) => (
            <div key={gap.gap_id} className="px-6 py-5">
              {/* Gap header */}
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <SeverityBadge severity={gap.severity} />
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                  {gap.gap_type?.replace(/_/g, ' ')}
                </span>
                {gap.when_to_act && (
                  <span className="rounded-lg bg-slate-50 px-2.5 py-0.5 text-[11px] font-medium text-slate-400">
                    Act by {gap.when_to_act}
                  </span>
                )}
              </div>

              {/* Gap statement */}
              <h4 className="text-[15px] font-semibold text-slate-900 mb-3">{gap.gap_statement}</h4>

              {/* AI's What / Why / When */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-blue-500">AI: What To Act</span>
                  <p className="text-[12px] leading-relaxed text-slate-600 mt-1">{gap.what_to_act || '—'}</p>
                </div>
                <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-amber-500">AI: Why To Act</span>
                  <p className="text-[12px] leading-relaxed text-slate-600 mt-1">{gap.why_to_act || '—'}</p>
                </div>
                <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-500">AI: When To Act</span>
                  <p className="text-[12px] leading-relaxed text-slate-600 mt-1">
                    {gap.when_to_act || '—'}
                    {gap.when_to_act_rationale && (
                      <span className="text-slate-400 text-[11px] block mt-0.5">{gap.when_to_act_rationale}</span>
                    )}
                  </p>
                </div>
              </div>

              {/* Evidence */}
              {gap.curriculum_evidence && (
                <div className="mb-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Evidence</p>
                  <p className="rounded-r-lg border-l-[3px] border-amber-300 bg-amber-50/50 py-2 pl-3 pr-2 text-[12px] leading-relaxed text-slate-600">
                    {gap.curriculum_evidence}
                  </p>
                </div>
              )}

              {/* Impact tags */}
              <div className="flex flex-wrap gap-1.5 mb-1">
                {gap.impacted_courses?.map((c: string) => (
                  <span key={c} className="whitespace-nowrap rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-indigo-600">{c}</span>
                ))}
                {gap.impacted_tools?.map((t: string) => (
                  <span key={t} className="whitespace-nowrap rounded bg-red-50 px-2 py-0.5 text-[10px] font-medium text-red-600">{t}</span>
                ))}
                {gap.impacted_sessions?.slice(0, 5).map((s: string) => (
                  <span key={s} className="whitespace-nowrap rounded bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-600">{s}</span>
                ))}
                {(gap.impacted_sessions?.length ?? 0) > 5 && (
                  <span className="whitespace-nowrap rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                    +{gap.impacted_sessions.length - 5} more
                  </span>
                )}
              </div>

              {/* Feedback section — always visible */}
              <GapFeedbackRow gap={gap} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

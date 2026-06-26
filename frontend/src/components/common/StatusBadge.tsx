const styles: Record<string, string> = {
  pending: 'bg-slate-100 text-slate-600',
  pending_review: 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/10',
  approved: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10',
  rejected: 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10',
  needs_review: 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10',
  processing: 'bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-600/10',
  active: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10',
  inactive: 'bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-500/10',
}

export default function StatusBadge({ status }: { status: string }) {
  const cls = styles[status] ?? 'bg-slate-100 text-slate-600'
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${cls}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

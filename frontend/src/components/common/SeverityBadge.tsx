const styles = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-amber-400 text-amber-950',
  low: 'bg-emerald-100 text-emerald-700',
}

const dots = {
  critical: 'bg-white/80',
  high: 'bg-white/80',
  medium: 'bg-amber-700',
  low: 'bg-emerald-500',
}

export default function SeverityBadge({ severity }: { severity: string }) {
  const cls = styles[severity as keyof typeof styles] ?? 'bg-slate-100 text-slate-600'
  const dot = dots[severity as keyof typeof dots] ?? 'bg-slate-400'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {severity}
    </span>
  )
}

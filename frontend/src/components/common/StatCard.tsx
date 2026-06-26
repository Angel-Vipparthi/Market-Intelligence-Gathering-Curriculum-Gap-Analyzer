interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  color?: 'blue' | 'red' | 'green' | 'yellow' | 'indigo' | 'purple'
  icon?: React.ReactNode
}

const colorMap = {
  blue: 'bg-blue-50 text-blue-700',
  red: 'bg-red-50 text-red-700',
  green: 'bg-emerald-50 text-emerald-700',
  yellow: 'bg-amber-50 text-amber-700',
  indigo: 'bg-indigo-50 text-indigo-700',
  purple: 'bg-purple-50 text-purple-700',
}

const valueColorMap = {
  blue: 'text-blue-700',
  red: 'text-red-600',
  green: 'text-emerald-600',
  yellow: 'text-amber-600',
  indigo: 'text-indigo-600',
  purple: 'text-purple-600',
}

export default function StatCard({ title, value, subtitle, color = 'indigo', icon }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-medium text-slate-500">{title}</p>
        {icon && <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${colorMap[color]}`}>{icon}</div>}
      </div>
      <p className={`mt-2 text-2xl font-bold tracking-tight ${valueColorMap[color]}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  )
}

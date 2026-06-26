import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Wrench, Star, Activity } from 'lucide-react'

export default function Skills() {
  const { data, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: async () => {
      const { data } = await api.get('/skills')
      return data
    },
  })

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        {(data?.items ?? []).map((skill: Record<string, unknown>) => (
          <div key={skill.skill_id as string} className="rounded-xl border border-slate-200 bg-white p-5 shadow-card transition-shadow hover:shadow-card-hover">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-50">
                  <Wrench className="h-5 w-5 text-indigo-600" />
                </div>
                <div>
                  <h4 className="text-[15px] font-semibold text-slate-800">{skill.skill_name as string}</h4>
                  <p className="mt-0.5 text-sm text-slate-500">{skill.description as string}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-right">
                <div className="flex items-center gap-1.5">
                  <Star className="h-4 w-4 text-amber-400" />
                  <span className="text-sm font-bold tabular-nums text-slate-700">{((skill.evaluation_score as number) ?? 0).toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400">
                  <Activity className="h-3.5 w-3.5" />
                  <span className="text-xs tabular-nums">{skill.usage_count as number} uses</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {(!data?.items || data.items.length === 0) && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/50 py-16">
            <Wrench className="h-10 w-10 text-slate-300" />
            <p className="mt-3 text-sm font-medium text-slate-400">No skills configured yet</p>
            <p className="mt-1 text-xs text-slate-300">Skills will appear after the first agent run</p>
          </div>
        )}
      </div>
    </div>
  )
}

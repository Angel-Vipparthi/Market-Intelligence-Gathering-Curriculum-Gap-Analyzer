import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { URLEntry } from '@/lib/types'
import StatusBadge from '@/components/common/StatusBadge'
import { Plus, Globe, Filter } from 'lucide-react'

export default function URLManagement() {
  const [newUrl, setNewUrl] = useState('')
  const [category, setCategory] = useState('')
  const [newCourseName, setNewCourseName] = useState('')
  const [courseFilter, setCourseFilter] = useState('')
  const qc = useQueryClient()

  const { data: courseList } = useQuery({
    queryKey: ['url-courses'],
    queryFn: async () => {
      const { data } = await api.get('/urls/courses')
      return data.items as string[]
    },
  })

  const { data, isLoading } = useQuery({
    queryKey: ['urls', courseFilter],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (courseFilter) params.course_name = courseFilter
      const { data } = await api.get('/urls', { params })
      return data as { items: URLEntry[]; total: number }
    },
  })

  const addUrl = useMutation({
    mutationFn: async () => {
      await api.post('/urls', {
        url: newUrl,
        category: category || undefined,
        course_name: newCourseName || courseFilter || undefined,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['urls'] })
      qc.invalidateQueries({ queryKey: ['url-courses'] })
      setNewUrl('')
      setCategory('')
      setNewCourseName('')
    },
  })

  return (
    <div className="space-y-6">
      {/* Course filter */}
      <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-card">
        <Filter className="h-4 w-4 text-slate-400" />
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Course</span>
        <select value={courseFilter} onChange={e => setCourseFilter(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-medium text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100">
          <option value="">All Courses</option>
          {(courseList ?? []).map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        {courseFilter && (
          <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-[11px] font-semibold text-indigo-600">
            {data?.total ?? 0} URLs
          </span>
        )}
      </div>

      {/* Add URL */}
      <div className="flex items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
        <div className="flex-1">
          <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-400">URL</label>
          <input
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="https://example.com/docs"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
          />
        </div>
        <div className="w-40">
          <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-400">Course</label>
          <input
            value={newCourseName || courseFilter}
            onChange={(e) => setNewCourseName(e.target.value)}
            placeholder="e.g. React"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
          />
        </div>
        <div className="w-40">
          <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-slate-400">Category</label>
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="documentation"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
          />
        </div>
        <button
          onClick={() => addUrl.mutate()}
          disabled={!newUrl || addUrl.isPending}
          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-5 py-2.5 text-[13px] font-semibold text-white shadow-sm transition hover:bg-indigo-700 active:scale-[0.98] disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> Add URL
        </button>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400">Source</th>
              <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400">Course</th>
              <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400">Category</th>
              <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400">Credibility</th>
              <th className="px-5 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && (
              <tr><td colSpan={5} className="px-5 py-12 text-center">
                <div className="inline-flex h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
              </td></tr>
            )}
            {data?.items?.map((url) => (
              <tr key={url.id} className="transition hover:bg-slate-50/50">
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100">
                      <Globe className="h-3.5 w-3.5 text-slate-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-medium text-slate-700">{url.source_name || url.domain}</p>
                      <p className="truncate text-xs text-slate-400 max-w-xs">{url.url}</p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3.5">
                  {url.course_name ? (
                    <span className="rounded-md bg-violet-50 px-2 py-0.5 text-xs font-semibold text-violet-600">{url.course_name}</span>
                  ) : (
                    <span className="text-xs text-slate-300">—</span>
                  )}
                </td>
                <td className="px-5 py-3.5">
                  <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{url.category ?? '—'}</span>
                </td>
                <td className="px-5 py-3.5">
                  <span className="text-[13px] text-slate-600">{url.credibility_tier?.replace(/_/g, ' ')}</span>
                </td>
                <td className="px-5 py-3.5">
                  <StatusBadge status={url.is_active ? 'active' : 'inactive'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items && (
          <div className="border-t border-slate-100 bg-slate-50/50 px-5 py-3">
            <p className="text-xs text-slate-400">{data.total} total URLs</p>
          </div>
        )}
      </div>
    </div>
  )
}

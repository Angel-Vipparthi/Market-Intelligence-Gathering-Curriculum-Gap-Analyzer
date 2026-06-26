import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { CostDashboard } from '@/lib/types'

export function useCostDashboard(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['costs', startDate, endDate],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const { data } = await api.get('/costs', { params })
      return data as CostDashboard
    },
  })
}

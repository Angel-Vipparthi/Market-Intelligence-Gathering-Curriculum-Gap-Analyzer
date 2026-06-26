import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Gap } from '@/lib/types'

export function useGaps(filters?: { decision_status?: string; severity?: string; gap_type?: string }) {
  return useQuery({
    queryKey: ['gaps', filters],
    queryFn: async () => {
      const { data } = await api.get('/gaps', { params: filters })
      return data as { items: Gap[]; total: number; by_severity: Record<string, number> }
    },
  })
}

export function useGap(gapId: string) {
  return useQuery({
    queryKey: ['gap', gapId],
    queryFn: async () => {
      const { data } = await api.get(`/gaps/${gapId}`)
      return data as Gap
    },
    enabled: !!gapId,
  })
}

export function useGapSummary() {
  return useQuery({
    queryKey: ['gap-summary'],
    queryFn: async () => {
      const { data } = await api.get('/gaps/summary')
      return data
    },
  })
}

export function useReviewGap() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ gapId, decision, comments, feedback }: { gapId: string; decision: string; comments?: string; feedback?: string }) => {
      const { data } = await api.post(`/gaps/${gapId}/review`, { decision, comments, feedback })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gaps'] })
      qc.invalidateQueries({ queryKey: ['gap-summary'] })
    },
  })
}

export function useRunGapAnalysis() {
  return useMutation({
    mutationFn: async (digestId: string) => {
      const { data } = await api.post('/gap-analysis/run', { digest_id: digestId })
      return data
    },
  })
}

export interface GapBatchItem {
  digest_id: string
  url: string
  topic: string
  status: 'processing' | 'done'
  gaps_found: number
  gaps: { gap_id: string; gap_statement: string; severity: string; gap_type: string }[]
}

export function useGapBatchProgress(digestIds: string[], enabled: boolean) {
  return useQuery({
    queryKey: ['gap-batch-progress', digestIds],
    queryFn: async () => {
      const { data } = await api.post('/gap-analysis/batch-progress', { digest_ids: digestIds })
      return data as { items: GapBatchItem[]; completed: number; total: number }
    },
    enabled: enabled && digestIds.length > 0,
    refetchInterval: enabled ? 3000 : false,
  })
}

export function useGapReport() {
  return useQuery({
    queryKey: ['gap-report'],
    queryFn: async () => {
      const { data } = await api.get('/gaps/report')
      return data
    },
  })
}

export function useSubmitGapFeedback() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ gapId, feedback_what, feedback_why, feedback_when }: {
      gapId: string; feedback_what?: string; feedback_why?: string; feedback_when?: string
    }) => {
      const { data } = await api.post(`/gaps/${gapId}/feedback`, { feedback_what, feedback_why, feedback_when })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gap-report'] })
      qc.invalidateQueries({ queryKey: ['gaps'] })
    },
  })
}

export function useRunAllGapAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/gap-analysis/run-all')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['gaps'] })
      qc.invalidateQueries({ queryKey: ['gap-summary'] })
    },
  })
}

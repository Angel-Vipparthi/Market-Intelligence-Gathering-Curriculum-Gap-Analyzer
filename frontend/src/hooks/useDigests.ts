import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Digest } from '@/lib/types'

export function useDigests(status?: string) {
  return useQuery({
    queryKey: ['digests', status],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (status) params.status = status
      const { data } = await api.get('/digests', { params })
      return data as { items: Digest[]; total: number; pending_review: number }
    },
  })
}

export function useDigest(digestId: string) {
  return useQuery({
    queryKey: ['digest', digestId],
    queryFn: async () => {
      const { data } = await api.get(`/digests/${digestId}`)
      return data as Digest
    },
    enabled: !!digestId,
  })
}

export function useReviewDigest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ digestId, decision, comments }: { digestId: string; decision: string; comments?: string }) => {
      const { data } = await api.post(`/digests/${digestId}/review`, { decision, comments })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['digests'] })
    },
  })
}

export function useProcessDigest() {
  return useMutation({
    mutationFn: async (urlId: string) => {
      const { data } = await api.post('/digests/process', { url_id: urlId })
      return data
    },
  })
}

export function useProcessAllDigests() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/digests/process-all')
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['digests'] })
      qc.invalidateQueries({ queryKey: ['digest-status'] })
    },
  })
}

export interface BatchItem {
  url_id: string
  url: string
  status: 'processing' | 'done'
  topic: string | null
  curriculum_relevant: string | null
  market_signal: string | null
}

export function useBatchProgress(urlIds: string[], enabled: boolean) {
  return useQuery({
    queryKey: ['batch-progress', urlIds],
    queryFn: async () => {
      const { data } = await api.post('/digests/batch-progress', { url_ids: urlIds })
      return data as { items: BatchItem[]; completed: number; total: number }
    },
    enabled: enabled && urlIds.length > 0,
    refetchInterval: enabled ? 3000 : false,
  })
}

export function useDigestStatus() {
  return useQuery({
    queryKey: ['digest-status'],
    queryFn: async () => {
      const { data } = await api.get('/digests/status/summary')
      return data as {
        total_urls: number
        total_digests: number
        curriculum_relevant: number
        by_status: Record<string, number>
      }
    },
    refetchInterval: 5000,
  })
}

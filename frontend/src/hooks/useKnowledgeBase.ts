import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface KBCourse {
  id: string
  product_name: string
  course_name: string
  description: string | null
  total_modules?: number
  total_sessions?: number
  modules?: KBModule[]
}

export interface KBModule {
  id: string
  course_id: string
  module_name: string
  description: string | null
  sort_order: number
  sessions?: KBSession[]
}

export interface KBSession {
  id: string
  module_id: string
  title: string
  content_types: string[]
  level: number
  skills: string[]
  prerequisites: string[]
  description: string | null
  sort_order: number
}

export function useProducts() {
  return useQuery({
    queryKey: ['kb-products'],
    queryFn: async () => {
      const { data } = await api.get('/kb/products')
      return data.items as string[]
    },
  })
}

export function useKBCourses(productName?: string) {
  return useQuery({
    queryKey: ['kb-courses', productName],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (productName) params.product_name = productName
      const { data } = await api.get('/kb/courses', { params })
      return data.items as KBCourse[]
    },
  })
}

export function useKBModules(courseId: string) {
  return useQuery({
    queryKey: ['kb-modules', courseId],
    queryFn: async () => {
      const { data } = await api.get('/kb/modules', { params: { course_id: courseId } })
      return data.items as KBModule[]
    },
    enabled: !!courseId,
  })
}

export function useKBSessions(moduleId?: string) {
  return useQuery({
    queryKey: ['kb-sessions', moduleId],
    queryFn: async () => {
      const { data } = await api.get('/kb/sessions', { params: { module_id: moduleId } })
      return data.items as KBSession[]
    },
    enabled: !!moduleId,
  })
}

export function useKBHierarchy(productName?: string, courseId?: string) {
  return useQuery({
    queryKey: ['kb-hierarchy', productName, courseId],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (productName) params.product_name = productName
      if (courseId) params.course_id = courseId
      const { data } = await api.get('/kb/hierarchy', { params })
      return data.courses as KBCourse[]
    },
  })
}

export function useKBStats(productName?: string) {
  return useQuery({
    queryKey: ['kb-stats', productName],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (productName) params.product_name = productName
      const { data } = await api.get('/kb/stats', { params })
      return data as {
        total_courses: number
        total_modules: number
        total_sessions: number
        level_distribution: Record<string, number>
        content_type_distribution: Record<string, number>
        top_skills: Record<string, number>
      }
    },
  })
}

export interface KBNode {
  id: string
  title: string
  level: number
  skills: string[]
  content_types: string[]
  module_name: string
  course_name: string
}

export interface KBEdge {
  source: string
  target: string
  type: 'prerequisite' | 'prerequisite_unlinked' | 'shared_skills'
  label: string
}

export interface KBSkillCluster {
  skill: string
  sessions: string[]
  count: number
}

export function useKBConnections(productName?: string, courseId?: string) {
  return useQuery({
    queryKey: ['kb-connections', productName, courseId],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (productName) params.product_name = productName
      if (courseId) params.course_id = courseId
      const { data } = await api.get('/kb/connections', { params })
      return data as {
        nodes: KBNode[]
        edges: KBEdge[]
        skill_clusters: KBSkillCluster[]
        total_connections: number
        prereq_chains: number
        skill_links: number
      }
    },
  })
}

export interface MCQQuestion {
  question_content: string
  question_type: string
  correct_answer: string
  available_options: { content: string; option_id: string }[]
  exam_type: string
  parent_title?: string
}

export interface CodingQuestion {
  question_content: string
  question_type: string
  correct_answer?: string
  exam_type: string
  parent_title?: string
}

export interface SessionContent {
  session_title: string
  reading: { title: string; content: string; tools?: string[] }[]
  mcqs: MCQQuestion[]
  coding_practice: CodingQuestion[]
  total_reading: number
  total_mcqs: number
  total_coding: number
}

export function useSessionContent(sessionTitle: string | null, moduleName?: string) {
  return useQuery({
    queryKey: ['kb-session-content', sessionTitle, moduleName],
    queryFn: async () => {
      const params: Record<string, string> = { session_title: sessionTitle! }
      if (moduleName) params.module_name = moduleName
      const { data } = await api.get('/kb/session-content', { params })
      return data as SessionContent
    },
    enabled: !!sessionTitle,
  })
}

export interface ModuleAssessments {
  module_name: string
  mcqs: MCQQuestion[]
  coding: CodingQuestion[]
  total: number
}

export function useModuleAssessments(moduleName: string | null) {
  return useQuery({
    queryKey: ['kb-module-assessments', moduleName],
    queryFn: async () => {
      const { data } = await api.get('/kb/module-assessments', { params: { module_name: moduleName } })
      return data as ModuleAssessments
    },
    enabled: !!moduleName,
  })
}

export function useCreateCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { product_name: string; course_name: string; description?: string }) => {
      const { data } = await api.post('/kb/courses', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-courses'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['kb-products'] })
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
    },
  })
}

export function useCreateModule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { course_id: string; module_name: string; description?: string; sort_order?: number }) => {
      const { data } = await api.post('/kb/modules', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-modules'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
    },
  })
}

export function useCreateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      module_id: string; title: string; content_types: string[];
      level: number; skills: string[]; prerequisites?: string[]; description?: string; sort_order?: number
    }) => {
      const { data } = await api.post('/kb/sessions', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-sessions'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
    },
  })
}

export function useUpdateSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ sessionId, ...payload }: {
      sessionId: string; title?: string; content_types?: string[];
      level?: number; skills?: string[]; prerequisites?: string[]; description?: string
    }) => {
      const { data } = await api.put(`/kb/sessions/${sessionId}`, payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-sessions'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
    },
  })
}

export function useDeleteSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (sessionId: string) => {
      const { data } = await api.delete(`/kb/sessions/${sessionId}`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-sessions'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
    },
  })
}

export interface SheetConfig {
  id: string
  product_name: string
  course_name: string
  sheet_url: string
  spreadsheet_id: string
  last_loaded_at: string | null
}

export function useSheetConfigs(productName?: string) {
  return useQuery({
    queryKey: ['kb-sheet-configs', productName],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (productName) params.product_name = productName
      const { data } = await api.get('/kb/sheet-configs', { params })
      return data.items as SheetConfig[]
    },
  })
}

export function useLoadFromSheet() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { product_name: string; course_name: string; sheet_url: string }) => {
      const { data } = await api.post('/kb/load-from-sheet', payload)
      return data as { total_records: number; course_name: string; errors: string[] }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-sheet-configs'] })
      qc.invalidateQueries({ queryKey: ['kb-courses'] })
      qc.invalidateQueries({ queryKey: ['kb-hierarchy'] })
      qc.invalidateQueries({ queryKey: ['kb-stats'] })
      qc.invalidateQueries({ queryKey: ['kb-products'] })
      qc.invalidateQueries({ queryKey: ['urls'] })
    },
  })
}

export function useDeleteSheetConfig() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (configId: string) => {
      const { data } = await api.delete(`/kb/sheet-configs/${configId}`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb-sheet-configs'] })
    },
  })
}

export interface URLEntry {
  id: string
  url: string
  domain: string
  source_name: string
  credibility_tier: string
  category: string
  course_name: string | null
  tags: string[]
  is_active: boolean
  last_crawled_at: string | null
  created_at: string
}

export interface Digest {
  digest_id: string
  url: string
  source_title: string
  source_type: string
  topic: string
  summary: string
  market_signal: string
  evidence_snippet: string
  tools_versions: { tool: string; version: string; change_type: string }[]
  curriculum_relevant: string
  credibility_score: number
  status: string
  total_tokens: number
  total_cost: number
  created_at: string
}

export interface Gap {
  gap_id: string
  digest_id: string
  gap_type: string
  market_signal: string
  curriculum_evidence: string
  gap_statement: string
  what_to_act: string
  why_to_act: string
  when_to_act: string
  when_to_act_rationale: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  severity_score: number
  severity_factors: Record<string, number>
  impacted_content_area: string
  impacted_courses: string[]
  impacted_sessions: string[]
  impacted_projects: string[]
  impacted_assessments: string[]
  impacted_quizzes: string[]
  impacted_tools: string[]
  action_items: { action: string; priority: string; estimated_effort: string }[]
  recommended_owner: string
  evidence_source: string
  confidence: number
  critic_feedback: Record<string, unknown>[]
  decision_status: 'pending_review' | 'approved' | 'rejected' | 'needs_review'
  total_tokens: number
  total_cost: number
  created_at: string
}

export interface CostSummary {
  total_cost: number
  total_input_tokens: number
  total_output_tokens: number
  total_runs: number
  avg_cost_per_run: number
}

export interface CostByWorkflow {
  workflow_type: string
  total_cost: number
  total_runs: number
  avg_cost_per_run: number
}

export interface CostByNode {
  node_name: string
  model: string
  total_cost: number
  total_calls: number
  avg_latency_ms: number | null
}

export interface DailyCost {
  date: string
  total_cost: number
  total_runs: number
}

export interface CostDashboard {
  summary: CostSummary
  by_workflow: CostByWorkflow[]
  by_node: CostByNode[]
  daily: DailyCost[]
}

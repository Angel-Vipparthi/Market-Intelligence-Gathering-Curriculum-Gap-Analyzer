import { useState } from 'react'
import {
  useKBHierarchy, useKBStats, useKBCourses, useKBConnections, useSessionContent,
  type KBCourse, type KBModule, type KBSession, type KBNode, type KBEdge, type KBSkillCluster,
} from '@/hooks/useKnowledgeBase'
import {
  BookOpen, Layers, FileText, ChevronRight, ChevronDown,
  Code2, BookOpenCheck, HelpCircle, Tag, BarChart3,
  Loader2, ArrowRight, Network, Link as LinkIcon, Brain,
  CheckCircle2, XCircle,
} from 'lucide-react'

const PRODUCTS = ['NIAT']

const LEVEL_LABELS: Record<string, string> = {
  '1': 'Beginner', '2': 'Beginner', '3': 'Intermediate', '4': 'Intermediate',
  '5': 'Advanced', '6': 'Advanced', '7': 'Advanced',
}
const LEVEL_COLORS: Record<string, string> = {
  Beginner: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Intermediate: 'bg-amber-50 text-amber-700 border-amber-200',
  Advanced: 'bg-red-50 text-red-700 border-red-200',
}

function SessionContentPanel({ sessionTitle, moduleName }: { sessionTitle: string; moduleName?: string }) {
  const { data, isLoading } = useSessionContent(sessionTitle, moduleName)
  const [activeTab, setActiveTab] = useState<'reading' | 'mcqs' | 'coding'>('reading')
  const [showAnswers, setShowAnswers] = useState<Set<number>>(new Set())

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-6 justify-center text-slate-400">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading content...
      </div>
    )
  }

  if (!data) return null

  const tabs = [
    { key: 'reading' as const, label: 'Reading Material', icon: BookOpenCheck, count: data.total_reading, color: 'text-blue-600' },
    { key: 'mcqs' as const, label: 'MCQs', icon: HelpCircle, count: data.total_mcqs, color: 'text-amber-600' },
    { key: 'coding' as const, label: 'Coding Practice', icon: Code2, count: data.total_coding, color: 'text-emerald-600' },
  ]

  const toggleAnswer = (idx: number) => {
    setShowAnswers(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  return (
    <div className="border-t border-slate-100 bg-white">
      {/* Tabs */}
      <div className="flex border-b border-slate-100">
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.key
          return (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-[12px] font-semibold transition border-b-2 ${
                isActive
                  ? `${tab.color} border-current bg-slate-50/50`
                  : 'text-slate-400 border-transparent hover:text-slate-600 hover:bg-slate-50/30'
              }`}>
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.count > 0 && (
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                  isActive ? 'bg-current/10' : 'bg-slate-100'
                }`}>{tab.count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'reading' && (
          <div className="space-y-3">
            {data.reading.length === 0 ? (
              <p className="text-sm text-slate-400 italic py-4 text-center">No reading material available</p>
            ) : (
              data.reading.map((r, i) => (
                <div key={i} className="rounded-lg border border-blue-100 bg-blue-50/30 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <BookOpenCheck className="h-4 w-4 text-blue-500" />
                    <h4 className="text-[13px] font-semibold text-slate-800">{r.title}</h4>
                  </div>
                  <div className="text-[13px] text-slate-600 leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                    {r.content}
                  </div>
                  {r.tools && r.tools.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1 pt-2 border-t border-blue-100">
                      <span className="text-[10px] font-semibold text-slate-400 self-center mr-1">Tools:</span>
                      {r.tools.map(t => (
                        <span key={t} className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'mcqs' && (
          <div className="space-y-3">
            {data.mcqs.length === 0 ? (
              <p className="text-sm text-slate-400 italic py-4 text-center">No MCQ questions available</p>
            ) : (
              <>
                <p className="text-[12px] font-bold text-slate-500 uppercase tracking-wide">{data.mcqs.length} Questions</p>
                {data.mcqs.map((mcq, idx) => {
                  const isRevealed = showAnswers.has(idx)
                  let correctIds: string[] = []
                  try {
                    const parsed = JSON.parse(mcq.correct_answer)
                    correctIds = parsed.map((p: { option_id: string }) => p.option_id)
                  } catch { /* empty */ }

                  return (
                    <div key={idx} className="rounded-lg border border-amber-100 bg-white p-4">
                      <div className="flex items-start justify-between mb-3">
                        <p className="text-[13px] font-medium text-slate-800 flex-1">
                          <span className="text-amber-500 font-bold mr-1.5">Q{idx + 1}.</span>
                          {mcq.question_content}
                        </p>
                        {mcq.parent_title && (
                          <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-600 ml-2 whitespace-nowrap flex-shrink-0">
                            {mcq.parent_title}
                          </span>
                        )}
                      </div>
                      <div className="space-y-1.5">
                        {(mcq.available_options || []).map((opt, oi) => {
                          const isCorrect = correctIds.includes(opt.option_id)
                          return (
                            <div key={oi} className={`flex items-start gap-2 rounded-lg px-3 py-2 text-[12px] ${
                              isRevealed && isCorrect
                                ? 'bg-emerald-50 border border-emerald-200'
                                : isRevealed
                                  ? 'bg-red-50/30 border border-slate-100'
                                  : 'bg-slate-50 border border-slate-100'
                            }`}>
                              {isRevealed ? (
                                isCorrect
                                  ? <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                                  : <XCircle className="h-4 w-4 text-red-300 flex-shrink-0 mt-0.5" />
                              ) : (
                                <span className="h-4 w-4 flex items-center justify-center text-[10px] font-bold text-slate-400 flex-shrink-0 mt-0.5">
                                  {String.fromCharCode(65 + oi)}
                                </span>
                              )}
                              <span className={isRevealed && isCorrect ? 'text-emerald-700 font-medium' : 'text-slate-600'}>{opt.content}</span>
                            </div>
                          )
                        })}
                      </div>
                      <button onClick={() => toggleAnswer(idx)}
                        className="mt-2 text-[11px] font-semibold text-indigo-500 hover:text-indigo-700 transition">
                        {isRevealed ? 'Hide Answer' : 'Show Answer'}
                      </button>
                    </div>
                  )
                })}
              </>
            )}
          </div>
        )}

        {activeTab === 'coding' && (
          <div className="space-y-3">
            {data.coding_practice.length === 0 ? (
              <p className="text-sm text-slate-400 italic py-4 text-center">No coding practice available</p>
            ) : (
              <>
                <p className="text-[12px] font-bold text-slate-500 uppercase tracking-wide">{data.coding_practice.length} Coding Questions</p>
                {data.coding_practice.map((cq, i) => (
                  <div key={i} className="rounded-lg border border-emerald-100 bg-white p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Code2 className="h-4 w-4 text-emerald-500" />
                        <span className="text-[13px] font-semibold text-slate-800">Problem {i + 1}</span>
                      </div>
                      {cq.parent_title && (
                        <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600">
                          {cq.parent_title}
                        </span>
                      )}
                    </div>
                    <div className="text-[13px] text-slate-600 leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto bg-slate-50 rounded-lg p-3 border border-slate-100">
                      {cq.question_content}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SessionItem({ session, moduleName }: { session: KBSession; moduleName?: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const levelLabel = LEVEL_LABELS[String(session.level)] || 'Unknown'

  return (
    <div className="rounded-lg border border-slate-100 bg-white overflow-hidden hover:border-slate-200 transition">
      <button onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-slate-50/50 transition">
        {isOpen
          ? <ChevronDown className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
          : <ChevronRight className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />}

        <FileText className="h-4 w-4 text-slate-400 flex-shrink-0" />

        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-medium text-slate-800">{session.title}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${LEVEL_COLORS[levelLabel]}`}>
            L{session.level} {levelLabel}
          </span>
          {session.content_types.includes('reading') && (
            <span className="inline-flex items-center gap-0.5 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600">
              <BookOpenCheck className="h-3 w-3" />
            </span>
          )}
          {session.content_types.includes('quiz') && (
            <span className="inline-flex items-center gap-0.5 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600">
              <HelpCircle className="h-3 w-3" />
            </span>
          )}
          {session.content_types.includes('coding') && (
            <span className="inline-flex items-center gap-0.5 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600">
              <Code2 className="h-3 w-3" />
            </span>
          )}
        </div>
      </button>

      {/* Skills & prerequisites bar */}
      {isOpen && (session.skills.length > 0 || session.prerequisites.length > 0) && (
        <div className="px-4 py-2 border-t border-slate-50 bg-slate-50/50 flex flex-wrap gap-3">
          {session.skills.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <Tag className="h-3 w-3 text-indigo-400" />
              {session.skills.map(s => (
                <span key={s} className="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-medium text-indigo-600">{s}</span>
              ))}
            </div>
          )}
          {session.prerequisites.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[10px] font-semibold text-slate-400">Requires:</span>
              {session.prerequisites.map(p => (
                <span key={p} className="inline-flex items-center gap-0.5 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-600">
                  <ArrowRight className="h-2.5 w-2.5" />{p}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Content panel */}
      {isOpen && <SessionContentPanel sessionTitle={session.title} moduleName={moduleName} />}
    </div>
  )
}

function ModuleCard({ module }: { module: KBModule }) {
  const [isOpen, setIsOpen] = useState(false)
  const sessions = module.sessions ?? []
  const sessionCount = sessions.length
  const levelLabel = sessions.length > 0 ? LEVEL_LABELS[String(sessions[0].level)] || 'Unknown' : ''

  const readingCount = sessions.filter(s => s.content_types.includes('reading')).length
  const quizCount = sessions.filter(s => s.content_types.includes('quiz')).length
  const practiceCount = sessions.filter(s => s.content_types.includes('coding')).length

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
      <button onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-slate-50/30 transition">
        {isOpen
          ? <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />
          : <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />}

        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 flex-shrink-0">
          <Layers className="h-4 w-4 text-indigo-600" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold text-slate-900">{module.module_name}</p>
          {module.description && (
            <p className="text-[12px] text-slate-400 truncate mt-0.5">{module.description}</p>
          )}
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {levelLabel && (
            <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${LEVEL_COLORS[levelLabel] || 'bg-slate-50 text-slate-500 border-slate-200'}`}>
              {levelLabel}
            </span>
          )}

          <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
            {sessionCount} sessions
          </span>

          <div className="flex items-center gap-1">
            {readingCount > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600">
                <BookOpenCheck className="h-3 w-3" />{readingCount}
              </span>
            )}
            {quizCount > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600">
                <HelpCircle className="h-3 w-3" />{quizCount}
              </span>
            )}
            {practiceCount > 0 && (
              <span className="inline-flex items-center gap-0.5 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600">
                <Code2 className="h-3 w-3" />{practiceCount}
              </span>
            )}
          </div>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-slate-100 px-5 py-4 space-y-2 bg-slate-50/30">
          {sessions.map((s: KBSession) => (
            <SessionItem key={s.id} session={s} moduleName={module.module_name} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function KnowledgeBase() {
  const [product, setProduct] = useState(PRODUCTS[0])
  const [selectedCourseId, setSelectedCourseId] = useState<string>('')

  const { data: allCourses } = useKBCourses(product)
  const { data: hierarchy, isLoading } = useKBHierarchy(product, selectedCourseId || undefined)
  const { data: stats } = useKBStats(product)
  const { data: connections } = useKBConnections(product, selectedCourseId || undefined)

  const totalReading = stats?.content_type_distribution?.reading ?? 0
  const totalQuiz = stats?.content_type_distribution?.quiz ?? 0
  const totalCoding = stats?.content_type_distribution?.coding ?? 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-violet-50/50 to-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100">
              <Brain className="h-5 w-5 text-violet-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Module Mapping</h3>
              <p className="text-xs text-slate-400">Module → Session → Content (Reading / MCQ / Practice)</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div>
              <label className="block text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Product</label>
              <select value={product} onChange={e => { setProduct(e.target.value); setSelectedCourseId('') }}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-medium text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100">
                {PRODUCTS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1">Course</label>
              <select value={selectedCourseId} onChange={e => setSelectedCourseId(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-[13px] font-medium text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100">
                <option value="">All Courses</option>
                {(allCourses ?? []).map(c => <option key={c.id} value={c.id}>{c.course_name}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-7 divide-x divide-slate-100">
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Modules</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-violet-600">{stats?.total_modules ?? 0}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Sessions</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-indigo-600">{stats?.total_sessions ?? 0}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Reading</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-blue-600">{totalReading}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">MCQ</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-amber-600">{totalQuiz}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Practice</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-emerald-600">{totalCoding}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Beginner</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-emerald-600">{stats?.level_distribution?.Beginner ?? 0}</p>
          </div>
          <div className="px-3 py-3 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Advanced</p>
            <p className="mt-0.5 text-lg font-bold tabular-nums text-red-600">{stats?.level_distribution?.Advanced ?? 0}</p>
          </div>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-violet-500" />
        </div>
      )}

      {/* Module hierarchy */}
      {!isLoading && hierarchy?.map((course: KBCourse) => (
        <div key={course.id} className="space-y-3">
          <div className="flex items-center gap-3 px-1">
            <BookOpen className="h-4 w-4 text-violet-500" />
            <h2 className="text-[13px] font-bold text-slate-700">{course.course_name}</h2>
            <span className="rounded bg-violet-50 px-2 py-0.5 text-[10px] font-bold text-violet-600">{course.product_name}</span>
            <span className="text-[11px] text-slate-400">{course.total_modules} modules · {course.total_sessions} sessions</span>
          </div>

          {(course.modules ?? []).map((mod: KBModule) => (
            <ModuleCard key={mod.id} module={mod} />
          ))}
        </div>
      ))}

      {/* Empty state */}
      {!isLoading && (!hierarchy || hierarchy.length === 0) && (
        <div className="flex flex-col items-center justify-center py-20 rounded-xl border border-dashed border-slate-300 bg-white/50">
          <Brain className="h-12 w-12 text-slate-300" />
          <p className="mt-4 text-base font-medium text-slate-400">No courses found for {product}</p>
        </div>
      )}

      {/* Knowledge Connections */}
      {connections && (connections.edges.length > 0 || connections.skill_clusters.length > 0) && (
        <div className="space-y-5">
          <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-cyan-50/50 to-white">
              <div className="flex items-center gap-2">
                <Network className="h-5 w-5 text-cyan-600" />
                <h3 className="text-sm font-bold text-slate-900">How Knowledge is Connected</h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-400">Prerequisite chains, shared skills, and session relationships</p>
            </div>
            <div className="grid grid-cols-3 divide-x divide-slate-100">
              <div className="px-5 py-3 text-center">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Total Links</p>
                <p className="mt-0.5 text-lg font-bold tabular-nums text-slate-900">{connections.total_connections}</p>
              </div>
              <div className="px-5 py-3 text-center">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Prerequisite Chains</p>
                <p className="mt-0.5 text-lg font-bold tabular-nums text-cyan-600">{connections.prereq_chains}</p>
              </div>
              <div className="px-5 py-3 text-center">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Skill Links</p>
                <p className="mt-0.5 text-lg font-bold tabular-nums text-violet-600">{connections.skill_links}</p>
              </div>
            </div>
          </div>

          {/* Prerequisite Flow */}
          {connections.edges.filter((e: KBEdge) => e.type === 'prerequisite' || e.type === 'prerequisite_unlinked').length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <ArrowRight className="h-4 w-4 text-cyan-500" />
                  <h3 className="text-[13px] font-semibold text-slate-900">Prerequisite Dependencies</h3>
                </div>
              </div>
              <div className="divide-y divide-slate-100">
                {(() => {
                  const nodeMap = Object.fromEntries(connections.nodes.map((n: KBNode) => [n.id, n]))
                  return connections.edges
                    .filter((e: KBEdge) => e.type === 'prerequisite' || e.type === 'prerequisite_unlinked')
                    .map((edge: KBEdge, i: number) => {
                      const source = nodeMap[edge.source]
                      const target = nodeMap[edge.target]
                      return (
                        <div key={i} className="px-6 py-3 flex items-center gap-3 hover:bg-slate-50/50 transition">
                          <div className="min-w-0 flex-1">
                            {source ? (
                              <div className="flex items-center gap-2">
                                <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${LEVEL_COLORS[LEVEL_LABELS[String(source.level)] || 'Beginner']}`}>
                                  L{source.level}
                                </span>
                                <p className="text-[13px] font-medium text-slate-700 truncate">{source.title}</p>
                                <span className="text-[10px] text-slate-400">{source.module_name}</span>
                              </div>
                            ) : (
                              <p className="text-[13px] font-medium text-amber-600 italic">{edge.source} (external)</p>
                            )}
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0 px-2">
                            <div className="h-px w-6 bg-cyan-300" />
                            <ArrowRight className="h-4 w-4 text-cyan-500" />
                            <div className="h-px w-6 bg-cyan-300" />
                          </div>
                          <div className="min-w-0 flex-1">
                            {target && (
                              <div className="flex items-center gap-2">
                                <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${LEVEL_COLORS[LEVEL_LABELS[String(target.level)] || 'Beginner']}`}>
                                  L{target.level}
                                </span>
                                <p className="text-[13px] font-medium text-slate-700 truncate">{target.title}</p>
                                <span className="text-[10px] text-slate-400">{target.module_name}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })
                })()}
              </div>
            </div>
          )}

          {/* Shared Skills */}
          {connections.edges.filter((e: KBEdge) => e.type === 'shared_skills').length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <LinkIcon className="h-4 w-4 text-violet-500" />
                  <h3 className="text-[13px] font-semibold text-slate-900">Shared Skill Connections</h3>
                </div>
              </div>
              <div className="divide-y divide-slate-100">
                {(() => {
                  const nodeMap = Object.fromEntries(connections.nodes.map((n: KBNode) => [n.id, n]))
                  return connections.edges
                    .filter((e: KBEdge) => e.type === 'shared_skills')
                    .slice(0, 15)
                    .map((edge: KBEdge, i: number) => {
                      const source = nodeMap[edge.source]
                      const target = nodeMap[edge.target]
                      if (!source || !target) return null
                      return (
                        <div key={i} className="px-6 py-3 flex items-center gap-3 hover:bg-slate-50/50 transition">
                          <div className="min-w-0 flex-1">
                            <p className="text-[13px] font-medium text-slate-700 truncate">{source.title}</p>
                            <span className="text-[10px] text-slate-400">{source.module_name}</span>
                          </div>
                          <div className="flex flex-shrink-0 flex-wrap items-center gap-1 px-2 max-w-[220px] justify-center">
                            {edge.label.split(', ').map(sk => (
                              <span key={sk} className="rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-medium text-violet-600">{sk}</span>
                            ))}
                          </div>
                          <div className="min-w-0 flex-1 text-right">
                            <p className="text-[13px] font-medium text-slate-700 truncate">{target.title}</p>
                            <span className="text-[10px] text-slate-400">{target.module_name}</span>
                          </div>
                        </div>
                      )
                    })
                })()}
              </div>
            </div>
          )}

          {/* Skill Clusters */}
          {connections.skill_clusters.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white shadow-card overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-indigo-500" />
                  <h3 className="text-[13px] font-semibold text-slate-900">Skill Clusters</h3>
                </div>
              </div>
              <div className="px-6 py-4 grid grid-cols-2 gap-3">
                {connections.skill_clusters.slice(0, 12).map((cluster: KBSkillCluster) => (
                  <div key={cluster.skill} className="rounded-lg border border-slate-100 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="inline-flex items-center gap-1 rounded-lg bg-indigo-100 px-2.5 py-1 text-[12px] font-bold text-indigo-700">
                        <Tag className="h-3 w-3" />{cluster.skill}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-400">{cluster.count} sessions</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {cluster.sessions.slice(0, 4).map(s => (
                        <span key={s} className="rounded bg-slate-50 px-2 py-0.5 text-[10px] text-slate-600">{s}</span>
                      ))}
                      {cluster.sessions.length > 4 && (
                        <span className="text-[10px] text-slate-400">+{cluster.sessions.length - 4}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Skills */}
      {stats && Object.keys(stats.top_skills).length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-slate-400" />
            <h3 className="text-[13px] font-semibold text-slate-900">Top Skills Covered</h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(stats.top_skills).map(([skill, count]) => (
              <span key={skill} className="inline-flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1 text-[11px] font-medium text-indigo-700">
                {skill} <span className="rounded bg-indigo-100 px-1 text-[10px] font-bold">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

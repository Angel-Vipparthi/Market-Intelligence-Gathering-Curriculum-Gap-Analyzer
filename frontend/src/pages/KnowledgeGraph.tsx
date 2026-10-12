import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

interface GraphNode {
  id: string
  type: string
  name: string
  properties: Record<string, unknown>
  document_id: string | null
  x: number
  y: number
  vx: number
  vy: number
}

interface GraphEdge {
  id: string
  source: string
  target: string
  relationship: string
  weight: number
}

interface GraphData {
  total_nodes: number
  total_edges: number
  nodes_by_type: Record<string, number>
  edges_by_relationship: Record<string, number>
  nodes: Omit<GraphNode, 'x' | 'y' | 'vx' | 'vy'>[]
  edges: GraphEdge[]
}

const TYPE_COLORS: Record<string, string> = {
  course: '#3b82f6',
  module: '#8b5cf6',
  topic: '#10b981',
  tool: '#ef4444',
  session: '#f59e0b',
  project: '#06b6d4',
  version: '#ec4899',
  coding_challenge: '#84cc16',
  quiz: '#f97316',
  tool_registry: '#a855f7',
}

const NODE_RADIUS: Record<string, number> = {
  course: 16,
  module: 12,
  topic: 6,
  tool: 8,
  session: 5,
  project: 5,
  version: 4,
  coding_challenge: 4,
  quiz: 4,
  tool_registry: 5,
}

function useCourses() {
  return useQuery({
    queryKey: ['graph-courses'],
    queryFn: async () => {
      const { data } = await api.get('/graph/courses')
      return data.courses as string[]
    },
  })
}

function useGraph(course: string) {
  return useQuery({
    queryKey: ['graph', course],
    queryFn: async () => {
      const params = course ? { course } : {}
      const { data } = await api.get('/graph', { params })
      return data as GraphData
    },
  })
}

function useToolImpact(toolName: string) {
  return useQuery({
    queryKey: ['graph-impact', toolName],
    queryFn: async () => {
      const { data } = await api.get(`/graph/impact/${encodeURIComponent(toolName)}`)
      return data as { courses: string[]; sessions: string[]; projects: string[]; assessments: string[]; quizzes: string[]; tools: string[] }
    },
    enabled: !!toolName,
  })
}

export default function KnowledgeGraph() {
  const [selectedCourse, setSelectedCourse] = useState('')
  const { data: courses } = useCourses()
  const { data, isLoading } = useGraph(selectedCourse)
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const nodesRef = useRef<GraphNode[]>([])
  const edgesRef = useRef<GraphEdge[]>([])
  const sizeRef = useRef({ w: 900, h: 600 })
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [selectedTool, setSelectedTool] = useState('')
  const [filterType, setFilterType] = useState('')
  const [, forceRender] = useState(0)
  const { data: impact } = useToolImpact(selectedTool)
  const animRef = useRef<number>(0)
  const dragRef = useRef<GraphNode | null>(null)
  const panRef = useRef({ x: 0, y: 0 })
  const zoomRef = useRef(1)
  const isPanning = useRef(false)
  const lastMouse = useRef({ x: 0, y: 0 })

  // Resize observer
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      sizeRef.current = { w: width, h: height }
      const canvas = canvasRef.current
      if (canvas) {
        canvas.width = width * window.devicePixelRatio
        canvas.height = height * window.devicePixelRatio
        canvas.style.width = `${width}px`
        canvas.style.height = `${height}px`
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Init nodes from data
  useEffect(() => {
    if (!data) return
    const { w, h } = sizeRef.current
    const cx = w / 2, cy = h / 2

    // Group by type for clustered layout
    const byType: Record<string, typeof data.nodes> = {}
    for (const n of data.nodes) {
      ;(byType[n.type] ||= []).push(n)
    }
    const types = Object.keys(byType)

    const initialized: GraphNode[] = []
    types.forEach((type, ti) => {
      const angle0 = (ti / types.length) * Math.PI * 2
      const group = byType[type]
      const clusterR = 100 + group.length * 3
      group.forEach((n, ni) => {
        const a = angle0 + (ni / group.length) * Math.PI * 0.5 - Math.PI * 0.25
        const r = clusterR + (Math.random() - 0.5) * 80
        initialized.push({
          ...n,
          x: cx + Math.cos(a) * r,
          y: cy + Math.sin(a) * r,
          vx: 0,
          vy: 0,
        })
      })
    })

    nodesRef.current = initialized
    edgesRef.current = data.edges
    panRef.current = { x: 0, y: 0 }
    zoomRef.current = 1
  }, [data])

  // Simulation + render loop
  useEffect(() => {
    let running = true
    let tick = 0

    const loop = () => {
      if (!running) return
      const nodes = nodesRef.current
      const edges = edgesRef.current
      const canvas = canvasRef.current
      if (!canvas || !nodes.length) {
        animRef.current = requestAnimationFrame(loop)
        return
      }

      const { w, h } = sizeRef.current
      const cx = w / 2, cy = h / 2
      const nodeMap = new Map(nodes.map(n => [n.id, n]))
      const cooling = Math.max(0.01, 1 - tick * 0.003)
      tick++

      // Physics
      for (const node of nodes) {
        node.vx *= 0.85
        node.vy *= 0.85
        node.vx += (cx - node.x) * 0.0005
        node.vy += (cy - node.y) * 0.0005
      }

      // Repulsion (spatial hash for perf)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const d2 = dx * dx + dy * dy
          if (d2 > 40000) continue // skip if > 200px apart
          const dist = Math.sqrt(d2) || 1
          const force = (120 / (dist * dist)) * cooling
          nodes[i].vx -= dx * force
          nodes[i].vy -= dy * force
          nodes[j].vx += dx * force
          nodes[j].vy += dy * force
        }
      }

      // Edge attraction
      for (const edge of edges) {
        const s = nodeMap.get(edge.source)
        const t = nodeMap.get(edge.target)
        if (!s || !t) continue
        const dx = t.x - s.x
        const dy = t.y - s.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const ideal = 60
        const force = (dist - ideal) * 0.005 * cooling
        s.vx += (dx / dist) * force
        s.vy += (dy / dist) * force
        t.vx -= (dx / dist) * force
        t.vy -= (dy / dist) * force
      }

      // Apply velocities
      for (const node of nodes) {
        if (dragRef.current?.id === node.id) continue
        node.x += node.vx
        node.y += node.vy
      }

      // Render
      const ctx = canvas.getContext('2d')
      if (!ctx) { animRef.current = requestAnimationFrame(loop); return }
      const dpr = window.devicePixelRatio
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      // Background
      ctx.fillStyle = '#f8fafc'
      ctx.fillRect(0, 0, w, h)

      ctx.save()
      ctx.translate(panRef.current.x, panRef.current.y)
      ctx.scale(zoomRef.current, zoomRef.current)

      const filteredIds = filterType
        ? new Set(nodes.filter(n => n.type === filterType).map(n => n.id))
        : null
      const hovered = hoveredNode

      // Edges
      for (const edge of edges) {
        const s = nodeMap.get(edge.source)
        const t = nodeMap.get(edge.target)
        if (!s || !t) continue
        if (filteredIds && !filteredIds.has(s.id) && !filteredIds.has(t.id)) continue

        const isHighlighted = hovered && (edge.source === hovered.id || edge.target === hovered.id)
        ctx.beginPath()
        ctx.moveTo(s.x, s.y)
        ctx.lineTo(t.x, t.y)
        ctx.strokeStyle = isHighlighted ? '#3b82f6' : '#cbd5e1'
        ctx.lineWidth = isHighlighted ? 1.5 : 0.3
        ctx.globalAlpha = isHighlighted ? 0.8 : 0.4
        ctx.stroke()
      }
      ctx.globalAlpha = 1

      // Nodes
      for (const node of nodes) {
        if (filteredIds && !filteredIds.has(node.id)) continue
        const color = TYPE_COLORS[node.type] || '#6b7280'
        const r = NODE_RADIUS[node.type] || 4
        const isHovered = hovered?.id === node.id
        const isConnected = hovered && edges.some(
          e => (e.source === hovered.id && e.target === node.id) || (e.target === hovered.id && e.source === node.id)
        )

        ctx.beginPath()
        ctx.arc(node.x, node.y, isHovered ? r + 3 : r, 0, Math.PI * 2)
        ctx.fillStyle = isHovered ? '#1e40af' : color
        ctx.globalAlpha = (!hovered || isHovered || isConnected) ? 1 : 0.3
        ctx.fill()

        if (isHovered || isConnected || r >= 8) {
          ctx.font = `${isHovered ? 'bold ' : ''}${isHovered ? 12 : 10}px Inter, system-ui, sans-serif`
          ctx.fillStyle = '#0f172a'
          ctx.globalAlpha = (!hovered || isHovered || isConnected) ? 1 : 0.2
          ctx.textAlign = 'center'
          const label = node.name.length > 25 ? node.name.slice(0, 24) + '...' : node.name
          ctx.fillText(label, node.x, node.y - r - 5)
        }
      }
      ctx.globalAlpha = 1

      ctx.restore()

      animRef.current = requestAnimationFrame(loop)
    }

    loop()
    return () => { running = false; cancelAnimationFrame(animRef.current) }
  }, [hoveredNode, filterType])

  // Mouse: hover, drag, pan, zoom
  const toGraphCoords = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current
    if (!canvas) return { gx: 0, gy: 0 }
    const rect = canvas.getBoundingClientRect()
    const mx = clientX - rect.left
    const my = clientY - rect.top
    const gx = (mx - panRef.current.x) / zoomRef.current
    const gy = (my - panRef.current.y) / zoomRef.current
    return { gx, gy }
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const { gx, gy } = toGraphCoords(e.clientX, e.clientY)

    if (dragRef.current) {
      dragRef.current.x = gx
      dragRef.current.y = gy
      dragRef.current.vx = 0
      dragRef.current.vy = 0
      return
    }

    if (isPanning.current) {
      panRef.current.x += e.clientX - lastMouse.current.x
      panRef.current.y += e.clientY - lastMouse.current.y
      lastMouse.current = { x: e.clientX, y: e.clientY }
      return
    }

    let found: GraphNode | null = null
    for (const node of nodesRef.current) {
      const dx = node.x - gx
      const dy = node.y - gy
      const r = NODE_RADIUS[node.type] || 4
      if (dx * dx + dy * dy < (r + 5) * (r + 5)) {
        found = node
        break
      }
    }
    setHoveredNode(found)
    const canvas = canvasRef.current
    if (canvas) canvas.style.cursor = found ? 'grab' : 'default'
  }, [toGraphCoords])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    lastMouse.current = { x: e.clientX, y: e.clientY }
    if (hoveredNode) {
      dragRef.current = hoveredNode
      const canvas = canvasRef.current
      if (canvas) canvas.style.cursor = 'grabbing'
    } else {
      isPanning.current = true
      const canvas = canvasRef.current
      if (canvas) canvas.style.cursor = 'move'
    }
  }, [hoveredNode])

  const handleMouseUp = useCallback(() => {
    dragRef.current = null
    isPanning.current = false
    const canvas = canvasRef.current
    if (canvas) canvas.style.cursor = 'default'
  }, [])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.92 : 1.08
    const newZoom = Math.min(4, Math.max(0.2, zoomRef.current * delta))
    const rect = canvasRef.current?.getBoundingClientRect()
    if (rect) {
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top
      panRef.current.x = mx - (mx - panRef.current.x) * (newZoom / zoomRef.current)
      panRef.current.y = my - (my - panRef.current.y) * (newZoom / zoomRef.current)
    }
    zoomRef.current = newZoom
  }, [])

  const handleClick = useCallback(() => {
    if (hoveredNode?.type === 'tool') {
      setSelectedTool(hoveredNode.name)
      forceRender(v => v + 1)
    }
  }, [hoveredNode])

  if (isLoading) return <div className="flex h-full items-center justify-center text-gray-400">Loading graph...</div>

  const tools = (data?.nodes ?? []).filter(n => n.type === 'tool').map(n => n.name).sort()

  return (
    <div className="flex h-full flex-col gap-3" style={{ minHeight: 0 }}>
      {/* Top bar */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
          className="rounded-lg border px-3 py-1.5 text-sm font-medium"
        >
          <option value="">All Courses</option>
          {(courses ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="text-xs text-gray-400">|</span>
        <span className="text-sm font-semibold text-gray-700">{data?.total_nodes} nodes</span>
        <span className="text-xs text-gray-400">|</span>
        <span className="text-sm font-semibold text-gray-700">{data?.total_edges} edges</span>
        <span className="text-xs text-gray-400">|</span>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setFilterType('')}
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${!filterType ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
          >
            All
          </button>
          {Object.entries(data?.nodes_by_type ?? {}).map(([type, count]) => (
            <button
              key={type}
              onClick={() => setFilterType(filterType === type ? '' : type)}
              className="flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium transition"
              style={{
                backgroundColor: filterType === type ? TYPE_COLORS[type] : TYPE_COLORS[type] + '18',
                color: filterType === type ? '#fff' : TYPE_COLORS[type],
              }}
            >
              <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: filterType === type ? '#fff' : TYPE_COLORS[type] }} />
              {type.replace('_', ' ')} ({count})
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-400">Scroll to zoom. Drag nodes. Click tools for impact.</span>
      </div>

      {/* Canvas container — fills remaining height */}
      <div ref={containerRef} className="relative min-h-0 flex-1 overflow-hidden rounded-lg border border-gray-200">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          onClick={handleClick}
          className="block h-full w-full"
        />
        {/* Hover tooltip */}
        {hoveredNode && (
          <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-2 rounded-lg border bg-white/95 px-3 py-2 shadow-sm backdrop-blur">
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: TYPE_COLORS[hoveredNode.type] || '#6b7280' }} />
            <span className="text-sm font-semibold text-gray-800">{hoveredNode.name}</span>
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">{hoveredNode.type}</span>
          </div>
        )}
      </div>

      {/* Tool impact panel */}
      <div className="flex gap-3">
        <select
          value={selectedTool}
          onChange={(e) => setSelectedTool(e.target.value)}
          className="w-64 rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">Tool Impact Analysis...</option>
          {tools.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        {impact && selectedTool && (
          <div className="flex flex-1 items-start gap-6 rounded-lg border bg-white px-4 py-2">
            <span className="text-sm font-semibold text-gray-700">"{selectedTool}"</span>
            {impact.courses.length > 0 && (
              <div>
                <span className="text-xs font-medium text-blue-600">Courses:</span>
                <span className="ml-1 text-xs text-gray-600">{impact.courses.join(', ')}</span>
              </div>
            )}
            {impact.sessions.length > 0 && (
              <div>
                <span className="text-xs font-medium text-green-600">Sessions ({impact.sessions.length}):</span>
                <span className="ml-1 text-xs text-gray-600">{impact.sessions.slice(0, 5).join(', ')}{impact.sessions.length > 5 ? ` +${impact.sessions.length - 5} more` : ''}</span>
              </div>
            )}
            {impact.projects.length > 0 && (
              <div>
                <span className="text-xs font-medium text-yellow-600">Projects ({impact.projects.length}):</span>
                <span className="ml-1 text-xs text-gray-600">{impact.projects.slice(0, 4).join(', ')}{impact.projects.length > 4 ? ` +${impact.projects.length - 4} more` : ''}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

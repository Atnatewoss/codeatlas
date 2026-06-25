"use client"

import { useMemo } from "react"

interface Node {
  x: number
  y: number
  id: string
  delay: number
  depth: number
}

interface Edge {
  x1: number
  y1: number
  x2: number
  y2: number
}

interface TreeLayout {
  nodes: Node[]
  edges: Edge[]
  totalHeight: number
}

const CENTER_X = 200
const LEVEL_GAP = 50
const TOP_PADDING = 24
const BASE_SPREAD = 170

function buildTreeLayout(maxDepth: number, maxChildren: number): TreeLayout {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // Build level-by-level (x positions only)
  const levels: { x: number; parentX: number | null }[][] = []
  levels.push([{ x: CENTER_X, parentX: null }])

  for (let d = 1; d <= maxDepth; d++) {
    const prev = levels[d - 1]
    const cur: { x: number; parentX: number }[] = []
    const spread = Math.max(BASE_SPREAD * Math.pow(0.55, d - 1), 30)
    const count = d === 1 ? maxChildren : Math.max(1, maxChildren - 1)

    for (const parent of prev) {
      for (let i = 0; i < count; i++) {
        const cx = parent.x - spread / 2 + (spread / (count + 1)) * (i + 1)
        cur.push({ x: cx, parentX: parent.x })
      }
    }

    levels.push(cur)
  }

  // Convert to nodes + edges
  for (let d = 0; d < levels.length; d++) {
    const y = TOP_PADDING + d * LEVEL_GAP
    for (const item of levels[d]) {
      const id = `n${nodes.length}`
      const delay = d * 0.45 + Math.random() * 0.35
      nodes.push({ x: item.x, y, id, delay, depth: d })

      if (item.parentX !== null && d > 0) {
        edges.push({ x1: item.parentX, y1: y - LEVEL_GAP, x2: item.x, y2: y })
      }
    }
  }

  const totalHeight = TOP_PADDING + (maxDepth + 1) * LEVEL_GAP
  return { nodes, edges, totalHeight }
}

interface AnimatedTreeProps {
  maxDepth?: number
  maxChildren?: number
}

export function AnimatedTree({ maxDepth = 3, maxChildren = 3 }: AnimatedTreeProps) {
  const layout = useMemo(() => buildTreeLayout(maxDepth, maxChildren), [maxDepth, maxChildren])
  const { nodes, edges, totalHeight } = layout

  if (nodes.length === 0) {
    return null
  }

  return (
    <svg
      viewBox={`0 0 ${CENTER_X * 2} ${totalHeight}`}
      fill="none"
      className="w-full h-full overflow-visible"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#5B8AF0" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#5B8AF0" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Connection lines */}
      {edges.map((e, i) => (
        <line
          key={`e${i}`}
          x1={e.x1}
          y1={e.y1}
          x2={e.x2}
          y2={e.y2}
          stroke="#4B4B5E"
          strokeWidth="0.5"
          strokeOpacity="0.3"
        />
      ))}

      {/* Ripple rings */}
      {nodes.map((n) => (
        <circle
          key={`r-${n.id}`}
          cx={n.x}
          cy={n.y}
          r={3}
          fill="none"
          stroke="#5B8AF0"
          strokeWidth="0.5"
          style={{ animation: `node-ripple 3s ease-out ${n.delay}s infinite` }}
        />
      ))}

      {/* Node glow */}
      {nodes.map((n) => (
        <circle
          key={`g-${n.id}`}
          cx={n.x}
          cy={n.y}
          r={8}
          fill="url(#nodeGlow)"
          style={{ animation: `node-pulse 2.5s ease-in-out ${n.delay}s infinite` }}
        />
      ))}

      {/* Node core */}
      {nodes.map((n) => (
        <circle
          key={n.id}
          cx={n.x}
          cy={n.y}
          r={2.5}
          fill="#5B8AF0"
          style={{ animation: `node-pulse 2.5s ease-in-out ${n.delay}s infinite` }}
        />
      ))}
    </svg>
  )
}

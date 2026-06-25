"use client"

import { useMemo, type ComponentType } from "react"
import { cn } from "@/lib/utils"
import type { ChatThought } from "@/lib/api"
import { Search, FolderSearch, FileText, Tags, PhoneCall, BarChart3 } from "lucide-react"

const TOOL_ICONS: Record<string, ComponentType<{ className?: string }>> = {
  grep: Search,
  glob: FolderSearch,
  read_file: FileText,
  lookup_symbol: Tags,
  get_callers: PhoneCall,
  get_callees: PhoneCall,
  graph_stats: BarChart3,
}

const FALLBACK_ICON = Search

interface ToTTreeNode {
  thought: ChatThought
  children: ToTTreeNode[]
  depth: number
}

function buildTree(thoughts: ChatThought[]): ToTTreeNode[] {
  const map = new Map<string, ToTTreeNode>()
  const roots: ToTTreeNode[] = []

  for (const t of thoughts) {
    map.set(t.id, { thought: t, children: [], depth: t.depth ?? 0 })
  }

  for (const node of map.values()) {
    const pid = node.thought.parent_id
    if (pid && map.has(pid)) {
      map.get(pid)!.children.push(node)
    } else {
      roots.push(node)
    }
  }

  // Assign depth recursively for roots that have undefined depth
  function setDepth(node: ToTTreeNode, d: number) {
    node.depth = d
    for (const child of node.children) {
      setDepth(child, d + 1)
    }
  }
  for (const root of roots) {
    setDepth(root, root.thought.depth ?? 1)
  }

  return roots
}

function scoreColor(score?: number): string {
  if (score === undefined || score <= 0) return "bg-muted/30 border-muted/30"
  if (score >= 0.7) return "bg-green-500/10 border-green-500/30"
  if (score >= 0.4) return "bg-amber-500/10 border-amber-500/30"
  return "bg-red-500/5 border-red-500/20"
}

function scoreLabel(score?: number): string {
  if (score === undefined || score <= 0) return ""
  return `${(score * 100).toFixed(0)}%`
}

function TreeNode({ node, isLast }: { node: ToTTreeNode; isLast: boolean }) {
  const t = node.thought
  const isPruned = t.is_pruned
  const isActive = !isPruned && (t.score === undefined || t.score === 0)
  const hasChildren = node.children.length > 0
  const Icon = TOOL_ICONS[t.tool || ""] || FALLBACK_ICON

  return (
    <div className="relative">
      {/* Vertical connector from parent */}
      {node.depth > 0 && (
        <div className="absolute left-3 top-0 bottom-0 w-px bg-border/40 -translate-x-1/2" />
      )}

      <div className={cn(
        "relative ml-4 mb-2 rounded-lg border px-2.5 py-2 text-[11px] transition-colors",
        scoreColor(t.score),
        isPruned && "opacity-40 line-through decoration-red-500/30",
        isActive && "animate-pulse border-primary/20",
      )}>
        {/* Horizontal connector from vertical line */}
        {node.depth > 0 && (
          <div className="absolute left-0 top-3 w-3 h-px bg-border/40 -translate-x-full" />
        )}

        <div className="flex items-center gap-1.5">
          {isActive && (
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
            </span>
          )}
          {!isActive && <Icon className="w-3 h-3 text-muted-foreground shrink-0" />}
          <span className="font-medium text-foreground truncate flex-1">{t.description || t.id}</span>
          {t.score !== undefined && t.score > 0 && (
            <span className={cn(
              "shrink-0 text-[9px] px-1 py-px rounded-full font-medium",
              t.score >= 0.7 ? "bg-green-500/15 text-green-500" : "bg-amber-500/15 text-amber-500",
            )}>
              {scoreLabel(t.score)}
            </span>
          )}
          {isPruned && (
            <span className="shrink-0 text-[9px] px-1 py-px rounded-full font-medium bg-red-500/15 text-red-500">pruned</span>
          )}
        </div>

        {/* Per-axis breakdown */}
        {t.score !== undefined && t.score > 0 && !isPruned && (
          <div className="flex items-center gap-2 mt-0.5 text-[9px] text-muted-foreground/50 font-mono">
            <span>R:{t.relevance !== undefined ? (t.relevance * 100).toFixed(0) : "?"}%</span>
            <span>E:{t.evidence_strength !== undefined ? (t.evidence_strength * 100).toFixed(0) : "?"}%</span>
            <span>D:{t.source_diversity !== undefined ? (t.source_diversity * 100).toFixed(0) : "?"}%</span>
          </div>
        )}

        {t.tool && (
          <div className="text-muted-foreground/60 font-mono text-[9px] truncate mt-0.5">
            {t.tool}: {t.target}
          </div>
        )}

        {/* Pruning rationale */}
        {isPruned && t.prune_reason && (
          <div className="text-[9px] text-red-500/60 mt-0.5 truncate" title={t.prune_reason}>
            score {t.score !== undefined ? (t.score * 100).toFixed(0) : "?"}% &lt; {t.prune_threshold !== undefined ? (t.prune_threshold * 100).toFixed(0) : "40"}% threshold — {t.prune_reason.slice(0, 100)}
          </div>
        )}

        {t.outcome && (
          <div className="text-muted-foreground/50 text-[9px] font-mono mt-1 bg-background/40 p-1 rounded border border-border/20 line-clamp-2">
            {t.outcome.slice(0, 120)}
          </div>
        )}
      </div>

      {hasChildren && (
        <div className="ml-2 border-l border-border/30 pl-1">
          {node.children.map((child, i) => (
            <TreeNode key={child.thought.id} node={child} isLast={i === node.children.length - 1} />
          ))}
        </div>
      )}
    </div>
  )
}

function DepthLevel({ level, nodes }: { level: number; nodes: ToTTreeNode[] }) {
  if (nodes.length === 0) return null

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 px-1 py-1">
        <div className="h-px flex-1 bg-border/30" />
        <span className="text-[10px] font-mono text-muted-foreground/40 font-medium">Depth {level}</span>
        <div className="h-px flex-1 bg-border/30" />
        <span className="text-[9px] text-muted-foreground/30 tabular-nums">{nodes.length} thought{nodes.length !== 1 ? "s" : ""}</span>
      </div>
      {nodes.map((node) => (
        <TreeNode key={node.thought.id} node={node} isLast />
      ))}
    </div>
  )
}

export function ToTTree({ thoughts }: { thoughts: ChatThought[] }) {
  const roots = useMemo(() => buildTree(thoughts), [thoughts])

  // Group nodes by depth level for the structured view
  const byDepth = useMemo(() => {
    const groups = new Map<number, ToTTreeNode[]>()
    function walk(node: ToTTreeNode) {
      const d = node.depth
      if (!groups.has(d)) groups.set(d, [])
      groups.get(d)!.push(node)
      for (const child of node.children) walk(child)
    }
    for (const root of roots) walk(root)

    // Sort by depth
    const sorted = Array.from(groups.entries()).sort(([a], [b]) => a - b)
    return sorted.map(([level, nodes]) => ({ level, nodes }))
  }, [roots])

  if (thoughts.length === 0) {
    return <div className="text-[11px] text-muted-foreground/40 px-2 py-4 text-center">No thoughts yet</div>
  }

  return (
    <div className="space-y-2">
      {/* Header stats */}
      <div className="flex items-center gap-3 px-1 text-[10px] text-muted-foreground/50">
        <span>{thoughts.length} total nodes</span>
        <span>{roots.length} root bran{roots.length !== 1 ? "ches" : "ch"}</span>
        <span>{byDepth.length} depth level{byDepth.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Tree visualization */}
      <div className="space-y-2">
        {byDepth.map(({ level, nodes }) => (
          <DepthLevel key={level} level={level} nodes={nodes} />
        ))}
      </div>
    </div>
  )
}

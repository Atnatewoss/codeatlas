"use client"

import { ChevronDown, ChevronRight, Clock, Network } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatStreamState } from "@/lib/api"
import { MermaidBlock } from "@/components/chat/mermaid-block"
import { ToTTree } from "@/components/chat/tot-tree"


function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

function getStatusLabel(s: ChatStreamState): string {
  if (s.isComplete) return "Research complete"
  const phase = s.phase
  if (phase === "cloning" || phase === "initializing") return s.cloneProgress || "Starting..."
  if (phase === "building_graph") return "Building code graph..."
  if (phase === "generate_thoughts") return "Thinking about how to explore..."
  if (phase === "execute_batch") return `Exploring codebase (${s.thoughts.length} paths)...`
  if (phase === "evaluate_batch") return `Analyzing results (depth ${s.depth})...`
  if (phase === "prune_expand" && s.depth > 1) return `Deepening search (depth ${s.depth})...`
  if (phase === "synthesize") return "Formulating answer..."
  if (phase) return `${phase}...`
  return "Starting research..."
}


interface ThinkingSectionProps {
  isResearching: boolean
  chatState: ChatStreamState
  thoughtsExpanded: boolean
  onToggleExpanded: () => void
  elapsed: number
}

export function ThinkingSection({
  isResearching,
  chatState,
  thoughtsExpanded,
  onToggleExpanded,
  elapsed,
}: ThinkingSectionProps) {
  return (
    <div className={cn(
      "bg-card rounded-2xl overflow-hidden shadow-sm border-l-2 transition-colors duration-500",
      isResearching ? "border-l-primary" : "border-l-transparent"
    )}>
      <button
        onClick={onToggleExpanded}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          {isResearching ? (
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          ) : (
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="relative inline-flex rounded-full h-2 w-2 bg-muted-foreground/30" />
            </span>
          )}
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-medium shrink-0">Deep thinking</span>
            <span className="text-xs text-muted-foreground tabular-nums shrink-0 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(elapsed)}
            </span>
            {isResearching && chatState.thoughts.length > 0 && (
              <span className="text-xs text-muted-foreground/60 bg-muted px-2 py-0.5 rounded-full truncate max-w-[160px]">
                {chatState.thoughts.length} thoughts
              </span>
            )}
            <span className="text-xs text-muted-foreground/60 truncate max-w-[200px] hidden sm:inline">
              {!chatState.isComplete ? getStatusLabel(chatState) : "Research complete"}
            </span>
          </div>
        </div>
        {thoughtsExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
        )}
      </button>

      {/* Expanded thought details + status */}
      {thoughtsExpanded && (
        <div className="px-4 pb-3 space-y-1.5">
          {/* Clone + build messages */}
          {chatState.cloneProgress && chatState.phase === "cloning" && (
            <div className="text-xs text-muted-foreground/60 font-mono bg-muted/20 px-2.5 py-1.5 rounded-lg">
              {chatState.cloneProgress}
            </div>
          )}

          {/* Code architecture diagram from graphify — always visible */}
          {chatState.graphDiagram && (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50 px-1 py-1">
                <Network className="w-3 h-3" />
                <span>Architecture diagram</span>
                <span className="text-[9px] text-muted-foreground/30">({chatState.graphDiagram.split('\n').filter(l => l.includes('-->')).length} call edges)</span>
              </div>
              <MermaidBlock content={chatState.graphDiagram.replace(/^```mermaid\n?|```$/g, '')} />
            </div>
          )}

          <ToTTree thoughts={chatState.thoughts} />

          {chatState.uncertainties.length > 0 && (
            <div className="px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <div className="text-[10px] font-medium text-amber-500 mb-1">Uncertainties</div>
              {chatState.uncertainties.map((u, i) => (
                <div key={i} className="text-[9px] text-amber-500/70">{u}</div>
              ))}
            </div>
          )}

          {/* Rejected branches + uncertainties summaries — only if non-empty */}
          {chatState.rejectedBranches && (
            <div className="px-3 py-2 rounded-lg bg-red-500/5 border border-red-500/20">
              <div className="text-[10px] font-medium text-red-500 mb-1">Rejected Branches</div>
              <div className="text-[9px] text-red-500/70 whitespace-pre-wrap">{chatState.rejectedBranches}</div>
            </div>
          )}

          {chatState.uncertaintiesSummary && (
            <div className="px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <div className="text-[10px] font-medium text-amber-500 mb-1">Uncertainties</div>
              <div className="text-[9px] text-amber-500/70 whitespace-pre-wrap">{chatState.uncertaintiesSummary}</div>
            </div>
          )}

          {chatState.depth > 0 && (
            <div className="text-[10px] text-muted-foreground/40">
              BFS depth: {chatState.depth}/{chatState.maxDepth}
            </div>
          )}

          {/* Final time display */}
          {chatState.isComplete && (
            <div className="text-[10px] text-muted-foreground/40 pt-1 border-t border-border/40">
              Completed in {formatTime(elapsed)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

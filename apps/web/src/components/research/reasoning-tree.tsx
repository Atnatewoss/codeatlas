"use client"

import { Brain, CheckCircle2, AlertTriangle, XCircle } from "lucide-react"
import type { ChatThought } from "@/lib/api"
import { cn } from "@/lib/utils"

export function ReasoningTree({
  thoughts,
  depth,
  maxDepth,
}: {
  thoughts?: ChatThought[]
  depth?: number
  maxDepth?: number
}) {
  if (!thoughts || thoughts.length === 0) {
    return (
      <div className="font-mono text-xs leading-5 text-muted-foreground">
        <div className="text-foreground font-semibold mb-2 flex items-center gap-2">
          <Brain className="w-3.5 h-3.5" />
          Tree of Thought
        </div>
        <p className="text-[11px] text-muted-foreground/60 italic">Waiting for thoughts...</p>
      </div>
    )
  }

  return (
    <div className="font-mono text-xs leading-5 text-muted-foreground">
      <div className="text-foreground font-semibold mb-2 flex items-center gap-2">
        <Brain className="w-3.5 h-3.5" />
        Tree of Thought
        {depth !== undefined && (
          <span className="text-[10px] text-muted-foreground font-normal">
            BFS depth {depth}/{maxDepth ?? "?"}
          </span>
        )}
      </div>

      <div className="pl-2 border-l border-border ml-2 space-y-3">
        {thoughts.map((thought, idx) => {
          const isPruned = thought.is_pruned
          const isHigh = thought.score !== undefined && thought.score >= 0.7
          const isMid = thought.score !== undefined && thought.score >= 0.4 && thought.score < 0.7

          return (
            <div key={thought.id}>
              <div className={cn(
                "flex items-center gap-1.5",
                isPruned && "opacity-40"
              )}>
                <span className="w-4 border-t border-border inline-block mr-1" />
                {isPruned ? (
                  <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                ) : isHigh ? (
                  <CheckCircle2 className="w-3 h-3 text-green-500 shrink-0" />
                ) : isMid ? (
                  <AlertTriangle className="w-3 h-3 text-amber-500 shrink-0" />
                ) : (
                  <Brain className="w-3 h-3 text-muted-foreground shrink-0" />
                )}
                <span className={cn(
                  "font-medium truncate",
                  isPruned ? "text-red-400/60" : isHigh ? "text-green-500" : "text-foreground"
                )}>
                  {thought.description || `Thought ${idx + 1}`}
                </span>
                {thought.score !== undefined && thought.score > 0 && (
                  <span className={cn(
                    "shrink-0 text-[10px] px-1.5 py-0.5 rounded-full font-medium ml-auto",
                    isHigh ? "bg-green-500/10 text-green-500" :
                    isMid ? "bg-amber-500/10 text-amber-500" :
                    "bg-muted text-muted-foreground"
                  )}>
                    {(thought.score * 100).toFixed(0)}%
                  </span>
                )}
                {isPruned && (
                  <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-red-500/10 text-red-400">
                    pruned
                  </span>
                )}
              </div>
              {thought.hypothesis && !isPruned && (
                <div className="pl-8 text-[10px] text-muted-foreground/60 italic mt-0.5">
                  {thought.hypothesis.slice(0, 100)}
                </div>
              )}
              {!isPruned && thought.relevance !== undefined && (
                <div className="pl-8 text-[9px] text-muted-foreground/40 mt-0.5">
                  rel: {(thought.relevance * 100).toFixed(0)}%
                  {" | "}ev: {(thought.evidence_strength! * 100).toFixed(0)}%
                  {thought.source_diversity !== undefined && (
                    <> | div: {(thought.source_diversity * 100).toFixed(0)}%</>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

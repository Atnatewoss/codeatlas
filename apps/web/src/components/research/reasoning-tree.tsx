"use client"

import { AlertTriangle, CheckCircle2, Loader2, GitBranch, Search, Layers, BookOpen, Shield } from "lucide-react"
import { getResearchStatus, type ResearchStatusResponse } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"

const BRANCH_ICONS: Record<string, typeof Search> = {
  structure: Layers,
  runtime: GitBranch,
  design: Search,
  onboarding: BookOpen,
  risk: Shield,
}

const BRANCH_LABELS: Record<string, string> = {
  structure: "Structure Analysis",
  runtime: "Runtime Analysis",
  design: "Design Reasoning",
  onboarding: "Developer Onboarding",
  risk: "Risk Assessment",
}

const BRANCH_ORDER = ["structure", "runtime", "design", "onboarding", "risk"] as const

export function ReasoningTree({ sessionId }: { sessionId: string }) {
  const { data } = useQuery<ResearchStatusResponse>({
    queryKey: ["researchStatus", sessionId],
    queryFn: () => getResearchStatus(sessionId),
    refetchInterval: (query) => {
      if (!query.state.data) return 3000
      if (query.state.data.status === "complete" || query.state.data.status === "failed") return false
      return 3000
    },
  })

  const branches = data?.branches
  const evaluation = data?.evaluation
  const synthesis = data?.synthesis
  const isComplete = data?.status === "complete"
  const hasContradictions = evaluation && evaluation.contradictions.length > 0

  return (
    <div className="font-mono text-xs leading-5 text-muted-foreground">
      <div className="text-foreground font-semibold mb-2 flex items-center gap-2">
        Reasoning Tree
        {isComplete && <CheckCircle2 className="w-3 h-3 text-green-500" />}
      </div>

      <div className="pl-2 border-l border-border ml-2 space-y-4">
        {BRANCH_ORDER.map((key) => {
          const Icon = BRANCH_ICONS[key]
          const status = branches?.[key]?.status ?? "idle"
          const findings = branches?.[key]?.findings ?? []

          return (
            <div key={key}>
              <div className="flex items-center gap-1.5">
                <span className="w-4 border-t border-border inline-block mr-1"></span>
                <Icon className="w-3 h-3 text-muted-foreground shrink-0" />
                <span className={`font-medium ${status === "complete" ? "text-green-500" : "text-foreground"}`}>
                  {BRANCH_LABELS[key]}
                </span>
                {status === "running" && <Loader2 className="w-3 h-3 animate-spin ml-auto" />}
                {status === "complete" && <CheckCircle2 className="w-3 h-3 text-green-500 ml-auto" />}
              </div>
              {findings.length > 0 && (
                <div className="pl-8 border-l border-border ml-3 mt-1 space-y-1">
                  {findings.slice(0, 3).map((f, i) => (
                    <div key={i} className="flex items-start gap-1">
                      <span className="text-foreground/40 mt-0.5">└</span>
                      <span className="truncate text-[11px]">{f.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {/* Evaluation Section */}
        {evaluation && (
          <div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 border-t border-border inline-block mr-1"></span>
              <AlertTriangle className={`w-3 h-3 shrink-0 ${hasContradictions ? "text-amber-500" : "text-green-500"}`} />
              <span className={`font-medium ${hasContradictions ? "text-amber-500" : "text-green-500"}`}>
                Evaluation
              </span>
            </div>
            <div className="pl-8 border-l border-border ml-3 mt-1 space-y-1">
              <div className="flex items-center gap-1 text-[11px]">
                <span className="text-foreground/40">└</span>
                {evaluation.contradictions.length} contradictions, {evaluation.agreements.length} agreements
              </div>
              {evaluation.investigation_needed && (
                <div className="flex items-center gap-1 text-[11px] text-amber-500">
                  <span className="text-foreground/40">└</span>
                  Investigation round {data?.investigation_round ?? 1}
                </div>
              )}
              {hasContradictions && evaluation.contradictions.slice(0, 2).map((c, i) => (
                <div key={i} className="flex items-start gap-1 text-[11px] text-amber-500/80">
                  <span className="text-foreground/40 mt-0.5">└</span>
                  <span className="truncate">{c.finding_a} vs {c.finding_b}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Synthesis Section */}
        {synthesis && isComplete && (
          <div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 border-t border-border inline-block mr-1"></span>
              <CheckCircle2 className="w-3 h-3 text-primary shrink-0" />
              <span className="font-medium text-primary">Synthesis</span>
            </div>
            <div className="pl-8 border-l border-border ml-3 mt-1 space-y-1">
              <div className="text-[11px] text-muted-foreground line-clamp-2">
                <span className="text-foreground/40">└ </span>
                {synthesis.summary}
              </div>
              {synthesis.key_insights.slice(0, 3).map((insight, i) => (
                <div key={i} className="flex items-start gap-1 text-[11px]">
                  <span className="text-foreground/40 mt-0.5">└</span>
                  <span className="truncate">{insight.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

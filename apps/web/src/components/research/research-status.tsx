"use client"

import { Check, Loader2 } from "lucide-react"
import { getResearchStatus } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"

interface BranchStatus {
  node_id: string
  status: string
  findings: string[]
  evidence: { filepath: string; snippet: string; explanation: string }[]
}

interface ResearchBranches {
  structure: BranchStatus
  runtime: BranchStatus
  design: BranchStatus
  onboarding: BranchStatus
  risk: BranchStatus
}

const BRANCH_LABELS: Record<string, string> = {
  structure: "Structure Analysis",
  runtime: "Runtime Analysis",
  design: "Design Reasoning",
  onboarding: "Developer Onboarding",
  risk: "Risk Assessment",
}

const BRANCH_ORDER = ["structure", "runtime", "design", "onboarding", "risk"] as const

export function ResearchStatus({ sessionId }: { sessionId: string }) {
  const { data, isError } = useQuery({
    queryKey: ["researchStatus", sessionId],
    queryFn: () => getResearchStatus(sessionId),
    refetchInterval: (query) => {
      if (!query.state.data) return 2000
      const allDone = BRANCH_ORDER.every(
        (key) => query.state.data.branches[key]?.status === "done"
      )
      return allDone ? false : 2000
    },
  })

  const branches = data?.branches

  if (isError) {
    return <div className="text-sm text-destructive-foreground">Lost connection to the research server.</div>
  }

  return (
    <div className="space-y-4">
      {BRANCH_ORDER.map((key) => {
        const status = branches?.[key]?.status ?? "pending"
        const label = BRANCH_LABELS[key]
        const findings = branches?.[key]?.findings ?? []

        return (
          <div key={key} className="space-y-1.5">
            <div className="flex items-center gap-3 text-sm">
              {status === "done" ? (
                <div className="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
                  <Check className="w-3 h-3" />
                </div>
              ) : status === "running" ? (
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground shrink-0" />
              ) : (
                <div className="w-5 h-5 rounded-full border border-dashed border-muted-foreground/50 shrink-0" />
              )}
              <span className={status === "pending" ? "text-muted-foreground" : "text-foreground font-medium"}>
                {label}
              </span>
            </div>

            {/* Show findings inline when branch completes */}
            {status === "done" && findings.length > 0 && (
              <div className="ml-8 space-y-1">
                {findings.slice(0, 2).map((f: string, i: number) => (
                  <div key={i} className="text-xs text-muted-foreground leading-relaxed truncate">
                    • {f}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

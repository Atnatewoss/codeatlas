"use client"

import { useEffect, useState, useCallback } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileCode2, ExternalLink } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { getResearchStatus } from "@/lib/api"

interface Evidence {
  filepath: string
  snippet: string
  explanation: string
}

interface ReportSection {
  label: string
  findings: string[]
  evidence: Evidence[]
}

const BRANCH_ORDER = ["structure", "runtime", "design", "onboarding", "risk"] as const
const BRANCH_LABELS: Record<string, string> = {
  structure: "Structure Analysis",
  runtime: "Runtime Analysis",
  design: "Design Reasoning",
  onboarding: "Developer Onboarding",
  risk: "Risk Assessment",
}

export function EvidencePanel({ sessionId }: { sessionId: string }) {
  const [sections, setSections] = useState<ReportSection[]>([])
  const [allEvidence, setAllEvidence] = useState<Evidence[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const data = await getResearchStatus(sessionId)
      const newSections: ReportSection[] = []
      const evidenceAcc: Evidence[] = []

      for (const key of BRANCH_ORDER) {
        const branch = data.branches[key]
        if (branch && branch.status === "done") {
          newSections.push({
            label: BRANCH_LABELS[key],
            findings: branch.findings,
            evidence: branch.evidence,
          })
          evidenceAcc.push(...branch.evidence)
        }
      }

      setSections(newSections)
      setAllEvidence(evidenceAcc)

      const allDone = BRANCH_ORDER.every((k) => data.branches[k]?.status === "done")
      if (allDone) setLoading(false)
      return allDone
    } catch {
      setLoading(false)
      return true
    }
  }, [sessionId])

  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      while (!cancelled) {
        const done = await fetchData()
        if (done || cancelled) break
        await new Promise((r) => setTimeout(r, 3000))
      }
    }
    poll()
    return () => { cancelled = true }
  }, [fetchData])

  return (
    <Tabs defaultValue="evidence" className="flex-1 flex flex-col h-full w-full">
      <div className="px-4 py-2 border-b bg-background">
        <TabsList className="w-full justify-start h-auto p-1 bg-transparent border">
          <TabsTrigger value="evidence" className="text-xs">Evidence</TabsTrigger>
          <TabsTrigger value="report" className="text-xs">Full Report</TabsTrigger>
          <TabsTrigger value="architecture" className="text-xs">Diagrams</TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">

          {/* Evidence Tab */}
          <TabsContent value="evidence" className="mt-0 space-y-4">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Cited References
            </div>
            {loading && allEvidence.length === 0 ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-lg" />
                ))}
              </div>
            ) : allEvidence.length === 0 ? (
              <p className="text-sm text-muted-foreground">No evidence gathered yet.</p>
            ) : (
              <div className="space-y-2">
                {allEvidence.map((ev, i) => (
                  <div key={i} className="group p-3 rounded-lg border bg-card hover:border-primary/50 transition-colors cursor-pointer">
                    <div className="flex items-center gap-2 text-sm font-medium mb-1.5">
                      <FileCode2 className="w-4 h-4 text-muted-foreground shrink-0" />
                      <span className="truncate">{ev.filepath}</span>
                      <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto opacity-0 group-hover:opacity-100 shrink-0" />
                    </div>
                    {ev.snippet && (
                      <div className="text-xs text-muted-foreground font-mono bg-muted/50 p-2 rounded border mb-1.5 truncate">
                        {ev.snippet}
                      </div>
                    )}
                    {ev.explanation && (
                      <div className="text-xs text-muted-foreground line-clamp-2">
                        {ev.explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Full Report Tab */}
          <TabsContent value="report" className="mt-0 space-y-6">
            <h3 className="text-foreground font-medium text-base">Deep Research Report</h3>
            {loading && sections.length === 0 ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-4/5" />
                  </div>
                ))}
              </div>
            ) : (
              sections.map((section, i) => (
                <div key={i} className="space-y-2">
                  <h4 className="text-sm font-semibold text-foreground">{section.label}</h4>
                  <ul className="space-y-1.5">
                    {section.findings.map((finding, j) => (
                      <li key={j} className="text-sm text-muted-foreground leading-relaxed flex gap-2">
                        <span className="text-primary mt-0.5 shrink-0">•</span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            )}
          </TabsContent>

          {/* Diagrams Tab */}
          <TabsContent value="architecture" className="mt-0">
            <div className="aspect-square bg-muted/30 rounded-lg border border-dashed flex items-center justify-center flex-col text-muted-foreground">
              <span className="text-sm font-medium">LikeC4 Diagram</span>
              <span className="text-xs mt-1 text-center px-4">
                Interactive architecture graph — generated from reasoning branches
              </span>
            </div>
          </TabsContent>

        </div>
      </ScrollArea>
    </Tabs>
  )
}

"use client"

import { useEffect, useState } from "react"
import { Check, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ResearchStatus({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 4) {
          clearInterval(interval)
          setTimeout(onComplete, 1000)
          return 4
        }
        return p + 1
      })
    }, 2000)
    return () => clearInterval(interval)
  }, [onComplete])

  const steps = [
    { title: "Architecture Analysis", state: progress > 0 ? "done" : progress === 0 ? "running" : "pending" },
    { title: "Execution Flow Analysis", state: progress > 1 ? "done" : progress === 1 ? "running" : "pending" },
    { title: "Design Decision Analysis", state: progress > 2 ? "done" : progress === 2 ? "running" : "pending" },
    { title: "Learning Path Analysis", state: progress > 3 ? "done" : progress === 3 ? "running" : "pending" },
  ]

  return (
    <Card className="bg-transparent border-0 shadow-none">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-sm font-medium">Research Branches</CardTitle>
      </CardHeader>
      <CardContent className="px-0 space-y-4">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-3 text-sm">
            {step.state === "done" ? (
              <div className="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
                <Check className="w-3 h-3" />
              </div>
            ) : step.state === "running" ? (
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground shrink-0" />
            ) : (
              <div className="w-5 h-5 rounded-full border border-dashed border-muted-foreground/50 shrink-0" />
            )}
            <span className={step.state === "pending" ? "text-muted-foreground" : "text-foreground font-medium"}>
              {step.title}
            </span>
          </div>
        ))}

        <div className="pt-6 border-t mt-6">
          <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-3">Pending</div>
          <div className="text-sm text-muted-foreground flex items-center gap-3">
             <div className="w-5 h-5 rounded-full border border-dashed border-muted-foreground/50 shrink-0" />
             Dependency Analysis
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

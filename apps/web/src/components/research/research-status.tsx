"use client"

import { useEffect, useState } from "react"
import { Check, Loader2 } from "lucide-react"

export function ResearchStatus() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 5) {
          clearInterval(interval)
          return 5
        }
        return p + 1
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const steps = [
    { title: "Structure Analysis", state: progress > 0 ? "done" : progress === 0 ? "running" : "pending" },
    { title: "Runtime Analysis", state: progress > 1 ? "done" : progress === 1 ? "running" : "pending" },
    { title: "Design Reasoning", state: progress > 2 ? "done" : progress === 2 ? "running" : "pending" },
    { title: "Developer Onboarding", state: progress > 3 ? "done" : progress === 3 ? "running" : "pending" },
    { title: "Risk Assessment", state: progress > 4 ? "done" : progress === 4 ? "running" : "pending" },
  ]

  return (
    <div className="space-y-4">
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
    </div>
  )
}

"use client"

import { useState, useRef, useEffect } from "react"
import { Composer } from "@/components/chat/composer"
import { MessageComponent } from "@/components/chat/message"
import { sendChatMessage, type ResearchStatusResponse } from "@/lib/api"
import { useMutation } from "@tanstack/react-query"
import { Loader2, Sparkles, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: string[]
}

export function ChatPanel({ sessionId, statusData }: { sessionId: string, statusData?: ResearchStatusResponse }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "I'm starting the deep research process. I'll build a mental model of this repository and report back shortly. Feel free to ask me questions while I work!",
      citations: []
    }
  ])

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, statusData])

  const { mutate: sendMessage, isPending: isLoading } = useMutation({
    mutationFn: (history: { role: string; content: string }[]) => sendChatMessage(sessionId, history),
    onSuccess: (res) => {
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.content,
        citations: res.citations ?? [],
      }
      setMessages((prev) => [...prev, assistantMsg])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I couldn't reach the research server. Make sure the API is running on port 8000.",
        },
      ])
    }
  })

  const handleSend = (content: string) => {
    if (!content.trim() || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    }

    setMessages((prev) => [...prev, userMsg])

    const history = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }))

    sendMessage(history)
  }

  const isResearching = statusData?.status === "cloning" || statusData?.status === "running"
  const isComplete = statusData?.status === "complete"
  
  const sourceCount = statusData?.branches 
    ? Object.values(statusData.branches)
        .filter(b => b.status === 'complete')
        .reduce((acc, b) => acc + (b.findings ? b.findings.reduce((fAcc, f) => fAcc + (f.evidence ? f.evidence.length : 0), 0) : 0), 0)
    : 0;

  const repoName = statusData?.repo_url ? new URL(statusData.repo_url).pathname.slice(1) : "the repository"

  return (
    <div className="flex-1 flex flex-col h-full bg-gradient-to-b from-background to-muted/10">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        {messages.map((msg) => (
          <MessageComponent
            key={msg.id}
            role={msg.role}
            content={msg.content}
            citations={msg.citations}
          />
        ))}

        {/* Live Research Bubble */}
        {statusData && (isResearching || isComplete) && (
          <div className="flex flex-col items-start gap-2 max-w-3xl mx-auto w-full group">
            <div className="flex items-center gap-3 w-full">
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border shadow-sm transition-all duration-700",
                isComplete ? "bg-primary/10 border-primary/20 text-primary" : "bg-muted border-border/50 text-muted-foreground"
              )}>
                {isComplete ? <CheckCircle2 className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
              </div>
              
              <div className="flex-1 bg-card border rounded-2xl p-4 shadow-sm relative overflow-hidden transition-all duration-500 hover:shadow-md hover:border-primary/30">
                {isResearching && (
                  <div className="absolute top-0 left-0 w-full h-[2px] bg-muted overflow-hidden">
                    <div className="absolute top-0 left-0 h-full bg-primary w-1/3 animate-[translateX_2s_ease-in-out_infinite]" style={{ transform: "translateX(-100%)", animationName: "indeterminate-progress" }}></div>
                  </div>
                )}
                
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {isResearching && <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />}
                    <span className="text-sm font-medium tracking-tight">
                      {statusData.status === "cloning" ? `Cloning ${repoName}` : 
                       statusData.status === "running" ? `Analyzing ${repoName}` :
                       `Research complete for ${repoName}`}
                    </span>
                  </div>
                  <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                    {sourceCount} sources
                  </span>
                </div>

                <div className="space-y-2">
                  {statusData.status === "cloning" ? (
                    <div className="text-xs font-mono text-muted-foreground bg-muted/50 p-2 rounded-lg border border-border/50 truncate">
                      {statusData.clone_progress || "Initializing clone..."}
                    </div>
                  ) : (
                    <div className="flex flex-col gap-1.5">
                      {["structure", "runtime", "design", "onboarding", "risk"].map(branch => {
                        const bStatus = statusData.branches[branch as keyof typeof statusData.branches]?.status;
                        if (!bStatus || bStatus === "idle") return null;
                        return (
                          <div key={branch} className="flex items-center gap-2 text-xs">
                            {bStatus === "complete" ? (
                              <CheckCircle2 className="w-3 h-3 text-green-500 shrink-0" />
                            ) : bStatus === "running" ? (
                              <Loader2 className="w-3 h-3 text-primary animate-spin shrink-0" />
                            ) : (
                              <div className="w-3 h-3 rounded-full border border-dashed border-muted-foreground/50 shrink-0" />
                            )}
                            <span className={cn("capitalize tracking-tight", bStatus === "complete" ? "text-foreground" : "text-muted-foreground")}>
                              {branch} Analysis
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center gap-3 max-w-3xl mx-auto">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            </div>
            <div className="flex gap-1 py-3 bg-muted/30 px-3 rounded-2xl border">
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-3xl mx-auto">
          <Composer onSend={handleSend} disabled={isLoading} />
        </div>
      </div>
    </div>
  )
}

"use client"

import { useState } from "react"
import { ChatPanel } from "@/components/chat/chat-panel"
import { ReasoningTree } from "@/components/research/reasoning-tree"
import { ResearchStatus } from "@/components/research/research-status"
import { EvidencePanel } from "@/components/research/evidence-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Github, Play, GitBranch } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { startResearch } from "@/lib/api"

export default function Home() {
  const [researchState, setResearchState] = useState<"idle" | "researching">("idle")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [repoUrl, setRepoUrl] = useState("")
  const [isStarting, setIsStarting] = useState(false)

  const handleStartResearch = async () => {
    if (!repoUrl) return
    setIsStarting(true)
    try {
      const res = await startResearch(repoUrl)
      setSessionId(res.session_id)
      setResearchState("researching")
    } catch (e) {
      console.error(e)
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <div className="flex-1 flex h-full overflow-hidden">
      
      {/* Left Panel: Research Branches (Visible when researching) */}
      {researchState === "researching" && sessionId && (
        <div className="w-[320px] bg-background border-r flex flex-col shrink-0">
          <div className="h-14 border-b flex items-center px-4 font-medium text-sm gap-2">
            <GitBranch className="w-4 h-4 text-muted-foreground" />
            Tree of Thought
          </div>
          <ScrollArea className="flex-1">
            <div className="p-4 space-y-8">
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                  Active Branches
                </h3>
                <ResearchStatus sessionId={sessionId} />
              </div>
              
              <div className="border-t pt-6">
                <ReasoningTree />
              </div>
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Middle: Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full min-w-0 border-r border-border/50">
        {researchState === "idle" ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-md w-full space-y-8">
              <div className="text-center space-y-2">
                <h1 className="text-2xl font-semibold tracking-tight">Analyze an Open Source Repository</h1>
                <p className="text-muted-foreground text-sm">Provide a GitHub URL to build a mental model of an unfamiliar codebase.</p>
              </div>
              
              <div className="space-y-4">
                <div className="relative">
                  <Github className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder="https://github.com/..." 
                    className="pl-9 h-10 bg-background/50" 
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                  />
                </div>
                <Button 
                  className="w-full" 
                  onClick={handleStartResearch}
                  disabled={isStarting || !repoUrl}
                >
                  <Play className="w-4 h-4 mr-2" />
                  {isStarting ? "Starting..." : "Start Deep Research"}
                </Button>
              </div>

              <div className="pt-8 space-y-3">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider text-center">
                  Examples
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  <Button variant="secondary" size="sm" className="h-8" onClick={() => setRepoUrl("https://github.com/langchain-ai/langgraph")}>langchain-ai/langgraph</Button>
                  <Button variant="secondary" size="sm" className="h-8" onClick={() => setRepoUrl("https://github.com/pyrpc/pyrpc")}>pyrpc/pyrpc</Button>
                  <Button variant="secondary" size="sm" className="h-8" onClick={() => setRepoUrl("https://github.com/fastapi/fastapi")}>fastapi/fastapi</Button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ChatPanel sessionId={sessionId!} />
        )}
      </div>

      {/* Right Side Panel: Evidence */}
      {researchState === "researching" && (
        <div className="w-[380px] bg-background flex flex-col shrink-0">
          <EvidencePanel sessionId={sessionId!} />
        </div>
      )}
    </div>
  )
}

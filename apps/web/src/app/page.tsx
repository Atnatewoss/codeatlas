"use client"

import { useState } from "react"
import { ChatPanel } from "@/components/chat/chat-panel"
import { ResearchStatus } from "@/components/research/research-status"
import { ReasoningTree } from "@/components/research/reasoning-tree"
import { ArchitecturePanel } from "@/components/research/architecture-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Github, Play } from "lucide-react"

export default function Home() {
  const [researchState, setResearchState] = useState<"idle" | "researching" | "completed">("idle")

  return (
    <div className="flex-1 flex h-full overflow-hidden">
      {/* Left/Center: Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full max-w-4xl mx-auto border-r border-border/50">
        {researchState === "idle" ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-md w-full space-y-8">
              <div className="text-center space-y-2">
                <h1 className="text-2xl font-semibold tracking-tight">Analyze an Open Source Repository</h1>
                <p className="text-muted-foreground text-sm">Provide a GitHub URL to start a Tree of Thought research session.</p>
              </div>
              
              <div className="space-y-4">
                <div className="relative">
                  <Github className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="https://github.com/..." className="pl-9 h-10 bg-background/50" />
                </div>
                <Button 
                  className="w-full" 
                  onClick={() => setResearchState("researching")}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Research
                </Button>
              </div>

              <div className="pt-8 space-y-3">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider text-center">
                  Examples
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  <Button variant="secondary" size="sm" className="h-8">langchain-ai/langgraph</Button>
                  <Button variant="secondary" size="sm" className="h-8">pyrpc/pyrpc</Button>
                  <Button variant="secondary" size="sm" className="h-8">fastapi/fastapi</Button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ChatPanel />
        )}
      </div>

      {/* Right Side Panel: Progress and Reports */}
      {researchState !== "idle" && (
        <div className="w-[480px] bg-background flex flex-col shrink-0">
          <div className="h-14 border-b flex items-center px-4 font-medium text-sm">
            Workspace
          </div>
          
          <div className="flex-1 overflow-auto">
            {researchState === "researching" ? (
              <div className="p-4">
                <ResearchStatus onComplete={() => setResearchState("completed")} />
              </div>
            ) : (
              <div className="h-full flex flex-col">
                <ArchitecturePanel />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

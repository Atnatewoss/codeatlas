"use client"

import { useState } from "react"
import { ChatPanel } from "@/components/chat/chat-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AnimatedTree } from "@/components/research/animated-tree"
import { Github, Play, Sparkles } from "lucide-react"

export function HomeContent() {
  const [researchState, setResearchState] = useState<"idle" | "researching">("idle")
  const [repoUrl, setRepoUrl] = useState("")

  const handleStartResearch = () => {
    if (!repoUrl) return
    setResearchState("researching")
  }

  if (researchState === "researching") {
    return <ChatPanel sessionId={repoUrl || "default"} repoPath={repoUrl} />
  }

  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 relative flex flex-col items-center justify-center overflow-hidden px-4">
        {/* Background tree */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
          <div className="w-full max-w-2xl opacity-20 sm:opacity-25">
            <AnimatedTree />
          </div>
        </div>

        {/* Gradient overlays for edge fade */}
        <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-background to-transparent pointer-events-none" />
        <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none" />
        <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-background to-transparent pointer-events-none" />
        <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-background to-transparent pointer-events-none" />

        {/* Foreground content */}
        <div className="relative z-10 w-full max-w-lg mx-auto space-y-8">
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center gap-2 mb-4">
              <div className="h-px w-8 bg-border" />
              <Sparkles className="w-4 h-4 text-muted-foreground" />
              <div className="h-px w-8 bg-border" />
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              CodeAtlas
            </h1>
            <p className="text-muted-foreground text-sm max-w-sm mx-auto leading-relaxed">
              Paste any repository URL and let Tree-of-Thought AI explore, reason, and explain the codebase.
            </p>
          </div>

          <div className="bg-card/60 backdrop-blur-xl border border-border/50 rounded-2xl p-2 shadow-2xl shadow-black/40">
            <div className="relative">
              <Github className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="https://github.com/org/repo"
                className="pl-11 h-12 text-sm bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/50"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStartResearch()}
              />
            </div>
            <div className="px-1 pb-1 pt-2">
              <Button
                className="w-full h-10 text-sm font-medium"
                onClick={handleStartResearch}
                disabled={!repoUrl}
              >
                <Play className="w-4 h-4 mr-2" />
                Start Deep Research
              </Button>
            </div>
          </div>

          <div className="text-center space-y-3">
            <div className="text-[11px] font-medium text-muted-foreground/50 uppercase tracking-widest">
              Explore examples
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              <Button
                variant="secondary" size="sm" className="h-8 text-xs"
                onClick={() => setRepoUrl("https://github.com/langchain-ai/langgraph")}
              >
                langchain-ai/langgraph
              </Button>
              <Button
                variant="secondary" size="sm" className="h-8 text-xs"
                onClick={() => setRepoUrl("https://github.com/encode/starlette")}
              >
                encode/starlette
              </Button>
              <Button
                variant="secondary" size="sm" className="h-8 text-xs"
                onClick={() => setRepoUrl("C:\\Users\\Admin\\Documents\\dev\\personal project\\pyrpc")}
              >
                pyrpc (local)
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

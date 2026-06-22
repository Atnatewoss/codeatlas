"use client"

import { useState } from "react"
import { ChatPanel } from "@/components/chat/chat-panel"
import { ReasoningTree } from "@/components/research/reasoning-tree"
import { ResearchStatus } from "@/components/research/research-status"
import { EvidencePanel } from "@/components/research/evidence-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Github, Play, GitBranch, CheckCircle2, AlertCircle, PanelLeftClose, PanelLeftOpen, Settings } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { startResearch } from "@/lib/api"
import { useMutation, useQuery } from "@tanstack/react-query"
import { getResearchStatus } from "@/lib/api"
import type { ResearchStatusResponse } from "@/lib/api"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"

export default function Home() {
  const [researchState, setResearchState] = useState<"idle" | "researching">("idle")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [repoUrl, setRepoUrl] = useState("")
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const { mutate: startResearchMutation, isPending: isStarting } = useMutation({
    mutationFn: startResearch,
    onSuccess: (res) => {
      setSessionId(res.session_id)
      setResearchState("researching")
    },
    onError: (e) => {
      console.error(e)
    },
  })

  const { data: statusData } = useQuery<ResearchStatusResponse>({
    queryKey: ["researchStatus", sessionId],
    queryFn: () => getResearchStatus(sessionId!),
    enabled: researchState === "researching" && !!sessionId,
    refetchInterval: (query) => {
      if (!query.state.data) return 2000
      if (query.state.data.status === "complete" || query.state.data.status === "failed") return false
      return 2000
    },
  })

  const isComplete = statusData?.status === "complete"
  const isFailed = statusData?.status === "failed"

  const sourceCount = statusData?.branches 
    ? Object.values(statusData.branches)
        .filter(b => b.status === 'complete')
        .reduce((acc, b) => acc + (b.findings ? b.findings.reduce((fAcc, f) => fAcc + (f.evidence ? f.evidence.length : 0), 0) : 0), 0)
    : 0;

  const handleStartResearch = () => {
    if (!repoUrl) return
    startResearchMutation(repoUrl)
  }

  return (
    <div className="flex-1 flex h-full overflow-hidden bg-background">

      {/* Left Panel: Collapsible Sidebar */}
      <div className={cn(
        "flex flex-col border-r transition-all duration-300 bg-muted/10 shrink-0",
        isSidebarOpen ? "w-[260px]" : "w-0 overflow-hidden border-none opacity-0"
      )}>
        <div className="h-14 border-b flex items-center px-4 font-semibold text-sm gap-2 shrink-0">
          <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center">
            <div className="w-3 h-3 border-2 border-primary rounded-full" />
          </div>
          CodeAtlas
        </div>
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Research Sessions
              </h3>
              <div className="space-y-1">
                <Button variant="ghost" className="w-full justify-start h-8 text-sm px-2 bg-muted/50 font-medium">
                  <span className="truncate">LangGraph</span>
                </Button>
                <Button variant="ghost" className="w-full justify-start h-8 text-sm px-2 text-muted-foreground">
                  <span className="truncate">PyRPC</span>
                </Button>
                <Button variant="ghost" className="w-full justify-start h-8 text-sm px-2 text-muted-foreground">
                  <span className="truncate">FastAPI</span>
                </Button>
              </div>
            </div>
          </div>
        </ScrollArea>
        <div className="p-4 border-t shrink-0">
          <Button variant="ghost" className="w-full justify-start h-9 text-sm px-2 text-muted-foreground">
            <Settings className="w-4 h-4 mr-2" />
            Workspace settings
          </Button>
        </div>
      </div>

      {/* Middle: Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full min-w-0 border-r border-border/50">
        <div className="h-14 border-b flex items-center px-4 gap-3 shrink-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
          <Button variant="ghost" size="icon" className="w-8 h-8 text-muted-foreground hover:text-foreground" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            {isSidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </Button>
          <div className="font-medium text-sm flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-muted-foreground" />
            Tree of Thought
          </div>
        </div>

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
                    onKeyDown={(e) => e.key === "Enter" && handleStartResearch()}
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
                  <Button variant="secondary" size="sm" className="h-8" onClick={() => setRepoUrl("https://github.com/encode/starlette")}>encode/starlette</Button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ChatPanel sessionId={sessionId!} />
        )}
      </div>

      {/* Right Side Panel: Activity & Sources */}
      {researchState === "researching" && (
        <div className="w-[420px] bg-background flex flex-col shrink-0">
          <Tabs defaultValue="activity" className="flex-1 flex flex-col h-full w-full">
            <div className="p-4 border-b flex justify-center shrink-0">
              <TabsList className="grid w-[280px] grid-cols-2 rounded-full h-9 bg-muted/50 p-1">
                <TabsTrigger value="activity" className="rounded-full text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm">
                  Activity
                </TabsTrigger>
                <TabsTrigger value="sources" className="rounded-full text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm">
                  {sourceCount} Sources
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="activity" className="flex-1 mt-0 overflow-hidden outline-none data-[state=active]:flex data-[state=active]:flex-col">
              <div className="p-4 border-b bg-muted/10 shrink-0">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium">Research Progress</h3>
                  {isComplete && (
                    <span className="text-xs text-green-500 flex items-center gap-1 font-medium bg-green-500/10 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3" />
                      Complete
                    </span>
                  )}
                  {isFailed && (
                    <span className="text-xs text-destructive flex items-center gap-1 font-medium bg-destructive/10 px-2 py-0.5 rounded-full">
                      <AlertCircle className="w-3 h-3" />
                      Failed
                    </span>
                  )}
                </div>
                <ResearchStatus sessionId={sessionId!} />
              </div>
              <ScrollArea className="flex-1">
                <div className="p-4">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                    Reasoning Tree
                  </h3>
                  <ReasoningTree sessionId={sessionId!} />
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="sources" className="flex-1 mt-0 overflow-hidden outline-none data-[state=active]:flex data-[state=active]:flex-col">
              <EvidencePanel sessionId={sessionId!} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}

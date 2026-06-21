"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ReasoningTree } from "./reasoning-tree"

export function ArchitecturePanel() {
  return (
    <Tabs defaultValue="report" className="flex-1 flex flex-col h-full w-full">
      <div className="px-4 py-2 border-b">
        <TabsList className="w-full justify-start h-auto p-1 bg-transparent border">
          <TabsTrigger value="report" className="text-xs">Report</TabsTrigger>
          <TabsTrigger value="architecture" className="text-xs">Architecture</TabsTrigger>
          <TabsTrigger value="reasoning" className="text-xs">Reasoning Tree</TabsTrigger>
          <TabsTrigger value="learning" className="text-xs">Learning Path</TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-6">
          <TabsContent value="report" className="mt-0 text-sm leading-relaxed text-muted-foreground">
            <h3 className="text-foreground font-medium text-lg mb-4">Architecture Report</h3>
            <p className="mb-4">
              CodeAtlas is built around a modern Next.js stack heavily reliant on server components and edge rendering for fast, distributed access to intelligence.
            </p>
            <p>
              The core orchestration is managed by LangGraph, enabling stateful, multi-agent reasoning over complex repository topologies.
            </p>
          </TabsContent>

          <TabsContent value="architecture" className="mt-0">
            <div className="aspect-video bg-muted/50 rounded-lg border border-dashed flex items-center justify-center flex-col text-muted-foreground">
              <span className="text-sm font-medium">LikeC4 Diagram Visualization</span>
              <span className="text-xs mt-1">Interactive architecture graph loads here</span>
            </div>
          </TabsContent>

          <TabsContent value="reasoning" className="mt-0">
            <ReasoningTree />
          </TabsContent>
          
          <TabsContent value="learning" className="mt-0 text-sm">
            <div className="space-y-4">
              <div className="p-4 rounded-lg border bg-card">
                <h4 className="font-medium mb-1 text-foreground">1. Core Concepts</h4>
                <p className="text-muted-foreground">Start by understanding the LangGraph state machine.</p>
              </div>
              <div className="p-4 rounded-lg border bg-card">
                <h4 className="font-medium mb-1 text-foreground">2. PyRPC Integration</h4>
                <p className="text-muted-foreground">Review how python sub-services connect to the Next.js router.</p>
              </div>
            </div>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  )
}

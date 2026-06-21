"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileCode2, ExternalLink } from "lucide-react"

export function EvidencePanel() {
  return (
    <Tabs defaultValue="evidence" className="flex-1 flex flex-col h-full w-full bg-sidebar/50">
      <div className="px-4 py-2 border-b bg-background">
        <TabsList className="w-full justify-start h-auto p-1 bg-transparent border">
          <TabsTrigger value="evidence" className="text-xs">Evidence</TabsTrigger>
          <TabsTrigger value="architecture" className="text-xs">Diagrams</TabsTrigger>
          <TabsTrigger value="report" className="text-xs">Full Report</TabsTrigger>
        </TabsList>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4">
          <TabsContent value="evidence" className="mt-0 space-y-4">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Cited References
            </div>
            
            <div className="space-y-2">
              <div className="group p-3 rounded-lg border bg-card hover:border-primary/50 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-sm font-medium mb-1.5">
                  <FileCode2 className="w-4 h-4 text-muted-foreground" />
                  <span>src/auth/jwt.py</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto opacity-0 group-hover:opacity-100" />
                </div>
                <div className="text-xs text-muted-foreground font-mono bg-muted/50 p-2 rounded border">
                  def verify_token(token: str): ...
                </div>
              </div>

              <div className="group p-3 rounded-lg border bg-card hover:border-primary/50 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-sm font-medium mb-1.5">
                  <FileCode2 className="w-4 h-4 text-muted-foreground" />
                  <span>src/server.py</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto opacity-0 group-hover:opacity-100" />
                </div>
                <div className="text-xs text-muted-foreground font-mono bg-muted/50 p-2 rounded border">
                  app.include_router(auth_router)
                </div>
              </div>

              <div className="group p-3 rounded-lg border bg-card hover:border-primary/50 transition-colors cursor-pointer">
                <div className="flex items-center gap-2 text-sm font-medium mb-1.5">
                  <FileCode2 className="w-4 h-4 text-muted-foreground" />
                  <span>docs/architecture.md</span>
                  <ExternalLink className="w-3 h-3 text-muted-foreground ml-auto opacity-0 group-hover:opacity-100" />
                </div>
                <div className="text-xs text-muted-foreground line-clamp-2">
                  The authentication layer is decoupled from the main application logic to allow for independent scaling.
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="architecture" className="mt-0">
            <div className="aspect-square bg-muted/30 rounded-lg border border-dashed flex items-center justify-center flex-col text-muted-foreground">
              <span className="text-sm font-medium">LikeC4 Diagram</span>
              <span className="text-xs mt-1 text-center px-4">Interactive architecture graph generated from reasoning branches</span>
            </div>
          </TabsContent>

          <TabsContent value="report" className="mt-0 text-sm leading-relaxed text-muted-foreground">
            <h3 className="text-foreground font-medium text-lg mb-4">Deep Research Report</h3>
            <p className="mb-4">
              The codebase employs a clear separation of concerns, isolating the core business logic from the authentication flow...
            </p>
          </TabsContent>
        </div>
      </ScrollArea>
    </Tabs>
  )
}

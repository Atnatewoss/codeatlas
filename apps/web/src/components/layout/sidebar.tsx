import { CodeXml, GitMerge, Hexagon, Search } from "lucide-react"
import Link from "next/link"

export function Sidebar() {
  return (
    <div className="w-64 border-r bg-sidebar flex flex-col h-full shrink-0">
      <div className="h-14 flex items-center px-4 border-b font-medium text-sm tracking-tight">
        <Hexagon className="w-4 h-4 mr-2 text-primary" />
        CodeAtlas
      </div>
      
      <div className="p-4 flex-1 overflow-auto">
        <div className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wider">
          Research Sessions
        </div>
        
        <div className="space-y-1">
          <Link href="#" className="flex flex-col px-3 py-2 rounded-md bg-accent text-accent-foreground text-sm">
            <div className="flex items-center font-medium">
              <Search className="w-3.5 h-3.5 mr-2" />
              LangGraph
            </div>
            <div className="text-xs text-muted-foreground mt-1 ml-5.5 truncate">
              langchain-ai/langgraph
            </div>
          </Link>
          
          <Link href="#" className="flex flex-col px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground text-sm text-muted-foreground transition-colors">
            <div className="flex items-center font-medium">
              <CodeXml className="w-3.5 h-3.5 mr-2" />
              PyRPC
            </div>
            <div className="text-xs text-muted-foreground mt-1 ml-5.5 truncate">
              pyrpc/pyrpc
            </div>
          </Link>

          <Link href="#" className="flex flex-col px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground text-sm text-muted-foreground transition-colors">
            <div className="flex items-center font-medium">
              <GitMerge className="w-3.5 h-3.5 mr-2" />
              FastAPI
            </div>
            <div className="text-xs text-muted-foreground mt-1 ml-5.5 truncate">
              fastapi/fastapi
            </div>
          </Link>
        </div>
      </div>
      
      <div className="p-4 border-t text-xs text-muted-foreground">
        Workspace settings
      </div>
    </div>
  )
}

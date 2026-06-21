import { cn } from "@/lib/utils"
import { FileCode2 } from "lucide-react"

export function MessageComponent({ role, content, citations }: { role: "user" | "assistant", content: string, citations?: string[] }) {
  return (
    <div className={cn(
      "flex w-full max-w-3xl mx-auto space-x-4",
      role === "user" ? "justify-end" : "justify-start"
    )}>
      {role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <div className="w-2 h-2 rounded-full bg-primary" />
        </div>
      )}
      
      <div className={cn(
        "px-4 py-3 rounded-2xl max-w-[85%] text-sm leading-relaxed",
        role === "user" 
          ? "bg-primary text-primary-foreground" 
          : "bg-muted"
      )}>
        <div className="whitespace-pre-wrap">{content}</div>
        
        {citations && citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/50">
            <div className="text-xs text-muted-foreground font-medium mb-2">References:</div>
            <div className="flex flex-wrap gap-2">
              {citations.map((citation, i) => (
                <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-background/50 border border-border/50 text-xs text-muted-foreground cursor-pointer hover:bg-background hover:text-foreground transition-colors">
                  <FileCode2 className="w-3 h-3" />
                  {citation}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

import { cn } from "@/lib/utils"

export function MessageComponent({ role, content }: { role: "user" | "assistant", content: string }) {
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
        {content}
      </div>
    </div>
  )
}

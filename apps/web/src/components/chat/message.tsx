import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkBreaks from "remark-breaks"
import { cn } from "@/lib/utils"
import type { ReactNode } from "react"
import { MermaidBlock } from "./mermaid-block"

export function MessageComponent({ role, content, citations, children }: { role: "user" | "assistant", content?: string, citations?: string[], children?: ReactNode }) {
  return (
    <div className={cn(
      "flex w-full",
      role === "user" ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "text-sm leading-relaxed",
        role === "user"
          ? "bg-muted/40 rounded-2xl px-3 py-2 max-w-[75%] text-foreground"
          : "w-full px-0 py-2 text-foreground"
      )}>
        {role === "assistant" && content ? (
          <Markdown
            remarkPlugins={[remarkGfm, remarkBreaks]}
            components={{
              p({ children, ...props }) {
                return <p className="mb-2 last:mb-0" {...props}>{children}</p>
              },
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || "")
                if (match && match[1] === "mermaid") {
                  return <MermaidBlock content={String(children).replace(/\n$/, "")} />
                }
                return <code className={className} {...props}>{children}</code>
              },
            }}
          >
            {content}
          </Markdown>
        ) : (
          <div className="whitespace-pre-wrap">
            {children || content}
          </div>
        )}

        {citations && citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/50">
            <div className="text-xs text-muted-foreground font-medium mb-2">References</div>
            <div className="space-y-1">
              {citations.map((citation, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                  <span className="shrink-0 w-4 text-right font-medium tabular-nums">[{i + 1}]</span>
                  <span>{citation}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

"use client"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ArrowUp } from "lucide-react"

export function Composer() {
  return (
    <div className="relative max-w-3xl mx-auto flex items-end gap-2 bg-muted/50 p-2 rounded-xl border">
      <Textarea
        placeholder="Ask about this repository..."
        className="min-h-[44px] max-h-32 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0 p-3 py-2.5"
        rows={1}
      />
      <Button size="icon" className="h-9 w-9 rounded-lg shrink-0">
        <ArrowUp className="w-4 h-4" />
      </Button>
    </div>
  )
}

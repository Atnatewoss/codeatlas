"use client"

import { useState, useRef, KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ArrowUp } from "lucide-react"

export function Composer({
  onSend,
  disabled,
}: {
  onSend?: (content: string) => void
  disabled?: boolean
}) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (!value.trim() || disabled) return
    onSend?.(value.trim())
    setValue("")
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = "auto"
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`
  }

  return (
    <div className="relative max-w-3xl mx-auto flex items-end gap-2 bg-muted/50 p-2 rounded-xl border">
      <Textarea
        ref={textareaRef}
        placeholder="Ask about this repository... (Enter to send, Shift+Enter for newline)"
        className="min-h-[44px] max-h-32 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0 p-3 py-2.5 text-sm"
        rows={1}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
      />
      <Button
        size="icon"
        className="h-9 w-9 rounded-lg shrink-0"
        onClick={handleSend}
        disabled={!value.trim() || disabled}
      >
        <ArrowUp className="w-4 h-4" />
      </Button>
    </div>
  )
}

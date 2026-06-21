"use client"

import { useState, useRef, useEffect } from "react"
import { Composer } from "./composer"
import { MessageComponent } from "./message"
import { sendChatMessage } from "@/lib/api"
import { useMutation } from "@tanstack/react-query"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: string[]
}

export function ChatPanel({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Research is running. Ask me anything about this repository - architecture, runtime flow, design patterns, or contributor onboarding.",
      citations: []
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const { mutate: sendMessage, isPending: isLoading } = useMutation({
    mutationFn: (history: { role: string; content: string }[]) => sendChatMessage(sessionId, history),
    onSuccess: (res) => {
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.content,
        citations: res.citations ?? [],
      }
      setMessages((prev) => [...prev, assistantMsg])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I couldn't reach the research server. Make sure the API is running on port 8000.",
        },
      ])
    }
  })

  const handleSend = (content: string) => {
    if (!content.trim() || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    }

    setMessages((prev) => [...prev, userMsg])

    const history = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }))

    sendMessage(history)
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <MessageComponent
            key={msg.id}
            role={msg.role}
            content={msg.content}
            citations={msg.citations}
          />
        ))}
        {isLoading && (
          <div className="flex items-center gap-3 max-w-3xl mx-auto">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            </div>
            <div className="flex gap-1 py-3">
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <Composer onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}

"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Composer } from "@/components/chat/composer"
import { MessageComponent } from "@/components/chat/message"
import { ThinkingSection } from "@/components/chat/thinking-section"
import { sendChatMessage, startChatResearch } from "@/lib/api"
import { useChatStream } from "@/hooks/use-chat-stream"
import { useMutation } from "@tanstack/react-query"
import { MessageSquare, Network } from "lucide-react"
import { MermaidBlock } from "@/components/chat/mermaid-block"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: string[]
}

export function ChatPanel({
  sessionId,
  repoPath,
}: {
  sessionId: string
  repoPath?: string
}) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "I'm starting the deep research process. I'll build a mental model of this repository and report back shortly. Feel free to ask me questions while I work!",
      citations: [],
    },
  ])
  const [chatSessionId, setChatSessionId] = useState<string | null>(null)

  const { mutate: startResearch, isPending: isResearchPending } = useMutation({
    mutationFn: (payload: { repoPath: string; query: string }) =>
      startChatResearch(payload.repoPath, payload.query, 3, 2, 5),
    onSuccess: (res) => setChatSessionId(res.session_id),
  })

  const { mutate: sendSyncMessage, isPending: isSyncPending } = useMutation({
    mutationFn: (history: { role: string; content: string }[]) =>
      sendChatMessage(sessionId, history),
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
          content:
            "Sorry, I couldn't reach the research server. Make sure the API is running on port 8000.",
        },
      ])
    },
  })

  const onResearchComplete = useCallback(() => {
    setChatSessionId(null)
  }, [])

  const { state: chatState } = useChatStream(chatSessionId, { onComplete: onResearchComplete })

  const isResearching = chatSessionId !== null && !chatState.isComplete

  // Keep thinking section visible after completion so the final time is shown
  const showThinking = chatSessionId !== null || (chatState.isComplete && chatState.thoughts.length > 0)
  // Timer only ticks while research is actively running
  const timerActive = chatSessionId !== null && !chatState.isComplete
  const isLoading = isResearchPending || isSyncPending || isResearching

  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!timerActive) {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
      return
    }
    const start = Date.now()
    setElapsed(0)
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 200)
    return () => { if (timerRef.current) clearInterval(timerRef.current); timerRef.current = null }
  }, [timerActive])

  const [thoughtsExpanded, setThoughtsExpanded] = useState(false)

  // Auto-open thinking while research runs, auto-close when answer arrives
  useEffect(() => {
    if (chatSessionId !== null && !chatState.isComplete) {
      setThoughtsExpanded(true)
    }
    if (chatState.isComplete) {
      setThoughtsExpanded(false)
    }
  }, [chatSessionId, chatState.isComplete])

  const bottomRef = useRef<HTMLDivElement>(null)
  const prevMsgCount = useRef(messages.length)

  // Scroll to bottom only when user sends a new message
  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
    prevMsgCount.current = messages.length
  }, [messages.length])

  const handleSend = useCallback(
    (content: string) => {
      if (!content.trim() || isLoading) return

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content,
      }
      setMessages((prev) => [...prev, userMsg])

      if (repoPath) {
        startResearch(
          { repoPath, query: content },
          {
            onError: () => {
              sendSyncMessage([...messages, userMsg].map((m) => ({
                role: m.role,
                content: m.content,
              })))
            },
          }
        )
      } else {
        sendSyncMessage([...messages, userMsg].map((m) => ({
          role: m.role,
          content: m.content,
        })))
      }
    },
    [isLoading, repoPath, messages, startResearch, sendSyncMessage]
  )

  return (
    <div className="flex-1 flex flex-col h-full bg-gradient-to-b from-background to-muted/10">
      <div className="flex-1 overflow-y-auto scrollbar-theme">
        <div className="max-w-2xl mx-auto px-4 md:px-6 space-y-4 py-4 md:py-6">
          {/* Messages: only user messages + first welcome */}
          {messages.map((msg, idx) => {
            if (msg.role === "assistant" && idx !== 0) return null
            return (
              <MessageComponent
                key={msg.id}
                role={msg.role}
                content={msg.content}
                citations={msg.citations}
              />
            )
          })}

          {/* Sync pending indicator */}
          {isSyncPending && !chatSessionId && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              </div>
              <div className="flex gap-1 py-3 bg-muted/30 px-3 rounded-2xl border">
                <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-muted-foreground/50 rounded-full animate-bounce" />
              </div>
            </div>
          )}

          {/* Single thinking section — visible as soon as research starts */}
          {showThinking && (
            <ThinkingSection
              isResearching={isResearching}
              chatState={chatState}
              thoughtsExpanded={thoughtsExpanded}
              onToggleExpanded={() => setThoughtsExpanded((v) => !v)}
              elapsed={elapsed}
            />
          )}

          {/* Live answer streaming */}
          {chatState.answer && !chatState.isComplete && (
            <div className="bg-card border rounded-2xl p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-4 h-4 text-primary" />
                <span className="text-xs font-medium text-muted-foreground">Answer</span>
              </div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {chatState.answer}
                <span className="inline-block w-1 h-4 bg-primary ml-0.5 animate-pulse" />
              </p>
            </div>
          )}

          {/* Final answer below thinking section — architecture diagram shown inline above answer */}
          {chatState.answer && chatState.isComplete && (
            <div>
              {chatState.graphDiagram && (
                <div className="mb-3 bg-card border rounded-2xl p-3 shadow-sm">
                  <div className="flex items-center gap-1.5 mb-2 text-[10px] text-muted-foreground/50">
                    <Network className="w-3 h-3" />
                    <span>Architecture diagram</span>
                    <span className="text-[9px] text-muted-foreground/30">({chatState.graphDiagram.split('\n').filter(l => l.includes('-->')).length} call edges)</span>
                  </div>
                  <MermaidBlock content={chatState.graphDiagram.replace(/^```mermaid\n?|```$/g, '')} />
                </div>
              )}
              <MessageComponent
                role="assistant"
                content={chatState.answer || "I explored the codebase but couldn't find specific information about that query."}
                citations={chatState.citations}
              />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="p-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-2xl mx-auto">
          <Composer onSend={handleSend} disabled={isLoading} />
        </div>
      </div>
    </div>
  )
}

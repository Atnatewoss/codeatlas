"use client"

import { useState, useEffect, useRef } from "react"
import type { ChatSSEEvent, ChatStreamState } from "@/lib/api"
import { getApiBaseUrl } from "@/lib/api-base"

const HTTP_BASE = getApiBaseUrl()

function getWsBaseUrl(): string {
  const base = HTTP_BASE
  if (base.startsWith("http")) {
    return base.replace(/^http/, "ws")
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
    return `${proto}//${window.location.host}${base}`
  }
  return `ws://localhost:8000${base}`
}

const WS_BASE = getWsBaseUrl()

const EMPTY_STATE: ChatStreamState = {
  thoughts: [],
  bestIds: [],
  rejectedIds: [],
  uncertainties: [],
  depth: 0,
  maxDepth: 3,
  answer: "",
  isComplete: false,
  isError: false,
  cloneProgress: "",
  phase: "",
  rejectedBranches: "",
  uncertaintiesSummary: "",
  graphStatus: "",
  graphDiagram: "",
  citations: [],
}

interface UseChatStreamOptions {
  onComplete?: (answer: string, citations?: string[]) => void
}

export function useChatStream(sessionId: string | null, options?: UseChatStreamOptions) {
  const [state, setState] = useState<ChatStreamState>(EMPTY_STATE)
  const wsRef = useRef<WebSocket | null>(null)
  const optionsRef = useRef(options)
  optionsRef.current = options

  function handleEvent(parsed: ChatSSEEvent) {
    const evt = parsed.event
    const data = parsed.data

    switch (evt) {
      case "heartbeat":
        break

      case "research_started":
        setState((prev) => ({
          ...prev,
          phase: "initializing",
        }))
        break

      case "clone_progress":
        setState((prev) => ({
          ...prev,
          phase: "cloning",
          cloneProgress: (data.message as string) || "",
        }))
        break

      case "thought_generated":
        setState((prev) => ({
          ...prev,
          thoughts: [
            ...prev.thoughts,
            {
              id: data.id as string,
              parent_id: data.parent_id as string | undefined,
              depth: data.depth as number | undefined,
              description: data.description as string,
              hypothesis: data.hypothesis as string | undefined,
              expected_evidence: data.expected_evidence as string | undefined,
              tool: data.tool as string,
              target: data.target as string,
            },
          ],
        }))
        break

      case "thought_executing":
        setState((prev) => ({
          ...prev,
          thoughts: prev.thoughts.map((t) =>
            t.id === data.id
              ? { ...t, tool: data.tool as string, target: data.target as string }
              : t
          ),
        }))
        break

      case "thought_result":
        setState((prev) => ({
          ...prev,
          thoughts: prev.thoughts.map((t) =>
            t.id === data.id
              ? { ...t, outcome: data.outcome as string }
              : t
          ),
        }))
        break

      case "thought_evaluated":
        setState((prev) => ({
          ...prev,
          thoughts: prev.thoughts.map((t) =>
            t.id === data.id
              ? {
                  ...t,
                  score: data.score as number,
                  relevance: data.relevance as number | undefined,
                  evidence_strength: data.evidence_strength as number | undefined,
                  source_diversity: data.source_diversity as number | undefined,
                  reasoning: data.reasoning as string | undefined,
                }
              : t
          ),
        }))
        break

      case "thought_pruned":
        setState((prev) => ({
          ...prev,
          thoughts: prev.thoughts.map((t) =>
            t.id === data.id
              ? {
                  ...t,
                  is_pruned: true,
                  prune_reason: data.reasoning as string | undefined,
                  prune_threshold: data.threshold as number | undefined,
                }
              : t
          ),
        }))
        break

      case "state":
        setState((prev) => ({
          ...prev,
          phase: (data.phase as string) || prev.phase,
          depth: (data.depth as number) ?? prev.depth,
          rejectedIds: (data.rejected_ids as string[]) ?? prev.rejectedIds,
        }))
        break

      case "citations":
        setState((prev) => ({
          ...prev,
          citations: (data.citations as string[]) || [],
        }))
        break

      case "graph_diagram":
        setState((prev) => ({
          ...prev,
          graphDiagram: (data.diagram as string) || "",
        }))
        break

      case "graph_status":
        setState((prev) => ({
          ...prev,
          graphStatus: (data.status as string) || "",
          phase: data.status === "building" ? "building_graph" : prev.phase,
        }))
        break

      case "rejected_branches":
        setState((prev) => ({
          ...prev,
          rejectedBranches: (data.summary as string) || "",
        }))
        break

      case "uncertainties":
        setState((prev) => ({
          ...prev,
          uncertaintiesSummary: (data.summary as string) || "",
        }))
        break

      case "answer_chunk":
        setState((prev) => ({
          ...prev,
          answer: data.answer as string,
        }))
        break

      case "complete":
        const answer = (data.answer as string) || ""
        const citations = (data.citations as string[]) || []
        setState((prev) => ({
          ...prev,
          answer: answer || prev.answer,
          isComplete: true,
          citations,
        }))
        optionsRef.current?.onComplete?.(answer, citations)
        break

      case "error":
        setState((prev) => ({
          ...prev,
          isError: true,
          isComplete: true,
        }))
        break
    }
  }

  useEffect(() => {
    if (!sessionId) return

    setState(EMPTY_STATE)

    if (wsRef.current) {
      wsRef.current.close()
    }

    const url = `${WS_BASE}/chat/ws/${sessionId}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data) as ChatSSEEvent
        handleEvent(parsed)
        if (parsed.event === "complete" || parsed.event === "error") {
          ws.close()
        }
      } catch {
        // Ignore parse errors
      }
    }

    ws.onerror = () => {
    }

    ws.onclose = () => {
      // WebSocket closed
    }

    return () => {
      ws.close()
    }
  }, [sessionId])

  return { state }
}
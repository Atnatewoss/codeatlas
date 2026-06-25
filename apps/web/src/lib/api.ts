import { getApiBaseUrl } from "@/lib/api-base"

const API_BASE_URL = getApiBaseUrl()

export interface ChatThought {
  id: string
  parent_id?: string
  depth?: number
  description: string
  hypothesis?: string
  expected_evidence?: string
  tool?: string
  target?: string
  score?: number
  relevance?: number
  evidence_strength?: number
  source_diversity?: number
  reasoning?: string
  outcome?: string
  is_pruned?: boolean
  prune_reason?: string
  prune_threshold?: number
}

export interface ChatStreamState {
  thoughts: ChatThought[]
  bestIds: string[]
  rejectedIds: string[]
  uncertainties: string[]
  depth: number
  maxDepth: number
  answer: string
  isComplete: boolean
  isError: boolean
  cloneProgress: string
  phase: string
  rejectedBranches: string
  uncertaintiesSummary: string
  graphStatus: string
  graphDiagram: string
  citations: string[]
}

export interface ChatSSEEvent {
  event: string
  data: Record<string, unknown>
  timestamp?: string
}

export interface ChatResponse {
  role: string
  content: string
  citations: string[]
}

export interface DeepResearchResponse {
  session_id: string
  repo_path: string
}

export async function startChatResearch(
  repoPath: string,
  query: string,
  maxDepth: number = 3,
  maxChildren: number = 2,
  keepTopK: number = 5
): Promise<DeepResearchResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_path: repoPath, query,
      max_depth: maxDepth,
      max_children: maxChildren,
      keep_top_k: keepTopK,
    }),
  })
  if (!res.ok) throw new Error("Failed to start chat research")
  return res.json()
}

export async function sendChatMessage(
  sessionId: string,
  messages: { role: string; content: string }[]
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, messages }),
  })
  if (!res.ok) throw new Error("Failed to send chat")
  return res.json()
}

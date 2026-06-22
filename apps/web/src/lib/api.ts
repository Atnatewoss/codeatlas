const API_BASE_URL = "http://localhost:8000/api"

export interface Evidence {
  filepath: string
  snippet: string
  explanation: string
}

export interface Finding {
  text: string
  confidence: number
  evidence: Evidence[]
}

export interface BranchStatus {
  status: string
  findings: Finding[]
  error: string | null
}

export interface ResearchBranches {
  structure: BranchStatus
  runtime: BranchStatus
  design: BranchStatus
  onboarding: BranchStatus
  risk: BranchStatus
}

export interface EvaluationResult {
  contradictions: { finding_a: string; finding_b: string; reason: string }[]
  agreements: { text: string; branches: string[]; confidence: number }[]
  low_confidence: { text: string; confidence: number }[]
  investigation_needed: boolean
}

export interface SynthesisResult {
  summary: string
  architecture_overview: string
  key_insights: { text: string; confidence: number; branch: string }[]
  learning_path: { file: string; reason: string }[]
  risk_summary: string
}

export interface ResearchStatusResponse {
  session_id: string
  repo_url: string
  status: "pending" | "running" | "complete" | "failed"
  branches: ResearchBranches
  evaluation: EvaluationResult | null
  synthesis: SynthesisResult | null
  investigation_round: number
  investigation_log: string[]
  started_at: string | null
  completed_at: string | null
}

export interface StartResearchResponse {
  session_id: string
  status_url: string
  stream_url: string
}

export interface ChatResponse {
  role: string
  content: string
  citations: string[]
}

export async function startResearch(repoUrl: string): Promise<StartResearchResponse> {
  const res = await fetch(`${API_BASE_URL}/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  })
  if (!res.ok) throw new Error("Failed to start research")
  return res.json()
}

export async function getResearchStatus(sessionId: string): Promise<ResearchStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/research/status/${sessionId}`)
  if (!res.ok) throw new Error("Failed to get status")
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

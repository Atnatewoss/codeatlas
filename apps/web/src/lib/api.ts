const API_BASE_URL = "http://localhost:8000/api"

export async function startResearch(repoUrl: string) {
  const res = await fetch(`${API_BASE_URL}/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl })
  })
  if (!res.ok) throw new Error("Failed to start research")
  return res.json() // { session_id: "..." }
}

export async function getResearchStatus(sessionId: string) {
  const res = await fetch(`${API_BASE_URL}/research/status/${sessionId}`)
  if (!res.ok) throw new Error("Failed to get status")
  return res.json()
}

export async function sendChatMessage(sessionId: string, messages: { role: string, content: string }[]) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, messages })
  })
  if (!res.ok) throw new Error("Failed to send chat")
  return res.json() // { role: "...", content: "...", citations: [...] }
}

"use client"

import { useState } from "react"
import { Composer } from "./composer"
import { MessageComponent } from "./message"

export function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      id: "1",
      role: "assistant",
      content: "I've analyzed the repository structure. The application employs a clear separation of concerns, isolating the core business logic from the authentication flow.\n\nAuthentication is implemented using JWT tokens and is decoupled to allow for independent scaling. What specific aspect of the architecture would you like me to explain next?",
      citations: ["src/auth/jwt.py", "src/server.py", "docs/architecture.md"]
    }
  ])

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <MessageComponent key={msg.id} role={msg.role as any} content={msg.content} citations={msg.citations} />
        ))}
      </div>
      <div className="p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <Composer />
      </div>
    </div>
  )
}

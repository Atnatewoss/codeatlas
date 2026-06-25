"use client"

import { useState, useEffect } from "react"

export function TypewriterText({ text, speed = 30 }: { text: string; speed?: number }) {
  const [displayed, setDisplayed] = useState("")
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (done) return
    let i = 0
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) { clearInterval(timer); setDone(true) }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed, done])

  return (
    <span>
      {displayed}
      {!done && <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse" />}
    </span>
  )
}

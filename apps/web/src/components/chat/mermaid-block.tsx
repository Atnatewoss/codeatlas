"use client"

import { useEffect, useRef, useState } from "react"
import mermaid from "mermaid"

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
})

export function MermaidBlock({ content }: { content: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [zoomLevel, setZoomLevel] = useState(1)

  useEffect(() => {
    if (ref.current) {
      ref.current.removeAttribute("data-processed")
      mermaid
        .run({
          nodes: [ref.current],
          suppressErrors: true,
        })
        .then(() => {
          const svg = ref.current?.querySelector("svg")
          if (svg) {
            svg.removeAttribute("width")
            svg.removeAttribute("height")
            svg.style.maxWidth = "100%"
          }
        })
        .catch(() => {})
    }
  }, [content])

  return (
    <div className="my-3">
      <div className="flex items-center gap-1 mb-1">
        <button
          onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
          className="text-[10px] px-1.5 py-0.5 rounded bg-muted/30 hover:bg-muted/60 text-muted-foreground/60 transition-colors"
          title="Zoom out"
        >
          -
        </button>
        <span className="text-[10px] text-muted-foreground/40 tabular-nums">{Math.round(zoomLevel * 100)}%</span>
        <button
          onClick={() => setZoomLevel((z) => Math.min(3, z + 0.25))}
          className="text-[10px] px-1.5 py-0.5 rounded bg-muted/30 hover:bg-muted/60 text-muted-foreground/60 transition-colors"
          title="Zoom in"
        >
          +
        </button>
        <button
          onClick={() => setZoomLevel(1)}
          className="text-[10px] px-1.5 py-0.5 rounded bg-muted/30 hover:bg-muted/60 text-muted-foreground/40 transition-colors ml-1"
          title="Reset zoom"
        >
          Reset
        </button>
      </div>
      <div className="overflow-x-auto overflow-y-hidden scrollbar-theme">
        <div
          className="mermaid"
          ref={ref}
          style={{
            transform: `scale(${zoomLevel})`,
            transformOrigin: "top left",
            transition: "transform 0.15s ease",
          }}
        >
          {content}
        </div>
      </div>
    </div>
  )
}

"use client"

import dynamic from "next/dynamic"

const HomeContent = dynamic(() => import("./home").then((m) => m.HomeContent), {
  ssr: false,
})

export default function Page() {
  return <HomeContent />
}

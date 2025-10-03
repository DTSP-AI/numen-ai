"use client"

import { LiveKitRoom } from "@livekit/components-react"
import "@livekit/components-styles"

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="chat-layout">
      {children}
    </div>
  )
}

"use client"

import { useSearchParams } from "next/navigation"
import { AgentBuilder } from "@/components/AgentBuilder"

export default function CreateAgentPage() {
  const searchParams = useSearchParams()
  const userId = searchParams.get("userId") || "00000000-0000-0000-0000-000000000001"
  const sessionId = searchParams.get("sessionId") || undefined

  return <AgentBuilder userId={userId} sessionId={sessionId} />
}

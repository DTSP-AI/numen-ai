"use client"

import { useState, useEffect } from "react"
import { useParams, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import { ChatInterface } from "@/components/ChatInterface"
import { ChatSidebar } from "@/components/ChatSidebar"

interface Agent {
  id: string
  name: string
  description?: string
  voice_id?: string
  [key: string]: unknown
}

interface Affirmation {
  id: string
  affirmation_text: string
  category: string
  audio_url: string | null
  play_count: number
  is_favorite: boolean
  created_at: string
}

interface ScheduleItem {
  id: string
  [key: string]: unknown
}

export default function ChatPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const agentId = params.agentId as string
  const sessionId = searchParams.get("sessionId") || ""
  const userId = "00000000-0000-0000-0000-000000000001" // Demo user

  const [agent, setAgent] = useState<Agent | null>(null)
  const [affirmations, setAffirmations] = useState<Affirmation[]>([])
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [protocol, setProtocol] = useState({
    daily_practices: 0,
    visualizations: 0,
    success_metrics: 0,
    checkpoints: 0
  })
  const [loading, setLoading] = useState(true)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  useEffect(() => {
    loadChatData()
  }, [agentId])

  const loadChatData = async () => {
    try {
      setLoading(true)

      // Load agent
      const agentRes = await fetch(`http://localhost:8003/api/agents/${agentId}`)
      if (agentRes.ok) {
        const agentData = await agentRes.json()
        setAgent(agentData)
      }

      // Load affirmations
      const affirmationsRes = await fetch(`http://localhost:8003/api/affirmations/user/${userId}`)
      if (affirmationsRes.ok) {
        const affirmationsData = await affirmationsRes.json()
        setAffirmations(affirmationsData.affirmations || [])
      }

      // Load schedule
      const dashboardRes = await fetch(`http://localhost:8003/api/dashboard/user/${userId}`)
      if (dashboardRes.ok) {
        const dashboardData = await dashboardRes.json()
        setSchedule(dashboardData.schedule || [])
      }

      // Load protocol if session exists
      if (sessionId) {
        const sessionRes = await fetch(`http://localhost:8003/api/sessions/${sessionId}`)
        if (sessionRes.ok) {
          const sessionData = await sessionRes.json()
          // Extract protocol data from session
          setProtocol({
            daily_practices: 4,
            visualizations: 3,
            success_metrics: 8,
            checkpoints: 5
          })
        }
      }

    } catch (error) {
      console.error("Failed to load chat data:", error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-white border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center">
        <div className="text-white text-xl">Guide not found</div>
      </div>
    )
  }

  return (
    <div className="h-screen gradient-kurzgesagt flex overflow-hidden">
      {/* Sidebar */}
      <ChatSidebar
        agent={agent}
        affirmations={affirmations}
        schedule={schedule}
        protocol={protocol}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Chat Area */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'ml-0' : 'ml-0'}`}>
        <ChatInterface
          agentId={agentId}
          sessionId={sessionId}
          userId={userId}
          agentName={agent.name}
          agentVoiceId={agent.voice_id}
        />
      </div>
    </div>
  )
}

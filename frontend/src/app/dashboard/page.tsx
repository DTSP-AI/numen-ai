"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { AffirmationCard } from "@/components/AffirmationCard"
import { ScriptPlayer } from "@/components/ScriptPlayer"
import { ScheduleCalendar } from "@/components/ScheduleCalendar"
import { AgentCard } from "@/components/AgentCard"
import { HorizontalTabs } from "@/components/HorizontalTabs"
import { DashboardStatCard } from "@/components/DashboardStatCard"
import { DiscoveryQuestions } from "@/components/DiscoveryQuestions"
import { ProtocolSummary } from "@/components/ProtocolSummary"

interface Agent {
  id: string
  name: string
  [key: string]: unknown
}

interface ScheduleItem {
  id: string
  [key: string]: unknown
}

interface Thread {
  id: string
  [key: string]: unknown
}

interface DashboardData {
  summary: {
    total_agents: number
    total_affirmations: number
    total_scripts: number
    upcoming_sessions: number
  }
  agents: Agent[]
  affirmations_by_category: Record<string, { total: number; with_audio: number }>
  schedule: ScheduleItem[]
  recent_threads: Thread[]
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

interface HypnosisScript {
  id: string
  title: string
  script_text: string
  duration_minutes: number
  audio_url: string | null
  focus_area: string
  play_count: number
  created_at: string
}

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const agentId = searchParams.get("agentId")
  const sessionId = searchParams.get("sessionId")
  const success = searchParams.get("success") === "true"

  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [affirmations, setAffirmations] = useState<Affirmation[]>([])
  const [scripts, setScripts] = useState<HypnosisScript[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"overview" | "affirmations" | "scripts" | "schedule">("overview")
  const [showMeetAgent, setShowMeetAgent] = useState(success)  // Phase 4: Show intro on first visit
  const [showDiscovery, setShowDiscovery] = useState(false)  // Phase 2: Discovery questions

  // Demo user ID (in production, get from auth context)
  const userId = "00000000-0000-0000-0000-000000000001"

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)

      // Load dashboard summary
      const dashboardRes = await fetch(`http://localhost:8000/api/dashboard/user/${userId}`)
      const dashboardData = await dashboardRes.json()
      setDashboardData(dashboardData)

      // Load affirmations
      const affirmationsRes = await fetch(`http://localhost:8000/api/affirmations/user/${userId}`)
      const affirmationsData = await affirmationsRes.json()
      setAffirmations(affirmationsData.affirmations || [])

      // Load scripts
      const scriptsRes = await fetch(`http://localhost:8000/api/scripts/user/${userId}`)
      const scriptsData = await scriptsRes.json()
      setScripts(scriptsData.scripts || [])

    } catch (error) {
      console.error("Failed to load dashboard:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleDiscoveryComplete = () => {
    setShowDiscovery(false)
    setShowMeetAgent(false)
    loadDashboard() // Reload to show generated affirmations
  }

  // Show discovery questions flow
  if (showDiscovery && agentId && sessionId) {
    return (
      <DiscoveryQuestions
        agentId={agentId}
        sessionId={sessionId}
        userId={userId}
        onComplete={handleDiscoveryComplete}
      />
    )
  }

  if (loading || !dashboardData) {
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

  // Phase 4: Meet Your Agent intro screen
  if (showMeetAgent && agentId && dashboardData?.agents?.length > 0) {
    const agent = dashboardData.agents.find(a => a.id === agentId) || dashboardData.agents[0]

    return (
      <div className="min-h-screen gradient-kurzgesagt p-6 flex items-center justify-center">
        <div className="max-w-3xl w-full">
          {/* Success Banner */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center mb-8"
          >
            <div className="text-6xl mb-4">✨</div>
            <h1 className="text-5xl font-bold text-white mb-3">Agent Created!</h1>
            <p className="text-xl text-white/80">Your personalized guide is ready</p>
          </motion.div>

          {/* Meet Your Agent Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-8 rounded-3xl"
          >
            <h2 className="text-3xl font-bold text-white mb-6">Meet {agent.name}</h2>

            {/* Capabilities */}
            <div className="bg-white/10 rounded-2xl p-6 mb-8">
              <h3 className="text-xl font-semibold text-white mb-4">What I Can Help You With:</h3>
              <ul className="space-y-3">
                <li className="flex items-start gap-3 text-white/90">
                  <svg className="w-6 h-6 text-kurzgesagt-yellow flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Create personalized affirmations aligned with your goals</span>
                </li>
                <li className="flex items-start gap-3 text-white/90">
                  <svg className="w-6 h-6 text-kurzgesagt-yellow flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Guide you through manifestation practices</span>
                </li>
                <li className="flex items-start gap-3 text-white/90">
                  <svg className="w-6 h-6 text-kurzgesagt-yellow flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Track your transformation journey</span>
                </li>
              </ul>
            </div>

            {/* CTA Button */}
            <Button
              onClick={() => setShowDiscovery(true)}
              className="w-full bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white text-xl py-6 rounded-xl shadow-lg hover:shadow-2xl transition-all font-semibold"
            >
              Generate My Plan
            </Button>

            {/* Skip link */}
            <button
              onClick={() => setShowMeetAgent(false)}
              className="w-full mt-4 text-white/60 hover:text-white transition-colors"
            >
              Skip to Dashboard →
            </button>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt">
      <div className="container mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-5xl font-bold text-white mb-4">Your Manifestation Dashboard</h1>
          <p className="text-xl text-white/80">Track your progress and access your personalized content</p>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div onClick={() => setActiveTab("overview")}>
            <DashboardStatCard
              label="Active Agents"
              value={dashboardData?.summary?.total_agents || 0}
              color="#FFD33D"
              delay={0.1}
            />
          </div>

          <div onClick={() => setActiveTab("affirmations")}>
            <DashboardStatCard
              label="Affirmations"
              value={dashboardData?.summary?.total_affirmations || 0}
              color="#00D9C0"
              delay={0.15}
            />
          </div>

          <div onClick={() => setActiveTab("scripts")}>
            <DashboardStatCard
              label="Hypnosis Scripts"
              value={dashboardData?.summary?.total_scripts || 0}
              color="#7C3AED"
              delay={0.2}
            />
          </div>

          <div onClick={() => setActiveTab("schedule")}>
            <DashboardStatCard
              label="Upcoming Sessions"
              value={dashboardData?.summary?.upcoming_sessions || 0}
              color="#FF6B6B"
              delay={0.25}
            />
          </div>
        </div>

        {/* Tab Navigation */}
        <HorizontalTabs
          tabs={[
            { id: "overview", label: "Overview" },
            { id: "affirmations", label: "Affirmations" },
            { id: "scripts", label: "Scripts" },
            { id: "schedule", label: "Schedule" },
          ]}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as "overview" | "affirmations" | "scripts" | "schedule")}
          className="mb-8"
        />

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "overview" && (
            <div className="space-y-8">
              {/* Protocol Summary (if exists) */}
              {sessionId && dashboardData?.summary?.total_affirmations > 0 && (
                <section>
                  <ProtocolSummary
                    protocol={{
                      daily_practices: 4,
                      visualizations: 3,
                      success_metrics: 8,
                      checkpoints: 5
                    }}
                    sessionId={sessionId}
                  />
                </section>
              )}

              {/* Agents */}
              <section>
                <h2 className="text-3xl font-bold text-white mb-6">Your Agents</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {dashboardData?.agents?.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  )) || null}
                </div>
              </section>

              {/* Recent Activity */}
              <section>
                <h2 className="text-3xl font-bold text-white mb-6">Recent Affirmations</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {affirmations.slice(0, 4).map((affirmation) => (
                    <AffirmationCard key={affirmation.id} affirmation={affirmation} onUpdate={loadDashboard} />
                  ))}
                </div>
              </section>
            </div>
          )}

          {activeTab === "affirmations" && (
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">All Affirmations</h2>

              {/* Category Filter */}
              <div className="flex gap-3 mb-6 flex-wrap">
                <button className="px-4 py-2 rounded-lg bg-white/20 text-white hover:bg-white/30 transition-all">
                  All
                </button>
                <button className="px-4 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-all">
                  Identity
                </button>
                <button className="px-4 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-all">
                  Gratitude
                </button>
                <button className="px-4 py-2 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-all">
                  Action
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {affirmations.map((affirmation) => (
                  <AffirmationCard key={affirmation.id} affirmation={affirmation} onUpdate={loadDashboard} />
                ))}
              </div>

              {affirmations.length === 0 && (
                <div className="glass-card p-12 rounded-2xl text-center">
                  <p className="text-white/60 text-lg">No affirmations yet. Start your journey!</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "scripts" && (
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">Hypnosis Scripts</h2>
              <div className="space-y-6">
                {scripts.map((script) => (
                  <ScriptPlayer key={script.id} script={script} />
                ))}
              </div>

              {scripts.length === 0 && (
                <div className="glass-card p-12 rounded-2xl text-center">
                  <p className="text-white/60 text-lg">No scripts yet. Generate your first hypnosis session!</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "schedule" && (
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">Your Schedule</h2>
              <ScheduleCalendar schedule={dashboardData?.schedule || []} />
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

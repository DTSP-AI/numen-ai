"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { AffirmationCard } from "@/components/AffirmationCard"
import { ScriptPlayer } from "@/components/ScriptPlayer"
import { ScheduleCalendar } from "@/components/ScheduleCalendar"
import { AgentCard } from "@/components/AgentCard"

interface DashboardData {
  summary: {
    total_agents: number
    total_affirmations: number
    total_scripts: number
    upcoming_sessions: number
  }
  agents: any[]
  affirmations_by_category: Record<string, { total: number; with_audio: number }>
  schedule: any[]
  recent_threads: any[]
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
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [affirmations, setAffirmations] = useState<Affirmation[]>([])
  const [scripts, setScripts] = useState<HypnosisScript[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"overview" | "affirmations" | "scripts" | "schedule">("overview")

  // Mock user ID (in production, get from auth context)
  const userId = "test-user-123"

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

  return (
    <div className="min-h-screen gradient-kurzgesagt">
      <div className="container mx-auto px-6 py-12">
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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12"
        >
          <div className="glass-card p-6 rounded-2xl">
            <div className="text-kurzgesagt-yellow text-3xl font-bold mb-2">
              {dashboardData?.summary?.total_agents || 0}
            </div>
            <div className="text-white/80">Active Agents</div>
          </div>

          <div className="glass-card p-6 rounded-2xl">
            <div className="text-kurzgesagt-aqua text-3xl font-bold mb-2">
              {dashboardData?.summary?.total_affirmations || 0}
            </div>
            <div className="text-white/80">Affirmations</div>
          </div>

          <div className="glass-card p-6 rounded-2xl">
            <div className="text-kurzgesagt-purple text-3xl font-bold mb-2">
              {dashboardData?.summary?.total_scripts || 0}
            </div>
            <div className="text-white/80">Hypnosis Scripts</div>
          </div>

          <div className="glass-card p-6 rounded-2xl">
            <div className="text-kurzgesagt-coral text-3xl font-bold mb-2">
              {dashboardData?.summary?.upcoming_sessions || 0}
            </div>
            <div className="text-white/80">Upcoming Sessions</div>
          </div>
        </motion.div>

        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8">
          {["overview", "affirmations", "scripts", "schedule"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                activeTab === tab
                  ? "bg-white text-kurzgesagt-purple shadow-lg"
                  : "glass-card text-white hover:bg-white/20"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "overview" && (
            <div className="space-y-8">
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

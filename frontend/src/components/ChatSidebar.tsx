"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface Agent {
  id: string
  name: string
  description?: string
  [key: string]: unknown
}

interface Affirmation {
  id: string
  affirmation_text: string
  category: string
  audio_url: string | null
  is_favorite: boolean
  created_at: string
}

interface ScheduleItem {
  id: string
  [key: string]: unknown
}

interface Protocol {
  daily_practices: number
  visualizations: number
  success_metrics: number
  checkpoints: number
}

interface ChatSidebarProps {
  agent: Agent
  affirmations: Affirmation[]
  schedule: ScheduleItem[]
  protocol: Protocol
  collapsed: boolean
  onToggleCollapse: () => void
}

export function ChatSidebar({
  agent,
  affirmations,
  schedule,
  protocol,
  collapsed,
  onToggleCollapse
}: ChatSidebarProps) {
  const [activeSection, setActiveSection] = useState<"protocol" | "affirmations" | "schedule">("protocol")

  if (collapsed) {
    return (
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: "60px" }}
        className="glass-card-dark border-r border-white/10 flex flex-col items-center py-6 gap-4"
      >
        <button
          onClick={onToggleCollapse}
          className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 transition-all flex items-center justify-center text-white"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ width: 0 }}
      animate={{ width: "380px" }}
      className="glass-card-dark border-r border-white/10 flex flex-col h-full overflow-hidden"
    >
      {/* Header */}
      <div className="p-6 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral flex items-center justify-center text-2xl">
            🤖
          </div>
          <div>
            <h3 className="text-white font-bold">{agent.name}</h3>
            <p className="text-white/60 text-xs">Your Guide</p>
          </div>
        </div>
        <button
          onClick={onToggleCollapse}
          className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 transition-all flex items-center justify-center text-white"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Section Tabs */}
      <div className="flex border-b border-white/10">
        <button
          onClick={() => setActiveSection("protocol")}
          className={`flex-1 py-3 text-sm font-semibold transition-all ${
            activeSection === "protocol"
              ? "text-white border-b-2 border-kurzgesagt-purple"
              : "text-white/60 hover:text-white/80"
          }`}
        >
          Protocol
        </button>
        <button
          onClick={() => setActiveSection("affirmations")}
          className={`flex-1 py-3 text-sm font-semibold transition-all ${
            activeSection === "affirmations"
              ? "text-white border-b-2 border-kurzgesagt-purple"
              : "text-white/60 hover:text-white/80"
          }`}
        >
          Affirmations
        </button>
        <button
          onClick={() => setActiveSection("schedule")}
          className={`flex-1 py-3 text-sm font-semibold transition-all ${
            activeSection === "schedule"
              ? "text-white border-b-2 border-kurzgesagt-purple"
              : "text-white/60 hover:text-white/80"
          }`}
        >
          Schedule
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          {activeSection === "protocol" && (
            <motion.div
              key="protocol"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-4"
            >
              <h4 className="text-white font-semibold mb-4">Your Manifestation Protocol</h4>

              <div className="bg-white/5 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-white/80 text-sm">Daily Practices</span>
                  <span className="text-kurzgesagt-yellow font-bold">{protocol.daily_practices}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/80 text-sm">Visualizations</span>
                  <span className="text-kurzgesagt-coral font-bold">{protocol.visualizations}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/80 text-sm">Success Metrics</span>
                  <span className="text-kurzgesagt-purple font-bold">{protocol.success_metrics}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/80 text-sm">Checkpoints</span>
                  <span className="text-kurzgesagt-aqua font-bold">{protocol.checkpoints}</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-kurzgesagt-purple/20 to-kurzgesagt-coral/20 rounded-xl p-4 border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-5 h-5 text-kurzgesagt-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="text-white font-semibold text-sm">Quick Tip</span>
                </div>
                <p className="text-white/70 text-xs">
                  Consistency is key! Try to complete your daily practices at the same time each day for maximum effectiveness.
                </p>
              </div>
            </motion.div>
          )}

          {activeSection === "affirmations" && (
            <motion.div
              key="affirmations"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-3"
            >
              <h4 className="text-white font-semibold mb-4">Your Affirmations ({affirmations.length})</h4>

              {affirmations.length === 0 ? (
                <div className="text-center py-8 text-white/60 text-sm">
                  No affirmations yet. Complete your discovery questions to generate personalized affirmations.
                </div>
              ) : (
                affirmations.slice(0, 10).map((affirmation) => (
                  <div
                    key={affirmation.id}
                    className="bg-white/5 hover:bg-white/10 rounded-lg p-3 transition-all cursor-pointer group"
                  >
                    <div className="flex items-start gap-2">
                      {affirmation.is_favorite && (
                        <svg className="w-4 h-4 text-kurzgesagt-yellow flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-white/90 text-sm line-clamp-2">{affirmation.affirmation_text}</p>
                        <span className="text-white/40 text-xs mt-1 inline-block">{affirmation.category}</span>
                      </div>
                      {affirmation.audio_url && (
                        <button className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <svg className="w-5 h-5 text-kurzgesagt-purple" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}

          {activeSection === "schedule" && (
            <motion.div
              key="schedule"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-3"
            >
              <h4 className="text-white font-semibold mb-4">Upcoming Sessions</h4>

              {schedule.length === 0 ? (
                <div className="text-center py-8 text-white/60 text-sm">
                  No scheduled sessions yet. Schedule your first session to start your journey.
                </div>
              ) : (
                schedule.map((item) => (
                  <div
                    key={item.id}
                    className="bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-aqua flex items-center justify-center text-white font-bold text-sm">
                        {new Date().getDate()}
                      </div>
                      <div className="flex-1">
                        <p className="text-white text-sm font-medium">Manifestation Session</p>
                        <p className="text-white/60 text-xs">Today at 9:00 AM</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

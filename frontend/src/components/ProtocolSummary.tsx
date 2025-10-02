"use client"

import { useState } from "react"
import { motion } from "framer-motion"

interface ProtocolSummaryProps {
  protocol: {
    daily_practices: number
    visualizations: number
    success_metrics: number
    checkpoints: number
  }
  sessionId: string
}

export function ProtocolSummary({ protocol, sessionId }: ProtocolSummaryProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-8 rounded-3xl"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white mb-1">Your Manifestation Protocol</h3>
          <p className="text-white/70">AI-generated personalized plan</p>
        </div>
        <div className="text-4xl">✨</div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white/10 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-kurzgesagt-yellow mb-1">
            {protocol.daily_practices}
          </div>
          <div className="text-white/80 text-sm">Daily Practices</div>
        </div>

        <div className="bg-white/10 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-kurzgesagt-aqua mb-1">
            {protocol.visualizations}
          </div>
          <div className="text-white/80 text-sm">Visualizations</div>
        </div>

        <div className="bg-white/10 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-kurzgesagt-purple mb-1">
            {protocol.success_metrics}
          </div>
          <div className="text-white/80 text-sm">Success Metrics</div>
        </div>

        <div className="bg-white/10 rounded-xl p-4 text-center">
          <div className="text-3xl font-bold text-kurzgesagt-coral mb-1">
            {protocol.checkpoints}
          </div>
          <div className="text-white/80 text-sm">Checkpoints</div>
        </div>
      </div>

      {/* Expand/Collapse */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full py-3 px-4 rounded-xl bg-white/10 hover:bg-white/20 transition-all text-white font-semibold flex items-center justify-center gap-2"
      >
        <span>{expanded ? "Hide" : "View"} Full Protocol</span>
        <svg
          className={`w-5 h-5 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-6 pt-6 border-t border-white/20"
        >
          <div className="space-y-4">
            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="text-white font-bold text-lg mb-3">📋 Daily Practices</h4>
              <p className="text-white/70 text-sm">
                Your protocol includes {protocol.daily_practices} structured daily practices designed to
                reinforce your manifestation goals through consistent action.
              </p>
            </div>

            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="text-white font-bold text-lg mb-3">🎯 Success Metrics</h4>
              <p className="text-white/70 text-sm">
                Track your progress with {protocol.success_metrics} specific, measurable indicators
                aligned with your manifestation objectives.
              </p>
            </div>

            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="text-white font-bold text-lg mb-3">⏱️ Checkpoints</h4>
              <p className="text-white/70 text-sm">
                Stay on track with {protocol.checkpoints} milestone checkpoints for reflection
                and course correction throughout your journey.
              </p>
            </div>

            <div className="text-center mt-6">
              <a
                href={`/protocol/${sessionId}`}
                className="inline-block px-6 py-3 bg-kurzgesagt-yellow text-kurzgesagt-navy font-bold rounded-xl hover:bg-kurzgesagt-yellow/90 transition-all"
              >
                View Detailed Protocol →
              </a>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

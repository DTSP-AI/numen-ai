"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"

interface PlanReviewProps {
  sessionId: string
  agentName: string
  protocol: {
    daily_practices: number
    visualizations: number
    success_metrics: number
    checkpoints: number
  }
  affirmations: Array<{
    id: string
    affirmation_text: string
    category: string
  }>
  onAccept: () => void
  onEdit: () => void
  onAskQuestions: () => void
}

export function PlanReview({
  sessionId,
  agentName,
  protocol,
  affirmations,
  onAccept,
  onEdit,
  onAskQuestions
}: PlanReviewProps) {
  const [isAccepting, setIsAccepting] = useState(false)
  const [showDisclaimer, setShowDisclaimer] = useState(true)

  const handleAccept = async () => {
    setIsAccepting(true)
    try {
      const response = await fetch(`http://localhost:8003/api/sessions/${sessionId}/consent`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          consented: true
        })
      })

      if (!response.ok) {
        throw new Error("Failed to record consent")
      }

      onAccept()
    } catch (error) {
      console.error("Consent error:", error)
      alert("Failed to record consent. Please try again.")
    } finally {
      setIsAccepting(false)
    }
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt p-6">
      <div className="max-w-5xl mx-auto py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="text-5xl mb-4">📋</div>
          <h1 className="text-5xl font-bold text-white mb-3">Review Your Personalized Plan</h1>
          <p className="text-xl text-white/80">
            Created by {agentName} just for you
          </p>
        </motion.div>

        {/* Legal Disclaimer */}
        {showDisclaimer && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-amber-500/20 border-2 border-amber-500/50 rounded-2xl p-6 mb-8"
          >
            <div className="flex items-start gap-4">
              <div className="text-3xl flex-shrink-0">⚠️</div>
              <div className="flex-1">
                <h3 className="text-white font-bold text-lg mb-2">Important Disclaimer</h3>
                <p className="text-white/90 text-sm mb-4">
                  This is <strong>not medical advice</strong>. The content provided by Numen AI is for
                  informational and personal development purposes only. This platform does not replace
                  professional mental health services, therapy, or medical treatment.
                </p>
                <p className="text-white/90 text-sm mb-4">
                  If you are experiencing a mental health crisis or have serious psychological concerns,
                  please contact a licensed mental health professional or emergency services immediately.
                </p>
                <p className="text-white/80 text-xs">
                  By proceeding, you acknowledge that you understand this is a self-help tool and agree
                  to use it responsibly as part of your personal wellness journey.
                </p>
              </div>
              <button
                onClick={() => setShowDisclaimer(false)}
                className="text-white/60 hover:text-white"
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}

        {/* Protocol Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-3xl p-8 mb-8"
        >
          <h2 className="text-3xl font-bold text-white mb-6">Your Manifestation Protocol</h2>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
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

          {/* Affirmations Preview */}
          <div>
            <h3 className="text-xl font-bold text-white mb-4">Sample Affirmations</h3>
            <div className="space-y-3">
              {affirmations.slice(0, 5).map((aff) => (
                <div key={aff.id} className="bg-white/5 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl flex-shrink-0">✨</div>
                    <div className="flex-1">
                      <p className="text-white font-medium">{aff.affirmation_text}</p>
                      <p className="text-white/60 text-sm mt-1">Category: {aff.category}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {affirmations.length > 5 && (
              <p className="text-white/60 text-sm mt-4 text-center">
                + {affirmations.length - 5} more affirmations included
              </p>
            )}
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          {/* Primary Action */}
          <Button
            onClick={handleAccept}
            disabled={isAccepting}
            className="w-full bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white text-xl py-6 rounded-xl shadow-lg hover:shadow-2xl transition-all font-semibold disabled:opacity-50"
          >
            {isAccepting ? "Recording Consent..." : "Accept & Start Session ✓"}
          </Button>

          {/* Secondary Actions */}
          <div className="grid grid-cols-2 gap-4">
            <Button
              onClick={onEdit}
              variant="outline"
              className="bg-white/10 text-white border-white/30 hover:bg-white/20 py-4 rounded-xl font-semibold"
            >
              Edit Plan
            </Button>
            <Button
              onClick={onAskQuestions}
              variant="outline"
              className="bg-white/10 text-white border-white/30 hover:bg-white/20 py-4 rounded-xl font-semibold"
            >
              Ask More Questions
            </Button>
          </div>
        </motion.div>

        {/* Privacy Notice */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-white/50 text-sm mt-8"
        >
          Your consent and session data are stored securely and comply with HIPAA/SOC2 standards.
          <br />
          By clicking &quot;Accept &amp; Start Session&quot;, you consent to proceeding with this personalized plan.
        </motion.p>
      </div>
    </div>
  )
}

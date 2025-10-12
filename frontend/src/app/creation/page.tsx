"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"

interface GenerationStep {
  id: string
  title: string
  description: string
  status: "pending" | "processing" | "complete"
}

export default function CreationPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const userId = searchParams.get("userId") || "00000000-0000-0000-0000-000000000001"
  const agentId = searchParams.get("agentId")
  const sessionId = searchParams.get("sessionId")

  const [steps, setSteps] = useState<GenerationStep[]>([
    {
      id: "analyze",
      title: "Analyzing Your Goals",
      description: "Understanding your aspirations and intentions",
      status: "pending"
    },
    {
      id: "synthesize",
      title: "Synthesizing Your Agent's Wisdom",
      description: "Channeling your guide's unique voice and approach",
      status: "pending"
    },
    {
      id: "craft",
      title: "Crafting Personalized Affirmations",
      description: "Creating powerful statements aligned with your journey",
      status: "pending"
    },
    {
      id: "energize",
      title: "Infusing with Intention",
      description: "Embedding supportive energy into each affirmation",
      status: "pending"
    }
  ])

  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [affirmations, setAffirmations] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!agentId) {
      setError("No agent selected. Please create an agent first.")
      return
    }

    generateAffirmations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId, userId, sessionId])

  const updateStepStatus = (index: number, status: GenerationStep["status"]) => {
    setSteps(prev => prev.map((step, i) =>
      i === index ? { ...step, status } : step
    ))
  }

  const generateAffirmations = async () => {
    try {
      // Step 1: Analyze goals
      setCurrentStepIndex(0)
      updateStepStatus(0, "processing")
      await new Promise(resolve => setTimeout(resolve, 1500))
      updateStepStatus(0, "complete")

      // Step 2: Synthesize agent wisdom
      setCurrentStepIndex(1)
      updateStepStatus(1, "processing")
      await new Promise(resolve => setTimeout(resolve, 1500))
      updateStepStatus(1, "complete")

      // Step 3: Craft affirmations (actual API call)
      setCurrentStepIndex(2)
      updateStepStatus(2, "processing")

      const response = await fetch("http://localhost:8003/api/affirmations/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          agent_id: agentId,
          session_id: sessionId,
          count: 10
        })
      })

      if (!response.ok) {
        throw new Error("Failed to generate affirmations")
      }

      const data = await response.json()
      setAffirmations(data.affirmations || [])
      updateStepStatus(2, "complete")

      // Step 4: Energize
      setCurrentStepIndex(3)
      updateStepStatus(3, "processing")
      await new Promise(resolve => setTimeout(resolve, 1000))
      updateStepStatus(3, "complete")

      // Navigate to affirmations display after brief pause
      setTimeout(() => {
        router.push(`/affirmations?userId=${userId}&agentId=${agentId}`)
      }, 1500)

    } catch (err) {
      console.error("Generation error:", err)
      setError(err instanceof Error ? err.message : "Failed to generate affirmations")
    }
  }

  if (error) {
    return (
      <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-12 rounded-3xl text-center max-w-md"
        >
          <div className="text-6xl mb-6">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-4">Something Went Wrong</h2>
          <p className="text-white/80 mb-6">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-8 py-4 bg-white text-kurzgesagt-purple font-semibold rounded-xl hover:bg-white/90 transition-all"
          >
            Start Over
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl lg:text-6xl font-bold text-white mb-4 font-[family-name:var(--font-heading)]">
            Creating Your Journey
          </h1>
          <p className="text-xl text-white/80">
            Your personalized guide is crafting affirmations just for you
          </p>
        </motion.div>

        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`glass-card p-6 rounded-2xl transition-all duration-500 ${
                step.status === "processing"
                  ? "ring-2 ring-kurzgesagt-purple shadow-lg shadow-kurzgesagt-purple/50"
                  : step.status === "complete"
                  ? "bg-white/10"
                  : "bg-white/5"
              }`}
            >
              <div className="flex items-center gap-4">
                {/* Status Icon */}
                <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 ${
                  step.status === "complete"
                    ? "bg-green-500"
                    : step.status === "processing"
                    ? "bg-kurzgesagt-purple"
                    : "bg-white/20"
                }`}>
                  {step.status === "complete" ? (
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : step.status === "processing" ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-6 h-6 border-3 border-white border-t-transparent rounded-full"
                    />
                  ) : (
                    <div className="w-3 h-3 rounded-full bg-white/50" />
                  )}
                </div>

                {/* Step Info */}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">{step.title}</h3>
                  <p className="text-white/70">{step.description}</p>
                </div>
              </div>

              {/* Progress Bar for Active Step */}
              {step.status === "processing" && (
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.5, ease: "easeInOut" }}
                  className="h-1 bg-kurzgesagt-purple rounded-full mt-4"
                />
              )}
            </motion.div>
          ))}
        </div>

        {/* Gentle Reminder */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="text-center mt-12 text-white/60 text-sm"
        >
          <p>This process is being guided by your personalized agent</p>
          <p className="mt-2">Each affirmation is crafted uniquely for your journey</p>
        </motion.div>
      </div>
    </div>
  )
}

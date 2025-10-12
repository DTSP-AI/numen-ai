"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"

interface DiscoveryQuestionsProps {
  agentId: string
  sessionId: string
  userId: string
  onComplete: (planResult?: any) => void
}

export function DiscoveryQuestions({ agentId, sessionId, userId, onComplete }: DiscoveryQuestionsProps) {
  const [step, setStep] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [answers, setAnswers] = useState({
    focusArea: "",
    dailyTime: "",
    cadence: ""
  })

  const focusAreas = [
    { value: "confidence", label: "Build Confidence & Self-Worth", emoji: "💪" },
    { value: "abundance", label: "Attract Wealth & Abundance", emoji: "💰" },
    { value: "relationships", label: "Improve Relationships & Love", emoji: "❤️" },
    { value: "health", label: "Enhance Health & Vitality", emoji: "🌟" },
    { value: "peace", label: "Find Inner Peace & Calm", emoji: "🧘" },
    { value: "purpose", label: "Discover Life Purpose", emoji: "🎯" }
  ]

  const timeCommitments = [
    { value: "15min", label: "15 minutes/day", description: "Quick daily practice" },
    { value: "30min", label: "30 minutes/day", description: "Moderate commitment" },
    { value: "60min", label: "60 minutes/day", description: "Deep transformation" }
  ]

  const cadences = [
    { value: "daily", label: "Daily", description: "Every day for fastest results" },
    { value: "3x_week", label: "3x per week", description: "Balanced approach" },
    { value: "weekly", label: "Weekly", description: "Gentle integration" }
  ]

  const handleNext = () => {
    if (step < 3) setStep(step + 1)
  }

  const handleBack = () => {
    if (step > 1) setStep(step - 1)
  }

  const handleGenerate = async () => {
    setIsGenerating(true)

    try {
      // Map answers to API format
      const commitmentLevel = answers.dailyTime === "60min" ? "intensive" :
                            answers.dailyTime === "30min" ? "moderate" : "light"

      const timeframe = answers.cadence === "daily" ? "30_days" :
                       answers.cadence === "3x_week" ? "60_days" : "90_days"

      const response = await fetch("http://localhost:8003/api/affirmations/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          user_id: userId,
          agent_id: agentId,
          session_id: sessionId,
          count: 10,
          discovery: {
            focus_area: answers.focusArea,
            daily_time: answers.dailyTime,
            cadence: answers.cadence
          }
        })
      })

      if (!response.ok) {
        throw new Error("Failed to generate plan")
      }

      const result = await response.json()
      console.log("Plan generated:", result)

      // Pass results to parent instead of just triggering reload
      onComplete(result)
    } catch (error) {
      console.error("Failed to generate plan:", error)
      alert("Failed to generate your personalized plan. Please try again.")
    } finally {
      setIsGenerating(false)
    }
  }

  const renderQuestion = () => {
    switch (step) {
      case 1:
        return (
          <motion.div
            key="question1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">What&apos;s your primary focus?</h2>
              <p className="text-white/80">Choose the area you want to transform first</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {focusAreas.map((area) => (
                <button
                  key={area.value}
                  onClick={() => setAnswers({ ...answers, focusArea: area.value })}
                  className={`p-6 rounded-2xl text-left transition-all ${
                    answers.focusArea === area.value
                      ? "bg-white text-kurzgesagt-purple shadow-2xl scale-105"
                      : "bg-white/10 text-white hover:bg-white/20"
                  }`}
                >
                  <div className="text-3xl mb-2">{area.emoji}</div>
                  <div className="font-bold text-lg">{area.label}</div>
                </button>
              ))}
            </div>
          </motion.div>
        )

      case 2:
        return (
          <motion.div
            key="question2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">How much time can you commit?</h2>
              <p className="text-white/80">Be realistic - consistency matters more than duration</p>
            </div>

            <div className="space-y-4">
              {timeCommitments.map((time) => (
                <button
                  key={time.value}
                  onClick={() => setAnswers({ ...answers, dailyTime: time.value })}
                  className={`w-full p-6 rounded-2xl text-left transition-all ${
                    answers.dailyTime === time.value
                      ? "bg-white text-kurzgesagt-purple shadow-2xl"
                      : "bg-white/10 text-white hover:bg-white/20"
                  }`}
                >
                  <div className="font-bold text-xl mb-1">{time.label}</div>
                  <div className={answers.dailyTime === time.value ? "text-kurzgesagt-purple/70" : "text-white/60"}>
                    {time.description}
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        )

      case 3:
        return (
          <motion.div
            key="question3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">What&apos;s your ideal practice rhythm?</h2>
              <p className="text-white/80">Choose a cadence that fits your lifestyle</p>
            </div>

            <div className="space-y-4">
              {cadences.map((cadence) => (
                <button
                  key={cadence.value}
                  onClick={() => setAnswers({ ...answers, cadence: cadence.value })}
                  className={`w-full p-6 rounded-2xl text-left transition-all ${
                    answers.cadence === cadence.value
                      ? "bg-white text-kurzgesagt-purple shadow-2xl"
                      : "bg-white/10 text-white hover:bg-white/20"
                  }`}
                >
                  <div className="font-bold text-xl mb-1">{cadence.label}</div>
                  <div className={answers.cadence === cadence.value ? "text-kurzgesagt-purple/70" : "text-white/60"}>
                    {cadence.description}
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        )
    }
  }

  const canProceed = () => {
    if (step === 1) return answers.focusArea !== ""
    if (step === 2) return answers.dailyTime !== ""
    if (step === 3) return answers.cadence !== ""
    return false
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt p-6 flex items-center justify-center">
      <div className="max-w-3xl w-full">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-all ${
                    s === step
                      ? "bg-white text-kurzgesagt-purple scale-110"
                      : s < step
                      ? "bg-kurzgesagt-aqua text-white"
                      : "bg-white/20 text-white/60"
                  }`}
                >
                  {s}
                </div>
                {s < 3 && (
                  <div
                    className={`h-1 w-16 mx-2 transition-all ${
                      s < step ? "bg-kurzgesagt-aqua" : "bg-white/20"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <p className="text-white/80 text-center">
            Question {step} of 3
          </p>
        </div>

        {/* Question Content */}
        <AnimatePresence mode="wait">
          {renderQuestion()}
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            onClick={handleBack}
            disabled={step === 1}
            variant="outline"
            className="px-8 py-3 bg-white/10 text-white border-white/30 hover:bg-white/20 disabled:opacity-50"
          >
            Back
          </Button>

          {step < 3 ? (
            <Button
              onClick={handleNext}
              disabled={!canProceed()}
              className="px-8 py-3 bg-white text-kurzgesagt-purple font-bold hover:bg-white/90 disabled:opacity-50"
            >
              Next
            </Button>
          ) : (
            <Button
              onClick={handleGenerate}
              disabled={!canProceed() || isGenerating}
              className="px-12 py-3 bg-kurzgesagt-yellow text-kurzgesagt-navy font-bold hover:bg-kurzgesagt-yellow/90 disabled:opacity-50"
            >
              {isGenerating ? "Generating Your Plan..." : "Generate My Plan ✨"}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

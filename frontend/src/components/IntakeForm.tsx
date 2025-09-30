"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api"
import type { TonePreference, SessionType } from "@/types"

interface IntakeFormProps {
  onComplete: (contractId: string, sessionId: string) => void
}

export function IntakeForm({ onComplete }: IntakeFormProps) {
  const [goals, setGoals] = useState<string[]>([""])
  const [tone, setTone] = useState<TonePreference>("calm")
  const [sessionType, setSessionType] = useState<SessionType>("manifestation")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const addGoal = () => {
    if (goals.length < 5) {
      setGoals([...goals, ""])
    }
  }

  const updateGoal = (index: number, value: string) => {
    const newGoals = [...goals]
    newGoals[index] = value
    setGoals(newGoals)
  }

  const removeGoal = (index: number) => {
    setGoals(goals.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Create session
      const session = await api.createSession("user-demo-001")

      // Create contract
      const contract = await api.createContract({
        session_id: session.id,
        user_id: "user-demo-001",
        goals: goals.filter(g => g.trim() !== ""),
        tone,
        voice_id: tone,
        session_type: sessionType
      })

      onComplete(contract.id, session.id)
    } catch (error) {
      console.error("Failed to create session:", error)
      alert("Failed to start session. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <h2 className="text-4xl lg:text-5xl font-bold text-white mb-3 font-[family-name:var(--font-heading)] tracking-tight">
        Let&apos;s Personalize Your Experience
      </h2>
      <p className="text-lg text-white/80 mb-10">
        Share your goals and preferences to create a tailored hypnotherapy session
      </p>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Goals */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <Label htmlFor="goals" className="text-white text-xl mb-4 block font-medium">
            What would you like to work on?
          </Label>
          <AnimatePresence mode="popLayout">
            {goals.map((goal, index) => (
              <motion.div
                key={index}
                className="flex gap-3 mb-3"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Input
                  value={goal}
                  onChange={(e) => updateGoal(index, e.target.value)}
                  placeholder="e.g., Build confidence, reduce anxiety..."
                  className="flex-1 bg-white/15 border-white/25 text-white placeholder:text-white/60 h-14 text-lg rounded-xl focus:bg-white/20 transition-all hover:border-white/40"
                  required={index === 0}
                />
                {goals.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => removeGoal(index)}
                    className="text-white hover:text-kurzgesagt-coral hover:bg-white/10 h-14 px-4 rounded-xl transition-all"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </Button>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          {goals.length < 5 && (
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                type="button"
                variant="outline"
                onClick={addGoal}
                className="mt-3 text-white border-white/30 bg-white/5 hover:bg-white/15 h-12 px-6 rounded-xl transition-all"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Add Another Goal
              </Button>
            </motion.div>
          )}
        </motion.div>

        {/* Session Type */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Label className="text-white text-xl mb-4 block font-medium">
            Session Type
          </Label>
          <Select value={sessionType} onValueChange={(v) => setSessionType(v as SessionType)}>
            <SelectTrigger className="bg-white/15 border-white/25 text-white h-14 text-lg rounded-xl hover:bg-white/20 hover:border-white/40 transition-all">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-kurzgesagt-navy border-white/20 text-white rounded-xl">
              <SelectItem value="manifestation" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Manifestation
              </SelectItem>
              <SelectItem value="anxiety_relief" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Anxiety Relief
              </SelectItem>
              <SelectItem value="sleep_hypnosis" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Sleep Hypnosis
              </SelectItem>
              <SelectItem value="confidence" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Confidence Building
              </SelectItem>
              <SelectItem value="habit_change" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Habit Change
              </SelectItem>
            </SelectContent>
          </Select>
        </motion.div>

        {/* Tone */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Label className="text-white text-xl mb-4 block font-medium">
            Preferred Voice Tone
          </Label>
          <Select value={tone} onValueChange={(v) => setTone(v as TonePreference)}>
            <SelectTrigger className="bg-white/15 border-white/25 text-white h-14 text-lg rounded-xl hover:bg-white/20 hover:border-white/40 transition-all">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-kurzgesagt-navy border-white/20 text-white rounded-xl">
              <SelectItem value="calm" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Calm & Soothing
              </SelectItem>
              <SelectItem value="energetic" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Energetic & Motivating
              </SelectItem>
              <SelectItem value="authoritative" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Authoritative & Confident
              </SelectItem>
              <SelectItem value="gentle" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Gentle & Nurturing
              </SelectItem>
              <SelectItem value="empowering" className="text-lg py-3 focus:bg-kurzgesagt-purple focus:text-white">
                Empowering & Strong
              </SelectItem>
            </SelectContent>
          </Select>
        </motion.div>

        {/* Submit */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-kurzgesagt-purple hover:bg-kurzgesagt-purple-light text-white text-xl py-7 rounded-xl shadow-lg hover:shadow-kurzgesagt-purple/50 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-3">
                <svg
                  className="animate-spin h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Starting Your Session...
              </span>
            ) : (
              "Begin Therapy Session"
            )}
          </Button>
        </motion.div>
      </form>
    </motion.div>
  )
}
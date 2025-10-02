"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface AgentBuilderProps {
  userId: string
  sessionId?: string
}

type Step = 1 | 2 | 3 | 4 | 5 | 6 | 7

interface Voice {
  id: string
  name: string
  category: string
  gender: string
  age: string
  description: string
  accent?: string
  use_case: string
}

interface AgentTraits {
  creativity: number
  empathy: number
  assertiveness: number
  humor: number
  formality: number
  verbosity: number
  confidence: number
  spirituality: number
  supportiveness: number
}

export function AgentBuilder({ userId, sessionId }: AgentBuilderProps) {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Step 1: Identity & Purpose
  const [agentName, setAgentName] = useState("")
  const [characterRole, setCharacterRole] = useState("")
  const [mission, setMission] = useState("")

  // Step 2: Core Personality Traits
  const [traits, setTraits] = useState<AgentTraits>({
    creativity: 50,
    empathy: 70,
    assertiveness: 50,
    humor: 30,
    formality: 40,
    verbosity: 60,
    confidence: 70,
    spirituality: 60,
    supportiveness: 80,
  })

  // Step 3: Communication Style
  const [interactionStyle, setInteractionStyle] = useState("")
  const [voicePreference, setVoicePreference] = useState("calm")
  const [pacing, setPacing] = useState("moderate")

  // Step 3.5: Voice Selection (NEW)
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([])
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null)
  const [isLoadingVoices, setIsLoadingVoices] = useState(false)
  const [isPlayingPreview, setIsPlayingPreview] = useState(false)

  // Step 4: Manifestation Focus Areas
  const [focusAreas, setFocusAreas] = useState<string[]>([])
  const [specializations, setSpecializations] = useState("")

  // Step 5: Philosophy & Approach
  const [philosophy, setPhilosophy] = useState("")
  const [techniques, setTechniques] = useState<string[]>([])

  // Step 6: Advanced Settings
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(800)

  const updateTrait = (trait: keyof AgentTraits, value: number) => {
    setTraits(prev => ({ ...prev, [trait]: value }))
  }

  const toggleFocusArea = (area: string) => {
    setFocusAreas(prev =>
      prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
    )
  }

  const toggleTechnique = (technique: string) => {
    setTechniques(prev =>
      prev.includes(technique) ? prev.filter(t => t !== technique) : [...prev, technique]
    )
  }

  const handleNext = () => {
    if (step < 6) setStep((step + 1) as Step)
  }

  const handleBack = () => {
    if (step > 1) setStep((step - 1) as Step)
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)

    try {
      // Load intake data from localStorage
      const intakeDataStr = localStorage.getItem('intakeData')
      const intakeData = intakeDataStr ? JSON.parse(intakeDataStr) : null

      const agentRequest = {
        name: agentName,
        type: "conversational",
        identity: {
          short_description: `${characterRole} - ${mission.substring(0, 100)}`,
          full_description: mission,
          character_role: characterRole,
          mission: mission,
          interaction_style: interactionStyle
        },
        traits: traits,
        configuration: {
          llm_provider: "openai",
          llm_model: "gpt-4",
          max_tokens: maxTokens,
          temperature: temperature,
          memory_enabled: true,
          voice_enabled: false,
          tools_enabled: false,
          memory_k: 6,
          thread_window: 20
        },
        tags: [
          "manifestation",
          "hypnotherapy",
          ...focusAreas,
          philosophy,
          voicePreference,
          pacing,
          ...specializations,
          ...techniques
        ]
      }

      // Create agent
      const agentResponse = await fetch("http://localhost:8000/api/agents", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-tenant-id": "00000000-0000-0000-0000-000000000001",
          "x-user-id": userId
        },
        body: JSON.stringify(agentRequest)
      })

      if (!agentResponse.ok) {
        const errorText = await agentResponse.text()
        console.error("Agent creation failed:", errorText)
        throw new Error(`Failed to create agent: ${errorText}`)
      }

      const agentResult = await agentResponse.json()
      console.log("Agent created:", agentResult)

      // Extract agent ID from response
      const agentId = agentResult.agent?.id || agentResult.id

      // Now have the Agent create a session
      const sessionResponse = await fetch("http://localhost:8000/api/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          agent_id: agentId,
          metadata: {
            intake_data: intakeData,
            created_by: "agent"
          }
        })
      })

      if (!sessionResponse.ok) {
        throw new Error("Failed to create session")
      }

      const sessionResult = await sessionResponse.json()
      const sessionId = sessionResult.id

      // Clean up localStorage
      localStorage.removeItem('intakeData')

      // Show success - agent and session created!
      // Navigate to dashboard/home instead of affirmation generation
      router.push(`/dashboard?agentId=${agentId}&sessionId=${sessionId}&success=true`)
    } catch (error) {
      console.error("Failed to create agent:", error)
      alert("Failed to create your personalized agent. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Let&apos;s Create Your Personal Guide</h2>
              <p className="text-white/80">Give your manifestation agent a name and purpose</p>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="agentName" className="text-white font-semibold">Agent Name</Label>
                <Input
                  id="agentName"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  placeholder="e.g., Luna, Marcus, Serena"
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label htmlFor="characterRole" className="text-white font-semibold">Character Role</Label>
                <Input
                  id="characterRole"
                  value={characterRole}
                  onChange={(e) => setCharacterRole(e.target.value)}
                  placeholder="e.g., Wise Manifestation Guide, Empowering Life Coach"
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label htmlFor="mission" className="text-white font-semibold">Mission & Purpose</Label>
                <Textarea
                  id="mission"
                  value={mission}
                  onChange={(e) => setMission(e.target.value)}
                  placeholder="Describe what this agent will help you achieve..."
                  rows={4}
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>
            </div>
          </motion.div>
        )

      case 2:
        return (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Core Personality Traits</h2>
              <p className="text-white/80">Shape how your agent thinks and responds</p>
            </div>

            <div className="space-y-6">
              {(Object.keys(traits) as Array<keyof AgentTraits>).map((trait) => (
                <div key={trait} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="text-white font-semibold capitalize">{trait}</Label>
                    <span className="text-white/80 text-sm">{traits[trait]}/100</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={traits[trait]}
                    onChange={(e) => updateTrait(trait, parseInt(e.target.value))}
                    className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between text-xs text-white/60">
                    <span>Low</span>
                    <span>Balanced</span>
                    <span>High</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )

      case 3:
        return (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Communication Style</h2>
              <p className="text-white/80">Define how your agent speaks and interacts</p>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="interactionStyle" className="text-white font-semibold">Interaction Style</Label>
                <Textarea
                  id="interactionStyle"
                  value={interactionStyle}
                  onChange={(e) => setInteractionStyle(e.target.value)}
                  placeholder="e.g., Warm and encouraging, with gentle wisdom and compassionate guidance"
                  rows={3}
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label className="text-white font-semibold">Voice Tone Preference</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {["calm", "energetic", "soothing", "authoritative"].map((voice) => (
                    <button
                      key={voice}
                      onClick={() => setVoicePreference(voice)}
                      className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                        voicePreference === voice
                          ? "bg-white text-kurzgesagt-purple"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {voice.charAt(0).toUpperCase() + voice.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-white font-semibold">Speaking Pace</Label>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  {["slow", "moderate", "fast"].map((pace) => (
                    <button
                      key={pace}
                      onClick={() => setPacing(pace)}
                      className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                        pacing === pace
                          ? "bg-white text-kurzgesagt-purple"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {pace.charAt(0).toUpperCase() + pace.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )

      case 4:
        return (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Manifestation Focus Areas</h2>
              <p className="text-white/80">Select the areas you want your agent to specialize in</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                "Wealth & Abundance",
                "Health & Vitality",
                "Relationships & Love",
                "Career & Success",
                "Inner Peace",
                "Confidence & Self-Worth",
                "Creativity & Expression",
                "Spiritual Growth",
                "Life Purpose",
                "Emotional Healing"
              ].map((area) => (
                <button
                  key={area}
                  onClick={() => toggleFocusArea(area)}
                  className={`px-4 py-3 rounded-lg font-semibold transition-all text-left ${
                    focusAreas.includes(area)
                      ? "bg-white text-kurzgesagt-purple"
                      : "bg-white/10 text-white hover:bg-white/20"
                  }`}
                >
                  {area}
                </button>
              ))}
            </div>

            <div>
              <Label htmlFor="specializations" className="text-white font-semibold">Additional Specializations</Label>
              <Textarea
                id="specializations"
                value={specializations}
                onChange={(e) => setSpecializations(e.target.value)}
                placeholder="Any specific areas or techniques you'd like to include..."
                rows={3}
                className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
              />
            </div>
          </motion.div>
        )

      case 5:
        return (
          <motion.div
            key="step5"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Philosophy & Approach</h2>
              <p className="text-white/80">Define the underlying philosophy and techniques</p>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="philosophy" className="text-white font-semibold">Core Philosophy</Label>
                <Textarea
                  id="philosophy"
                  value={philosophy}
                  onChange={(e) => setPhilosophy(e.target.value)}
                  placeholder="e.g., Combines Law of Attraction with mindfulness and neuroplasticity principles..."
                  rows={4}
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label className="text-white font-semibold">Preferred Techniques</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {[
                    "Visualization",
                    "Affirmations",
                    "Guided Meditation",
                    "Hypnotherapy",
                    "NLP Techniques",
                    "Energy Work",
                    "Journaling Prompts",
                    "Breathwork"
                  ].map((technique) => (
                    <button
                      key={technique}
                      onClick={() => toggleTechnique(technique)}
                      className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                        techniques.includes(technique)
                          ? "bg-white text-kurzgesagt-purple"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {technique}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )

      case 6:
        return (
          <motion.div
            key="step6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Review & Create</h2>
              <p className="text-white/80">Review your agent and create your personalized guide</p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-4">
              <div>
                <h3 className="text-white font-bold mb-2">Agent Name</h3>
                <p className="text-white/80">{agentName || "Not set"}</p>
              </div>
              <div>
                <h3 className="text-white font-bold mb-2">Character Role</h3>
                <p className="text-white/80">{characterRole || "Not set"}</p>
              </div>
              <div>
                <h3 className="text-white font-bold mb-2">Focus Areas</h3>
                <p className="text-white/80">{focusAreas.join(", ") || "None selected"}</p>
              </div>
              <div>
                <h3 className="text-white font-bold mb-2">Techniques</h3>
                <p className="text-white/80">{techniques.join(", ") || "None selected"}</p>
              </div>
              <div>
                <h3 className="text-white font-bold mb-2">Personality Highlights</h3>
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-sm">
                    <span className="text-white/60">Empathy:</span> <span className="text-white">{traits.empathy}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-white/60">Spirituality:</span> <span className="text-white">{traits.spirituality}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-white/60">Supportiveness:</span> <span className="text-white">{traits.supportiveness}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-kurzgesagt-yellow/10 border border-kurzgesagt-yellow/30 rounded-xl p-4">
              <p className="text-white/90 text-sm">
                ✨ Your personalized manifestation agent will be created with these settings. You can always adjust them later.
              </p>
            </div>
          </motion.div>
        )
    }
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt py-16">
      <div className="container mx-auto px-6 max-w-4xl">
        {/* Progress Indicator */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            {[1, 2, 3, 4, 5, 6].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${
                    s === step
                      ? "bg-white text-kurzgesagt-purple"
                      : s < step
                      ? "bg-kurzgesagt-aqua text-white"
                      : "bg-white/20 text-white/60"
                  }`}
                >
                  {s}
                </div>
                {s < 6 && (
                  <div
                    className={`h-1 w-12 mx-2 transition-all ${
                      s < step ? "bg-kurzgesagt-aqua" : "bg-white/20"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <p className="text-white/80 text-center">
            Step {step} of 6: {
              ["Identity", "Personality", "Communication", "Focus", "Philosophy", "Review"][step - 1]
            }
          </p>
        </div>

        {/* Form Content */}
        <AnimatePresence mode="wait">
          {renderStep()}
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-12">
          <Button
            onClick={handleBack}
            disabled={step === 1}
            variant="outline"
            className="px-8 py-3 bg-white/10 text-white border-white/30 hover:bg-white/20"
          >
            Back
          </Button>

          {step < 6 ? (
            <Button
              onClick={handleNext}
              className="px-8 py-3 bg-white text-kurzgesagt-purple font-bold hover:bg-white/90"
            >
              Next
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-12 py-3 bg-kurzgesagt-yellow text-kurzgesagt-navy font-bold hover:bg-kurzgesagt-yellow/90"
            >
              {isSubmitting ? "Creating..." : "Create My Agent ✨"}
            </Button>
          )}
        </div>
      </div>

      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
        }
        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: white;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </div>
  )
}

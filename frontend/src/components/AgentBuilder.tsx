"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { AIHelpButton } from "@/components/AIHelpButton"

interface AgentBuilderProps {
  userId: string
  sessionId?: string
}

type Step = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9

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
  confidence: number
  empathy: number
  creativity: number
  discipline: number
  assertiveness: number
  humor: number
  formality: number
  verbosity: number
  spirituality: number
  supportiveness: number
}

export function AgentBuilder({ userId }: AgentBuilderProps) {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Step 1: Identity & Purpose
  const [agentName, setAgentName] = useState("")
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])
  const [mission, setMission] = useState("")
  const [isMissionFocused, setIsMissionFocused] = useState(false)

  // Step 2: 4 User-Facing Guide Controls
  const [guideControls, setGuideControls] = useState({
    guide_energy: 50,          // Calm ↔ Energetic
    coaching_style: 50,        // Nurturing ↔ Directive
    creative_expression: 50,   // Practical ↔ Imaginative
    communication_depth: 50,   // Concise ↔ Detailed
  })

  // Legacy traits state (for backend compatibility)
  const [traits, setTraits] = useState<AgentTraits>({
    confidence: 70,
    empathy: 70,
    creativity: 50,
    discipline: 60,
    assertiveness: 50,
    humor: 30,
    formality: 40,
    verbosity: 60,
    spirituality: 60,
    supportiveness: 80,
  })

  // Step 3: Voice Selection
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([])
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null)
  const [isLoadingVoices, setIsLoadingVoices] = useState(false)
  const [isPlayingPreview, setIsPlayingPreview] = useState<string | null>(null)

  // Step 4: Avatar
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null)
  const [avatarPrompt, setAvatarPrompt] = useState("")
  const [isGeneratingAvatar, setIsGeneratingAvatar] = useState(false)
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false)

  // Step 4: Communication Style
  const [selectedInteractionStyles, setSelectedInteractionStyles] = useState<string[]>([])
  const [voicePreference, setVoicePreference] = useState("calm")
  const [pacing, setPacing] = useState("moderate")

  // Step 5: Manifestation Focus Areas
  const [focusAreas, setFocusAreas] = useState<string[]>([])
  const [specializations, setSpecializations] = useState("")

  // Step 6: Philosophy & Approach
  const [philosophy, setPhilosophy] = useState("")
  const [techniques, setTechniques] = useState<string[]>([])

  // Step 7: Advanced Settings (LLM Configuration)
  const [maxTokens, setMaxTokens] = useState(800)
  const [temperature, setTemperature] = useState(0.7)

  // Convert guide controls to backend traits
  const convertGuideControlsToTraits = () => {
    // Map user-friendly controls to backend trait system
    return {
      // guide_energy (0=Calm, 100=Energetic) maps to confidence + assertiveness
      confidence: Math.round((guideControls.guide_energy * 0.6) + 40),
      assertiveness: Math.round((guideControls.guide_energy * 0.8) + 20),

      // coaching_style (0=Nurturing, 100=Directive) maps to empathy + supportiveness
      empathy: Math.round(100 - (guideControls.coaching_style * 0.6)),
      supportiveness: Math.round(100 - (guideControls.coaching_style * 0.5)),

      // creative_expression (0=Practical, 100=Imaginative) maps to creativity + humor
      creativity: guideControls.creative_expression,
      humor: Math.round(guideControls.creative_expression * 0.4),

      // communication_depth (0=Concise, 100=Detailed) maps to verbosity + formality
      verbosity: guideControls.communication_depth,
      formality: Math.round(50 - (guideControls.communication_depth * 0.2)),

      // Fixed values for stability
      discipline: 60,
      spirituality: 60,
    }
  }

  // Load voices when Step 3 is reached
  useEffect(() => {
    if (step === 3 && availableVoices.length === 0) {
      loadVoices()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step])

  const loadVoices = async () => {
    setIsLoadingVoices(true)
    try {
      const response = await fetch("http://localhost:8003/api/voices", {
        headers: {
          "x-user-id": userId,
          "Accept": "application/json"
        },
        mode: "cors"
      })
      const data = await response.json()
      setAvailableVoices(data.voices || [])
    } catch (error) {
      console.error("Failed to load voices:", error)
    } finally {
      setIsLoadingVoices(false)
    }
  }

  const playVoicePreview = async (voiceId: string) => {
    setIsPlayingPreview(voiceId)
    try {
      const response = await fetch("http://localhost:8003/api/voices/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voice_id: voiceId,
          text: "Hello, I'm your personalized Guide. Together, we'll unlock your potential and create lasting transformation."
        })
      })

      if (response.ok) {
        const audioBlob = await response.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.onerror = () => {
          console.error("Audio playback failed for preview")
          setIsPlayingPreview(null)
        }
        audio.onended = () => {
          setIsPlayingPreview(null)
          URL.revokeObjectURL(audioUrl)
        }
        audio.play()
      } else {
        const errText = await response.text()
        console.error("Voice preview request failed:", errText)
        alert("Voice preview failed. Please check your ElevenLabs API key or network connection.")
        setIsPlayingPreview(null)
      }
    } catch (error) {
      console.error("Failed to play preview:", error)
      alert("Voice preview failed. Please check your network connection.")
      setIsPlayingPreview(null)
    }
  }

  const generateAvatar = async () => {
    if (!avatarPrompt.trim()) {
      alert("Please enter a description for your avatar")
      return
    }

    setIsGeneratingAvatar(true)
    try {
      const response = await fetch("http://localhost:8003/api/avatar/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: avatarPrompt,
          size: "1024x1024",
          quality: "auto",
          background: "opaque"
        })
      })

      if (response.ok) {
        const data = await response.json()
        // Prepend localhost if relative URL
        const fullAvatarUrl = data.avatar_url.startsWith('http')
          ? data.avatar_url
          : `http://localhost:8003${data.avatar_url}`
        setAvatarUrl(fullAvatarUrl)
      } else {
        const error = await response.text()
        console.error("Avatar generation failed:", error)
        alert("Failed to generate avatar. Please try again.")
      }
    } catch (error) {
      console.error("Avatar generation error:", error)
      alert("Failed to generate avatar. Please try again.")
    } finally {
      setIsGeneratingAvatar(false)
    }
  }

  const uploadAvatar = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploadingAvatar(true)
    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("http://localhost:8003/api/avatar/upload", {
        method: "POST",
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setAvatarUrl(`http://localhost:8003${data.avatar_url}`)
      } else {
        const error = await response.text()
        console.error("Avatar upload failed:", error)
        alert("Failed to upload avatar. Please try a different file.")
      }
    } catch (error) {
      console.error("Avatar upload error:", error)
      alert("Failed to upload avatar. Please try again.")
    } finally {
      setIsUploadingAvatar(false)
    }
  }

  const toggleRole = (role: string) => {
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role]
    )
  }

  const toggleInteractionStyle = (style: string) => {
    setSelectedInteractionStyles(prev =>
      prev.includes(style) ? prev.filter(s => s !== style) : [...prev, style]
    )
  }

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

  const validateCurrentStep = (): boolean => {
    switch (step) {
      case 1:
        if (!agentName.trim()) {
          alert("Please enter a name for your Guide")
          return false
        }
        if (selectedRoles.length === 0) {
          alert("Please select at least one role for your Guide")
          return false
        }
        if (!mission.trim()) {
          alert("Please describe your Guide's mission")
          return false
        }
        return true
      case 3:
        if (!selectedVoice) {
          alert("Please select a voice for your Guide")
          return false
        }
        return true
      case 5:
        if (selectedInteractionStyles.length === 0) {
          alert("Please select at least one interaction style")
          return false
        }
        return true
      default:
        return true
    }
  }

  const handleNext = () => {
    if (!validateCurrentStep()) return
    if (step < 9) setStep((step + 1) as Step)
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
          // Backend validation requires short_description <= 100 characters
          // Dynamically truncate the combined string to enforce the limit
          short_description: `${selectedRoles.join(', ')} - ${mission}`.substring(0, 100),
          full_description: mission,
          character_role: selectedRoles[0] || "",
          roles: selectedRoles,
          mission: mission,
          interaction_style: selectedInteractionStyles.join(', '),
          interaction_styles: selectedInteractionStyles,
          avatar_url: avatarUrl || undefined
        },
        traits: convertGuideControlsToTraits(),
        configuration: {
          llm_provider: "openai",
          llm_model: "gpt-4",
          max_tokens: maxTokens,
          temperature: temperature,
          memory_enabled: true,
          voice_enabled: selectedVoice ? true : false,
          tools_enabled: false,
          memory_k: 6,
          thread_window: 20
        },
        voice: selectedVoice ? {
          provider: "elevenlabs",
          voice_id: selectedVoice.id,
          language: "en-US",
          speed: 1.0,
          pitch: 1.0,
          stability: 0.75,
          similarity_boost: 0.75,
          stt_provider: "deepgram",
          stt_model: "nova-2",
          stt_language: "en",
          vad_enabled: true
        } : undefined,
        tags: [
          "manifestation",
          "hypnotherapy",
          ...focusAreas,
          ...selectedRoles,
          philosophy,
          voicePreference,
          pacing,
          specializations,
          ...techniques
        ].filter(Boolean)
      }

      // Create agent
      const agentResponse = await fetch("http://localhost:8003/api/agents", {
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
      const sessionResponse = await fetch("http://localhost:8003/api/sessions", {
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
              <h2 className="text-3xl font-bold text-white mb-2">Who is Your Guide?</h2>
              <p className="text-white/80">Define your Guide's identity and purpose</p>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="agentName" className="text-white font-semibold">Guide Name</Label>
                <Input
                  id="agentName"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  placeholder="e.g., Luna, Marcus, Serena"
                  className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label className="text-white font-semibold">Guide Roles (Select 1-3)</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {[
                    "Stoic Sage",
                    "Manifestation Mentor",
                    "Life Coach",
                    "Fitness Guide",
                    "Spiritual Guide",
                    "Career Advisor",
                    "Wellness Coach",
                    "Mindfulness Teacher"
                  ].map((role) => (
                    <button
                      key={role}
                      onClick={() => toggleRole(role)}
                      disabled={!selectedRoles.includes(role) && selectedRoles.length >= 3}
                      className={`px-4 py-3 rounded-lg font-semibold transition-all text-left ${
                        selectedRoles.includes(role)
                          ? "bg-white text-kurzgesagt-purple"
                          : selectedRoles.length >= 3
                          ? "bg-white/5 text-white/40 cursor-not-allowed"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                </div>
                <p className="text-white/60 text-sm mt-2">
                  {selectedRoles.length}/3 roles selected
                </p>
              </div>

              <div>
                <Label htmlFor="mission" className="text-white font-semibold">Mission & Purpose</Label>
                <div className="relative">
                  <Textarea
                    id="mission"
                    value={mission}
                    onChange={(e) => setMission(e.target.value)}
                    onFocus={() => setIsMissionFocused(true)}
                    onBlur={() => setIsMissionFocused(false)}
                    placeholder="Describe what this Guide will help you achieve..."
                    rows={4}
                    className="mt-2 bg-white/10 border-white/20 text-white placeholder:text-white/50 pr-28"
                  />
                  {(isMissionFocused || mission.trim()) && (
                    <AIHelpButton
                      value={mission}
                      onResult={(suggestion) => setMission(suggestion)}
                    />
                  )}
                </div>
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
              <h2 className="text-3xl font-bold text-white mb-2">Core Attributes</h2>
              <p className="text-white/80">Define your Guide's personality through 4 key controls</p>
            </div>

            <div className="space-y-6">
              {/* Guide Energy */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div>
                    <Label className="text-white font-semibold">Guide Energy</Label>
                    <p className="text-white/60 text-xs mt-1">How your guide presents themselves</p>
                  </div>
                  <span className="text-white/80 text-sm font-mono">{guideControls.guide_energy}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={guideControls.guide_energy}
                  onChange={(e) => setGuideControls({...guideControls, guide_energy: parseInt(e.target.value)})}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-white/60">
                  <span>Calm</span>
                  <span>Balanced</span>
                  <span>Energetic</span>
                </div>
              </div>

              {/* Coaching Style */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div>
                    <Label className="text-white font-semibold">Coaching Style</Label>
                    <p className="text-white/60 text-xs mt-1">Approach to guidance and support</p>
                  </div>
                  <span className="text-white/80 text-sm font-mono">{guideControls.coaching_style}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={guideControls.coaching_style}
                  onChange={(e) => setGuideControls({...guideControls, coaching_style: parseInt(e.target.value)})}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-white/60">
                  <span>Nurturing</span>
                  <span>Balanced</span>
                  <span>Directive</span>
                </div>
              </div>

              {/* Creative Expression */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div>
                    <Label className="text-white font-semibold">Creative Expression</Label>
                    <p className="text-white/60 text-xs mt-1">Communication and ideation style</p>
                  </div>
                  <span className="text-white/80 text-sm font-mono">{guideControls.creative_expression}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={guideControls.creative_expression}
                  onChange={(e) => setGuideControls({...guideControls, creative_expression: parseInt(e.target.value)})}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-white/60">
                  <span>Practical</span>
                  <span>Balanced</span>
                  <span>Imaginative</span>
                </div>
              </div>

              {/* Communication Depth */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div>
                    <Label className="text-white font-semibold">Communication Depth</Label>
                    <p className="text-white/60 text-xs mt-1">Level of detail in responses</p>
                  </div>
                  <span className="text-white/80 text-sm font-mono">{guideControls.communication_depth}/100</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={guideControls.communication_depth}
                  onChange={(e) => setGuideControls({...guideControls, communication_depth: parseInt(e.target.value)})}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-white/60">
                  <span>Concise</span>
                  <span>Balanced</span>
                  <span>Detailed</span>
                </div>
              </div>
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
              <h2 className="text-3xl font-bold text-white mb-2">How Does Your Guide Sound?</h2>
              <p className="text-white/80">Choose the voice that will bring your Guide to life</p>
            </div>

            {isLoadingVoices ? (
              <div className="text-center text-white py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <p>Loading voices...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  {availableVoices.map((voice) => (
                    <div
                      key={voice.id}
                      className={`p-4 rounded-lg transition-all cursor-pointer ${
                        selectedVoice?.id === voice.id
                          ? "bg-white text-kurzgesagt-purple border-2 border-white"
                          : "bg-white/10 text-white border-2 border-white/20 hover:bg-white/20"
                      }`}
                      onClick={() => setSelectedVoice(voice)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-bold text-lg">{voice.name}</h3>
                          <p className={`text-sm mt-1 ${selectedVoice?.id === voice.id ? 'text-kurzgesagt-purple/80' : 'text-white/70'}`}>
                            {voice.description}
                          </p>
                          <div className="flex gap-2 mt-2">
                            <span className={`text-xs px-2 py-1 rounded ${selectedVoice?.id === voice.id ? 'bg-kurzgesagt-purple/20' : 'bg-white/20'}`}>
                              {voice.gender}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded ${selectedVoice?.id === voice.id ? 'bg-kurzgesagt-purple/20' : 'bg-white/20'}`}>
                              {voice.accent || voice.age}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            playVoicePreview(voice.id)
                          }}
                          disabled={isPlayingPreview === voice.id}
                          className={`ml-4 px-4 py-2 rounded-lg font-semibold transition-all ${
                            isPlayingPreview === voice.id
                              ? "bg-kurzgesagt-yellow/50 cursor-wait"
                              : "bg-kurzgesagt-yellow text-kurzgesagt-navy hover:bg-kurzgesagt-yellow/90"
                          }`}
                        >
                          {isPlayingPreview === voice.id ? "Playing..." : "Preview"}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {selectedVoice && (
                  <div className="bg-kurzgesagt-yellow/10 border border-kurzgesagt-yellow/30 rounded-xl p-4 mt-4">
                    <p className="text-white/90 text-sm">
                      🎙️ <strong>{selectedVoice.name}</strong> will be your Guide's voice. Use case: {selectedVoice.use_case}
                    </p>
                  </div>
                )}

                {/* Voice Lab Navigation Button */}
                <div className="bg-gradient-to-r from-kurzgesagt-yellow/20 to-kurzgesagt-pink/20 border-2 border-kurzgesagt-yellow/40 rounded-xl p-6 mt-6">
                  <h3 className="text-white font-bold text-xl mb-2">🎙️ Create Your Own Voice</h3>
                  <p className="text-white/80 text-sm mb-4">
                    Record or upload voice samples to clone your own custom voice with AI
                  </p>
                  <Button
                    onClick={() => router.push(`/voice-lab?userId=${userId}`)}
                    className="w-full bg-kurzgesagt-yellow text-kurzgesagt-navy font-bold text-lg py-6 hover:bg-kurzgesagt-yellow/90 transition-all shadow-lg"
                  >
                    Open Voice Lab →
                  </Button>
                </div>
              </div>
            )}
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
              <h2 className="text-3xl font-bold text-white mb-2">What Does Your Guide Look Like?</h2>
              <p className="text-white/80">Create or upload an avatar to give your Guide a visual identity</p>
            </div>

            <div className="space-y-6">
              {/* Avatar Preview */}
              {avatarUrl && (
                <div className="flex justify-center">
                  <div className="relative">
                    <img
                      src={avatarUrl}
                      alt="Guide Avatar"
                      className="w-48 h-48 rounded-full object-cover border-4 border-white shadow-lg"
                    />
                    <button
                      onClick={() => setAvatarUrl(null)}
                      className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600 transition-all"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}

              {/* Generate with DALL·E */}
              <div className="bg-white/10 rounded-xl p-6 space-y-4">
                <h3 className="text-white font-bold text-lg">Generate with AI</h3>
                <p className="text-white/70 text-sm">Describe your Guide and we&apos;ll create an avatar using DALL·E 3</p>

                <Textarea
                  value={avatarPrompt}
                  onChange={(e) => setAvatarPrompt(e.target.value)}
                  placeholder="e.g., A wise elderly woman with kind eyes, wearing flowing robes, serene expression..."
                  rows={3}
                  className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />

                <Button
                  onClick={generateAvatar}
                  disabled={isGeneratingAvatar || !avatarPrompt.trim()}
                  className="w-full bg-kurzgesagt-purple text-white hover:bg-kurzgesagt-purple/90"
                >
                  {isGeneratingAvatar ? "Generating..." : "Generate Avatar"}
                </Button>
              </div>

              {/* Upload Custom Image */}
              <div className="bg-white/10 rounded-xl p-6 space-y-4">
                <h3 className="text-white font-bold text-lg">Upload Custom Avatar</h3>
                <p className="text-white/70 text-sm">Upload your own image (PNG, JPG, WEBP, max 5MB)</p>

                <div className="relative">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={uploadAvatar}
                    disabled={isUploadingAvatar}
                    className="block w-full text-sm text-white
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-lg file:border-0
                      file:text-sm file:font-semibold
                      file:bg-white file:text-kurzgesagt-purple
                      hover:file:bg-white/90
                      file:cursor-pointer cursor-pointer"
                  />
                </div>

                {isUploadingAvatar && (
                  <p className="text-white/70 text-sm">Uploading...</p>
                )}
              </div>

              {/* Skip Option */}
              <div className="text-center">
                <p className="text-white/60 text-sm">
                  You can add an avatar later from your dashboard
                </p>
              </div>
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
              <h2 className="text-3xl font-bold text-white mb-2">Communication Style</h2>
              <p className="text-white/80">Define how your Guide speaks and interacts</p>
            </div>

            <div className="space-y-4">
              <div>
                <Label className="text-white font-semibold">Interaction Styles (Select 1-3)</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {[
                    "Encouraging",
                    "Analytical",
                    "Compassionate",
                    "Direct",
                    "Gentle",
                    "Motivational",
                    "Reflective",
                    "Supportive"
                  ].map((style) => (
                    <button
                      key={style}
                      onClick={() => toggleInteractionStyle(style)}
                      disabled={!selectedInteractionStyles.includes(style) && selectedInteractionStyles.length >= 3}
                      className={`px-4 py-3 rounded-lg font-semibold transition-all ${
                        selectedInteractionStyles.includes(style)
                          ? "bg-white text-kurzgesagt-purple"
                          : selectedInteractionStyles.length >= 3
                          ? "bg-white/5 text-white/40 cursor-not-allowed"
                          : "bg-white/10 text-white hover:bg-white/20"
                      }`}
                    >
                      {style}
                    </button>
                  ))}
                </div>
                <p className="text-white/60 text-sm mt-2">
                  {selectedInteractionStyles.length}/3 styles selected
                </p>
                <p className="text-white/80 text-sm mt-3 bg-white/10 p-3 rounded-lg">
                  💬 This Guide is optimized for creating <strong>speech-ready scripts</strong> for ElevenLabs voice synthesis.
                </p>
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
              <h2 className="text-3xl font-bold text-white mb-2">Manifestation Focus Areas</h2>
              <p className="text-white/80">Select the areas you want your Guide to specialize in</p>
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

      case 7:
        return (
          <motion.div
            key="step7"
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

      case 8:
        return (
          <motion.div
            key="step8"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">Review & Create</h2>
              <p className="text-white/80">Review your Guide and create your personalized companion</p>
            </div>

            <div className="glass-card p-6 rounded-2xl space-y-4">
              <div>
                <h3 className="text-white font-bold mb-2">Agent Name</h3>
                <p className="text-white/80">{agentName || "Not set"}</p>
              </div>
              <div>
                <h3 className="text-white font-bold mb-2">Character Role</h3>
                <p className="text-white/80">{selectedRoles.join(", ") || "Not set"}</p>
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
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
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
                {s < 8 && (
                  <div
                    className={`h-1 w-6 mx-1 transition-all ${
                      s < step ? "bg-kurzgesagt-aqua" : "bg-white/20"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <p className="text-white/80 text-center">
            Step {step} of 8: {
              ["Identity", "Attributes", "Voice", "Avatar", "Communication", "Focus", "Philosophy", "Review"][step - 1]
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

          {step < 8 ? (
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
              {isSubmitting ? "Creating..." : "Create My Guide ✨"}
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

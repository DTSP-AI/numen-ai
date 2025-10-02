"use client"

import { useState } from "react"
import { motion } from "framer-motion"

interface Affirmation {
  id: string
  affirmation_text: string
  category: string
  audio_url: string | null
  play_count: number
  is_favorite: boolean
  created_at: string
}

interface Props {
  affirmation: Affirmation
  onUpdate: () => void
  userId?: string
}

export function AffirmationCard({ affirmation, onUpdate, userId = "00000000-0000-0000-0000-000000000001" }: Props) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [audio, setAudio] = useState<HTMLAudioElement | null>(() =>
    typeof Audio !== "undefined" && affirmation.audio_url
      ? new Audio(`http://localhost:8000${affirmation.audio_url}`)
      : null
  )

  const categoryColors = {
    identity: "from-kurzgesagt-yellow to-kurzgesagt-orange",
    gratitude: "from-kurzgesagt-aqua to-kurzgesagt-teal",
    action: "from-kurzgesagt-purple to-kurzgesagt-indigo",
    visualization: "from-kurzgesagt-coral to-kurzgesagt-purple",
  }

  const categoryColor = categoryColors[affirmation.category as keyof typeof categoryColors] || "from-gray-400 to-gray-600"

  const handlePlay = async () => {
    if (!audio) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      audio.play()
      setIsPlaying(true)

      // Record play event
      await fetch(`http://localhost:8000/api/affirmations/${affirmation.id}/play`, {
        method: "POST"
      })
      onUpdate()
    }

    audio.onended = () => setIsPlaying(false)
  }

  const handleFavorite = async () => {
    await fetch(`http://localhost:8000/api/affirmations/${affirmation.id}/favorite?is_favorite=${!affirmation.is_favorite}`, {
      method: "PATCH"
    })
    onUpdate()
  }

  const handleSynthesize = async () => {
    setIsSynthesizing(true)
    try {
      const response = await fetch(`http://localhost:8000/api/affirmations/${affirmation.id}/synthesize`, {
        method: "POST",
        headers: {
          "x-user-id": userId
        }
      })

      if (response.ok) {
        const data = await response.json()
        // Create new audio element with synthesized audio
        if (data.audio_url) {
          const newAudio = new Audio(`http://localhost:8000${data.audio_url}`)
          setAudio(newAudio)
        }
        onUpdate()
      } else {
        const error = await response.text()
        console.error("Synthesis failed:", error)
        alert("Audio synthesis failed. Check ELEVENLABS_API_KEY in backend.")
      }
    } catch (error) {
      console.error("Synthesis error:", error)
      alert("Failed to synthesize audio. Please try again.")
    } finally {
      setIsSynthesizing(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className="glass-card rounded-2xl p-6 relative overflow-hidden"
    >
      {/* Category Badge */}
      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${categoryColor}`}>
        {affirmation.category}
      </div>

      {/* Favorite Button */}
      <button
        onClick={handleFavorite}
        className="absolute top-4 left-4 text-2xl transition-transform hover:scale-110"
      >
        {affirmation.is_favorite ? "⭐" : "☆"}
      </button>

      {/* Affirmation Text */}
      <div className="mt-8 mb-6">
        <p className="text-white text-lg leading-relaxed">
          &ldquo;{affirmation.affirmation_text}&rdquo;
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {affirmation.audio_url ? (
            <button
              onClick={handlePlay}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                isPlaying
                  ? "bg-kurzgesagt-coral text-white"
                  : "bg-white/20 text-white hover:bg-white/30"
              }`}
            >
              {isPlaying ? "⏸ Pause" : "▶ Play"}
            </button>
          ) : (
            <button
              onClick={handleSynthesize}
              disabled={isSynthesizing}
              className="px-4 py-2 rounded-lg bg-kurzgesagt-purple text-white font-semibold hover:bg-kurzgesagt-purple/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSynthesizing ? "⏳ Synthesizing..." : "🎤 Generate Voice"}
            </button>
          )}
        </div>

        {/* Stats */}
        <div className="text-white/60 text-sm">
          {affirmation.play_count} plays
        </div>
      </div>
    </motion.div>
  )
}

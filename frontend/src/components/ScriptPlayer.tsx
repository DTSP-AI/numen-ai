"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

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

interface Props {
  script: HypnosisScript
}

export function ScriptPlayer({ script }: Props) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [audio] = useState(() => typeof Audio !== "undefined" && script.audio_url ? new Audio(`http://localhost:8000${script.audio_url}`) : null)

  const handlePlay = () => {
    if (!audio) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      audio.play()
      setIsPlaying(true)
    }

    audio.onended = () => setIsPlaying(false)
  }

  const handleSynthesize = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/scripts/${script.id}/synthesize`, {
        method: "POST"
      })

      if (response.ok) {
        alert("Script audio synthesized successfully!")
        window.location.reload()
      } else {
        alert("Audio synthesis failed. Check ELEVENLABS_API_KEY.")
      }
    } catch (error) {
      console.error("Synthesis error:", error)
      alert("Failed to synthesize audio")
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white mb-2">{script.title}</h3>
          <div className="flex items-center gap-4 text-white/60 text-sm">
            <span>⏱️ {script.duration_minutes} minutes</span>
            <span>🎯 {script.focus_area}</span>
            <span>▶ {script.play_count} plays</span>
          </div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-4 py-2 rounded-lg bg-white/20 text-white hover:bg-white/30 transition-all"
        >
          {isExpanded ? "Hide Script" : "View Script"}
        </button>
      </div>

      {/* Audio Controls */}
      <div className="flex gap-3 mb-4">
        {script.audio_url ? (
          <button
            onClick={handlePlay}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${
              isPlaying
                ? "bg-kurzgesagt-coral text-white"
                : "bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-indigo text-white hover:opacity-90"
            }`}
          >
            {isPlaying ? "⏸️ Pause Session" : "▶️ Start Session"}
          </button>
        ) : (
          <button
            onClick={handleSynthesize}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white font-semibold hover:opacity-90 transition-all"
          >
            🎤 Synthesize Audio
          </button>
        )}

        <button className="px-4 py-3 rounded-xl bg-white/20 text-white hover:bg-white/30 transition-all">
          📥 Download
        </button>
      </div>

      {/* Script Text */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="bg-white/10 rounded-xl p-6 mt-4 max-h-96 overflow-y-auto">
              <p className="text-white/80 leading-relaxed whitespace-pre-wrap">
                {script.script_text}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pacing Markers (if available) */}
      {script.audio_url && (
        <div className="mt-4 p-4 bg-white/5 rounded-lg">
          <div className="text-white/60 text-sm mb-2">Session Progress</div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-kurzgesagt-aqua to-kurzgesagt-purple"
              initial={{ width: "0%" }}
              animate={{ width: isPlaying ? "100%" : "0%" }}
              transition={{ duration: script.duration_minutes * 60, ease: "linear" }}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

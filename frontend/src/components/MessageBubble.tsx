"use client"

import { useState } from "react"
import { motion } from "framer-motion"

interface Message {
  id: string
  role: "user" | "agent"
  content: string
  timestamp: string
  audio_url?: string
}

interface MessageBubbleProps {
  message: Message
  isLatest: boolean
}

export function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const isAgent = message.role === "agent"

  const playAudio = () => {
    if (!message.audio_url) return

    const audio = new Audio(message.audio_url)
    setIsPlayingAudio(true)

    audio.onended = () => setIsPlayingAudio(false)
    audio.onerror = () => setIsPlayingAudio(false)

    audio.play()
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isAgent ? "justify-start" : "justify-end"}`}
    >
      {isAgent && (
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral flex items-center justify-center text-lg flex-shrink-0">
          🤖
        </div>
      )}

      <div className={`flex flex-col ${isAgent ? "items-start" : "items-end"} max-w-[70%]`}>
        {/* Message Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl ${
            isAgent
              ? "bg-white/10 backdrop-blur-sm border border-white/20 rounded-tl-sm"
              : "bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white rounded-tr-sm"
          }`}
        >
          <p className={`text-sm leading-relaxed ${isAgent ? "text-white" : "text-white"}`}>
            {message.content}
          </p>

          {/* Audio Player (if available) */}
          {message.audio_url && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={playAudio}
              className={`mt-3 flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                isAgent
                  ? "bg-white/10 hover:bg-white/20"
                  : "bg-white/20 hover:bg-white/30"
              }`}
            >
              {isPlayingAudio ? (
                <>
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  >
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                    </svg>
                  </motion.div>
                  <span className="text-xs text-white">Playing...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  <span className="text-xs text-white">Play Audio</span>
                </>
              )}
            </motion.button>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-white/40 mt-1 px-1">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>

      {!isAgent && (
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kurzgesagt-aqua to-kurzgesagt-yellow flex items-center justify-center text-lg flex-shrink-0">
          👤
        </div>
      )}
    </motion.div>
  )
}

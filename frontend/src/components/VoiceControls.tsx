"use client"

import { useState } from "react"
import { motion } from "framer-motion"

interface VoiceControlsProps {
  agentId: string
  sessionId: string
  voiceId?: string
}

export function VoiceControls({ agentId, sessionId, voiceId }: VoiceControlsProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [error] = useState<string | null>(null)

  const connectToVoice = async () => {
    // TODO: Implement LiveKit voice connection
    console.log("Voice connection requested:", { agentId, sessionId, voiceId })
    setIsConnected(true)
  }

  const disconnectFromVoice = () => {
    setIsConnected(false)
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  return (
    <div className="flex items-center gap-3">
      {error && (
        <motion.div
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-red-400 text-sm mr-2"
        >
          {error}
        </motion.div>
      )}

      {!isConnected ? (
        <button
          onClick={connectToVoice}
          className="bg-kurzgesagt-purple text-white px-4 py-2 rounded-lg hover:bg-kurzgesagt-purple/90 transition-all"
        >
          Start Voice Chat
        </button>
      ) : (
        <>
          <button
            onClick={toggleMute}
            className={`px-4 py-2 rounded-lg transition-all ${
              isMuted
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-white/20 text-white hover:bg-white/30"
            }`}
          >
            {isMuted ? "Unmute" : "Mute"}
          </button>

          <button
            onClick={disconnectFromVoice}
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-all"
          >
            End Call
          </button>
        </>
      )}
    </div>
  )
}

"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useVoiceClient, useConnectionState, useLocalParticipant, useRemoteParticipants } from "@livekit/components-react"
import { Room, RoomEvent, ConnectionState } from "livekit-client"

interface VoiceControlsProps {
  agentId: string
  sessionId: string
  voiceId?: string
}

export function VoiceControls({ agentId, sessionId, voiceId }: VoiceControlsProps) {
  const [room] = useState(() => new Room())
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Set up room event listeners
    room.on(RoomEvent.Connected, () => {
      console.log("Connected to LiveKit room")
      setIsConnected(true)
      setIsConnecting(false)
    })

    room.on(RoomEvent.Disconnected, () => {
      console.log("Disconnected from LiveKit room")
      setIsConnected(false)
    })

    room.on(RoomEvent.Reconnecting, () => {
      console.log("Reconnecting to LiveKit room")
      setIsConnecting(true)
    })

    room.on(RoomEvent.Reconnected, () => {
      console.log("Reconnected to LiveKit room")
      setIsConnecting(false)
    })

    return () => {
      room.disconnect()
    }
  }, [room])

  const connectToVoice = async () => {
    setIsConnecting(true)
    setError(null)

    try {
      // Request LiveKit token from backend
      const response = await fetch("http://localhost:8000/api/livekit/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          room_name: `chat-${sessionId}`,
          participant_name: `user-${Date.now()}`,
          metadata: {
            agent_id: agentId,
            session_id: sessionId,
            voice_id: voiceId
          }
        })
      })

      if (!response.ok) {
        throw new Error("Failed to get LiveKit token")
      }

      const data = await response.json()

      // Connect to LiveKit room
      await room.connect(data.url, data.token)

      // Enable microphone
      await room.localParticipant.setMicrophoneEnabled(true)

    } catch (err) {
      console.error("Failed to connect to voice:", err)
      setError("Failed to connect to voice chat")
      setIsConnecting(false)
      setIsConnected(false)
    }
  }

  const disconnectFromVoice = () => {
    room.disconnect()
    setIsConnected(false)
  }

  const toggleMute = async () => {
    if (room.localParticipant) {
      const newMutedState = !isMuted
      await room.localParticipant.setMicrophoneEnabled(!newMutedState)
      setIsMuted(newMutedState)
    }
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

      <AnimatePresence mode="wait">
        {!isConnected && !isConnecting && (
          <motion.button
            key="connect"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={connectToVoice}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white rounded-lg hover:shadow-lg transition-all font-semibold"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
            Start Voice Chat
          </motion.button>
        )}

        {isConnecting && (
          <motion.div
            key="connecting"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
            />
            Connecting...
          </motion.div>
        )}

        {isConnected && (
          <motion.div
            key="connected"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex items-center gap-2"
          >
            {/* Mute/Unmute Button */}
            <button
              onClick={toggleMute}
              className={`p-3 rounded-lg transition-all ${
                isMuted
                  ? "bg-red-500 hover:bg-red-600"
                  : "bg-white/10 hover:bg-white/20"
              }`}
            >
              {isMuted ? (
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>

            {/* Voice Active Indicator */}
            <div className="flex items-center gap-2 px-3 py-2 bg-green-500/20 text-green-400 rounded-lg border border-green-500/40">
              <motion.div
                className="w-2 h-2 bg-green-400 rounded-full"
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              <span className="text-sm font-medium">Voice Active</span>
            </div>

            {/* Disconnect Button */}
            <button
              onClick={disconnectFromVoice}
              className="p-3 bg-red-500 hover:bg-red-600 rounded-lg transition-all"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

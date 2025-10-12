"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"

interface TherapySessionProps {
  sessionId: string
  contractId: string
  onBack: () => void
}

interface Transcript {
  id: string
  speaker: string
  content: string
  timestamp: string
}

export function TherapySession({ sessionId, onBack }: TherapySessionProps) {
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [isActive, setIsActive] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [ws])

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [transcripts])

  const startSession = () => {
    setIsActive(true)

    // Connect to WebSocket
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'
    const wsUrl = API_URL.replace('http', 'ws')
    const websocket = new WebSocket(`${wsUrl}/api/therapy/session/${sessionId}`)

    websocket.onopen = () => {
      console.log('WebSocket connected')
      websocket.send(JSON.stringify({ type: 'start_session' }))
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'session_started') {
        console.log('Session started')
      } else if (data.type === 'transcript') {
        setTranscripts(prev => [...prev, {
          id: data.id,
          speaker: data.speaker,
          content: data.content,
          timestamp: data.timestamp
        }])
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket closed')
    }

    setWs(websocket)
  }

  const endSession = async () => {
    if (ws) {
      ws.send(JSON.stringify({ type: 'end_session' }))
      ws.close()
      setWs(null)
    }

    setIsActive(false)

    // Fetch final transcripts
    try {
      const result = await api.getTranscripts(sessionId)
      setTranscripts(result.transcripts || [])
    } catch (error) {
      console.error('Failed to fetch transcripts:', error)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="text-center">
        <motion.h2
          className="text-4xl lg:text-5xl font-bold text-white mb-4 font-[family-name:var(--font-heading)] tracking-tight"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {isActive ? "Your Session is Live" : "Ready to Begin"}
        </motion.h2>
        <motion.p
          className="text-lg text-white/80"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {isActive
            ? "Relax and listen to your personalized hypnotherapy session"
            : "Click the button below to start your transformative experience"}
        </motion.p>
      </div>

      {/* Session Status */}
      <motion.div
        className="bg-white/10 rounded-2xl p-8 text-center border border-white/20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        {isActive ? (
          <div className="space-y-6">
            <div className="w-32 h-32 mx-auto rounded-full bg-gradient-to-br from-kurzgesagt-purple/30 to-kurzgesagt-aqua/30 flex items-center justify-center">
              <motion.div
                animate={{
                  scale: [1, 1.3, 1],
                  rotate: [0, 180, 360]
                }}
                transition={{
                  repeat: Infinity,
                  duration: 3,
                  ease: "easeInOut"
                }}
                className="w-20 h-20 rounded-full gradient-purple-aqua shadow-lg"
              />
            </div>
            <motion.p
              className="text-white text-xl font-medium"
              animate={{ opacity: [0.7, 1, 0.7] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              Session in progress...
            </motion.p>
          </div>
        ) : (
          <div className="text-white space-y-4">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-kurzgesagt-aqua/20 mb-4">
              <svg
                className="w-10 h-10 text-kurzgesagt-aqua"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="text-xl font-medium mb-2">Session Created</p>
            <div className="inline-flex items-center gap-2 bg-white/10 rounded-lg px-4 py-2">
              <svg
                className="w-4 h-4 text-kurzgesagt-yellow"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm font-mono text-white/70">{sessionId.slice(0, 16)}...</span>
            </div>
          </div>
        )}
      </motion.div>

      {/* Transcripts */}
      <AnimatePresence>
        {transcripts.length > 0 && (
          <motion.div
            className="bg-white/10 rounded-2xl p-6 max-h-96 overflow-y-auto border border-white/20"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h3 className="text-2xl font-bold text-white mb-6 font-[family-name:var(--font-heading)] sticky top-0 bg-white/10 backdrop-blur-sm py-2 -mx-2 px-2 rounded-lg">
              Session Transcript
            </h3>
            <div className="space-y-3">
              {transcripts.map((t, index) => (
                <motion.div
                  key={t.id}
                  initial={{ opacity: 0, x: t.speaker === "agent" ? -20 : 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  className={`p-4 rounded-xl ${
                    t.speaker === "agent"
                      ? "bg-gradient-to-br from-kurzgesagt-purple/30 to-kurzgesagt-purple/10 text-white border-l-4 border-kurzgesagt-purple"
                      : "bg-white/15 text-white border-l-4 border-kurzgesagt-aqua"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${
                      t.speaker === "agent" ? "bg-kurzgesagt-purple" : "bg-kurzgesagt-aqua"
                    }`} />
                    <span className="font-semibold text-sm">
                      {t.speaker === "agent" ? "Therapist" : "You"}
                    </span>
                    <span className="text-xs text-white/60 ml-auto">
                      {new Date(t.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-base leading-relaxed">{t.content}</div>
                </motion.div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Controls */}
      <motion.div
        className="flex gap-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        {!isActive ? (
          <>
            <motion.div
              className="flex-1"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Button
                onClick={startSession}
                className="w-full bg-kurzgesagt-aqua hover:bg-kurzgesagt-aqua-light text-kurzgesagt-navy py-7 text-xl rounded-xl shadow-lg hover:shadow-kurzgesagt-aqua/50 transition-all font-semibold"
              >
                <svg
                  className="w-6 h-6 mr-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Start Session
              </Button>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={onBack}
                variant="outline"
                className="text-white border-white/30 hover:bg-white/10 h-full px-6 rounded-xl transition-all"
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
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </Button>
            </motion.div>
          </>
        ) : (
          <motion.div
            className="w-full"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              onClick={endSession}
              className="w-full bg-kurzgesagt-coral hover:bg-kurzgesagt-coral-light text-white py-7 text-xl rounded-xl shadow-lg hover:shadow-kurzgesagt-coral/50 transition-all font-semibold"
            >
              <svg
                className="w-6 h-6 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
                />
              </svg>
              End Session
            </Button>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  )
}
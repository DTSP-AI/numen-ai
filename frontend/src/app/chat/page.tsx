"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AffirmationCard } from "@/components/AffirmationCard"
import { ScheduleCalendar } from "@/components/ScheduleCalendar"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

interface AgentAsset {
  id: string
  type: "affirmation" | "protocol" | "script"
  title: string
  created_at: string
}

export default function ChatPage() {
  const searchParams = useSearchParams()
  const agentId = searchParams.get("agentId")
  const sessionId = searchParams.get("sessionId")

  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [assets, setAssets] = useState<AgentAsset[]>([])
  const [schedule, setSchedule] = useState([])
  const [affirmations, setAffirmations] = useState([])
  const [agentName, setAgentName] = useState("Your Guide")
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const userId = "00000000-0000-0000-0000-000000000001"

  useEffect(() => {
    loadChatHistory()
    loadAgentAssets()
    loadAgentInfo()
  }, [agentId, sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const loadChatHistory = async () => {
    if (!sessionId) return

    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${sessionId}/messages`)
      const data = await response.json()
      setMessages(data.messages || [])
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }

  const loadAgentAssets = async () => {
    if (!agentId) return

    try {
      // Load affirmations created by this agent
      const affirmationsRes = await fetch(`http://localhost:8000/api/affirmations/agent/${agentId}`)
      const affirmationsData = await affirmationsRes.json()
      setAffirmations(affirmationsData.affirmations || [])

      // Load schedule
      const scheduleRes = await fetch(`http://localhost:8000/api/dashboard/user/${userId}`)
      const scheduleData = await scheduleRes.json()
      setSchedule(scheduleData.schedule || [])

      // Combine assets
      const allAssets: AgentAsset[] = [
        ...(affirmationsData.affirmations || []).map((a: any) => ({
          id: a.id,
          type: "affirmation" as const,
          title: a.affirmation_text.slice(0, 50) + "...",
          created_at: a.created_at,
        })),
      ]
      setAssets(allAssets)
    } catch (error) {
      console.error("Failed to load agent assets:", error)
    }
  }

  const loadAgentInfo = async () => {
    if (!agentId) return

    try {
      const response = await fetch(`http://localhost:8000/api/agents/${agentId}`)
      const data = await response.json()
      setAgentName(data.name || "Your Guide")
    } catch (error) {
      console.error("Failed to load agent info:", error)
    }
  }

  const sendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsTyping(true)

    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${sessionId}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          agent_id: agentId,
        }),
      })

      const data = await response.json()

      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: "assistant",
        content: data.response || "I'm here to help guide you.",
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Reload assets if new ones were created
      if (data.assets_created) {
        loadAgentAssets()
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        role: "assistant",
        content: "Sorry, I'm having trouble connecting. Please try again.",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt flex">
      {/* Sidebar - Agent Assets & Schedule */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.aside
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-80 bg-white/10 backdrop-blur-xl border-r border-white/20 overflow-y-auto flex-shrink-0"
          >
            <div className="p-6 space-y-6">
              {/* Agent Info */}
              <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-xl font-bold">
                    {agentName[0]}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-lg">{agentName}</h3>
                    <p className="text-white/60 text-sm">Your Manifestation Guide</p>
                  </div>
                </div>
              </div>

              {/* Recent Assets */}
              <div>
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Your Assets ({assets.length})
                </h3>
                <div className="space-y-2">
                  {assets.slice(0, 5).map((asset) => (
                    <motion.div
                      key={asset.id}
                      whileHover={{ scale: 1.02 }}
                      className="glass-card p-3 rounded-xl cursor-pointer"
                    >
                      <div className="flex items-start gap-2">
                        <div className={`w-2 h-2 rounded-full mt-1.5 ${
                          asset.type === "affirmation" ? "bg-kurzgesagt-aqua" :
                          asset.type === "protocol" ? "bg-kurzgesagt-purple" :
                          "bg-kurzgesagt-yellow"
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm truncate">{asset.title}</p>
                          <p className="text-white/50 text-xs">
                            {new Date(asset.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {assets.length === 0 && (
                    <p className="text-white/40 text-sm text-center py-4">
                      No assets yet. Start chatting!
                    </p>
                  )}
                </div>
              </div>

              {/* Affirmations Preview */}
              {affirmations.length > 0 && (
                <div>
                  <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                    Your Affirmations
                  </h3>
                  <div className="space-y-3">
                    {affirmations.slice(0, 3).map((affirmation: any) => (
                      <div key={affirmation.id} className="glass-card p-4 rounded-xl">
                        <p className="text-white text-sm leading-relaxed">
                          {affirmation.affirmation_text}
                        </p>
                        {affirmation.audio_url && (
                          <button className="mt-2 text-kurzgesagt-aqua text-xs flex items-center gap-1">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" />
                            </svg>
                            Play Audio
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Schedule */}
              {schedule.length > 0 && (
                <div>
                  <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Upcoming
                  </h3>
                  <div className="glass-card p-4 rounded-xl">
                    <p className="text-white/60 text-sm">Next session in 2 days</p>
                  </div>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white/10 backdrop-blur-xl border-b border-white/20 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-2xl font-bold text-white">Chat with {agentName}</h1>
            </div>
            <Button
              variant="outline"
              className="text-white border-white/30 hover:bg-white/10"
              onClick={() => window.location.href = "/dashboard"}
            >
              Dashboard
            </Button>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <div className="w-20 h-20 mx-auto mb-6 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-3xl">
                  💬
                </div>
                <h2 className="text-3xl font-bold text-white mb-3">Start Your Journey</h2>
                <p className="text-white/60 text-lg">Ask me anything about your manifestation goals</p>
              </motion.div>
            )}

            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20, x: message.role === "user" ? 20 : -20 }}
                animate={{ opacity: 1, y: 0, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl ${
                    message.role === "user"
                      ? "bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-purple/80"
                      : "glass-card"
                  } rounded-2xl p-5 shadow-lg`}
                >
                  <div className="flex items-start gap-3">
                    {message.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                        {agentName[0]}
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="text-white leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                      <p className="text-white/40 text-xs mt-2">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    {message.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                        You
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}

            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="glass-card rounded-2xl p-5">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-sm font-bold">
                      {agentName[0]}
                    </div>
                    <div className="flex gap-1">
                      <motion.div
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 1, delay: 0 }}
                        className="w-2 h-2 rounded-full bg-white/60"
                      />
                      <motion.div
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
                        className="w-2 h-2 rounded-full bg-white/60"
                      />
                      <motion.div
                        animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
                        className="w-2 h-2 rounded-full bg-white/60"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-white/20 bg-white/5 backdrop-blur-xl p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-white/40 rounded-xl px-5 py-6 text-lg focus:ring-2 focus:ring-kurzgesagt-purple"
                disabled={isTyping}
              />
              <Button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-aqua hover:opacity-90 text-white px-8 rounded-xl text-lg font-semibold shadow-lg disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

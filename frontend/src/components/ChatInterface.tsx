"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { MessageBubble } from "@/components/MessageBubble"
import { resolveAvatarUrl } from "@/lib/avatar-utils"

interface Message {
  id: string
  role: "user" | "agent"
  content: string
  timestamp: string
  audio_url?: string
}

interface ChatInterfaceProps {
  agentId: string
  sessionId: string
  userId: string
  agentName: string
  agentVoiceId?: string
}

export function ChatInterface({
  agentId,
  sessionId,
  userId,
  agentName,
  agentVoiceId
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [agentAvatar, setAgentAvatar] = useState<string | null>(null)
  const [isVoiceConnected, setIsVoiceConnected] = useState(false)
  const [isVoiceMuted, setIsVoiceMuted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadMessages()
    loadAgentAvatar()
  }, [sessionId, agentId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const loadMessages = async () => {
    if (!sessionId) return

    try {
      const response = await fetch(`http://localhost:8003/api/chat/sessions/${sessionId}/messages`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error("Failed to load messages:", error)
    }
  }

  const loadAgentAvatar = async () => {
    try {
      const response = await fetch(`http://localhost:8003/api/agents/${agentId}`, {
        headers: {
          'x-tenant-id': '00000000-0000-0000-0000-000000000001',
          'x-user-id': userId
        }
      })
      if (response.ok) {
        const data = await response.json()
        const avatarUrl = data.contract?.identity?.avatar_url
        if (avatarUrl) {
          // Resolve relative URLs to absolute URLs
          setAgentAvatar(resolveAvatarUrl(avatarUrl))
        }
      }
    } catch (error) {
      console.error("Failed to load agent avatar:", error)
    }
  }

  const sendMessage = async () => {
    if (!inputValue.trim() || isSending) return

    const userMessage = inputValue.trim()
    setInputValue("")
    setIsSending(true)

    // Add user message optimistically
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      // Send message to backend
      const response = await fetch(`http://localhost:8003/api/chat/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          agent_id: agentId,
          message: userMessage
        })
      })

      if (response.ok) {
        const data = await response.json()

        // Replace temp message and add agent response
        setMessages(prev => {
          const filtered = prev.filter(m => m.id !== tempUserMessage.id)
          return [
            ...filtered,
            data.user_message,
            data.agent_response
          ]
        })
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      // Remove temp message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const connectToVoice = async () => {
    // TODO: Implement LiveKit voice connection
    console.log("Voice connection requested:", { agentId, sessionId, agentVoiceId })
    setIsVoiceConnected(true)
  }

  const disconnectFromVoice = () => {
    setIsVoiceConnected(false)
    setIsVoiceMuted(false)
  }

  const toggleVoiceMute = () => {
    setIsVoiceMuted(!isVoiceMuted)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header - Hidden on mobile */}
      <div className="hidden md:flex glass-card border-b border-white/20 px-6 py-4 items-center justify-between">
        <div className="flex items-center gap-4">
          {agentAvatar ? (
            <img
              src={agentAvatar}
              alt={agentName}
              className="w-12 h-12 rounded-full object-cover ring-2 ring-white/20"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral flex items-center justify-center text-xl font-bold text-white">
              {agentName[0]}
            </div>
          )}
          <div>
            <h2 className="text-xl font-bold text-white">{agentName}</h2>
            <p className="text-sm text-white/60">Your Manifestation Guide</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-12"
            >
              {agentAvatar ? (
                <img
                  src={agentAvatar}
                  alt={agentName}
                  className="w-24 h-24 mx-auto mb-6 rounded-full object-cover ring-4 ring-white/30"
                />
              ) : (
                <div className="w-24 h-24 mx-auto mb-6 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-4xl font-bold">
                  {agentName[0]}
                </div>
              )}
              <h3 className="text-2xl font-bold text-white mb-2">Start Your Journey</h3>
              <p className="text-white/60">Ask me anything about your manifestation goals</p>
            </motion.div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
              agentAvatar={agentAvatar}
              agentName={agentName}
            />
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4 items-start"
            >
              {agentAvatar ? (
                <img
                  src={agentAvatar}
                  alt={agentName}
                  className="w-16 h-16 rounded-full object-cover ring-2 ring-white/20 flex-shrink-0 mt-1"
                />
              ) : (
                <div className="w-16 h-16 rounded-full gradient-purple-aqua flex items-center justify-center text-white text-xl font-bold flex-shrink-0 mt-1">
                  {agentName[0]}
                </div>
              )}
              <div className="glass-card px-4 py-3 rounded-2xl rounded-tl-sm">
                <div className="flex gap-1">
                  <motion.div
                    className="w-2 h-2 bg-white/60 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-white/60 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-white/60 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="glass-card border-t border-white/20 px-6 py-4">
        <div className="flex gap-3 items-end">
          <Textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-1 resize-none bg-white/10 border-white/20 text-white placeholder:text-white/40 rounded-xl focus:ring-2 focus:ring-kurzgesagt-purple min-h-[60px] max-h-[200px]"
            rows={1}
          />

          {/* Voice Chat Button */}
          {!isVoiceConnected ? (
            <motion.button
              onClick={connectToVoice}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white p-4 rounded-xl hover:shadow-lg transition-all"
              title="Start Voice Chat"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </motion.button>
          ) : (
            <div className="flex gap-2">
              {/* Mute/Unmute Button */}
              <motion.button
                onClick={toggleVoiceMute}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`p-4 rounded-xl transition-all ${
                  isVoiceMuted
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-white/20 hover:bg-white/30"
                } text-white`}
                title={isVoiceMuted ? "Unmute" : "Mute"}
              >
                {isVoiceMuted ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
              </motion.button>

              {/* End Call Button */}
              <motion.button
                onClick={disconnectFromVoice}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-red-500 hover:bg-red-600 text-white p-4 rounded-xl transition-all"
                title="End Call"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" />
                </svg>
              </motion.button>
            </div>
          )}

          <Button
            onClick={sendMessage}
            disabled={!inputValue.trim() || isSending}
            className="bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white px-8 py-6 rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSending ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
              />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

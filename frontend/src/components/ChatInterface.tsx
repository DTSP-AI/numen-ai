"use client"

import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { MessageBubble } from "@/components/MessageBubble"
import { VoiceControls } from "@/components/VoiceControls"

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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadMessages()
  }, [sessionId])

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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="glass-card border-b border-white/20 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral flex items-center justify-center text-2xl">
            🤖
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{agentName}</h2>
            <p className="text-sm text-white/60">Your Manifestation Guide</p>
          </div>
        </div>

        {/* Voice Controls */}
        <VoiceControls
          agentId={agentId}
          sessionId={sessionId}
          voiceId={agentVoiceId}
        />
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
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-2xl font-bold text-white mb-2">Start Your Journey</h3>
              <p className="text-white/60">Ask me anything about your manifestation goals</p>
            </motion.div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
            />
          ))}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral flex items-center justify-center text-lg flex-shrink-0">
                🤖
              </div>
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

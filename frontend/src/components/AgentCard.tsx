"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useRouter } from "next/navigation"

interface Agent {
  id: string
  name: string
  type: string
  interaction_count: number
  last_interaction_at: string | null
  created_at: string
  contract?: {
    identity?: {
      avatar_url?: string
    }
  }
}

interface Props {
  agent: Agent
  sessionId?: string
}

export function AgentCard({ agent, sessionId }: Props) {
  const router = useRouter()
  const [showMenu, setShowMenu] = useState(false)
  const typeColors = {
    conversational: "from-kurzgesagt-aqua to-kurzgesagt-teal",
    voice: "from-kurzgesagt-purple to-kurzgesagt-indigo",
    workflow: "from-kurzgesagt-yellow to-kurzgesagt-orange",
    autonomous: "from-kurzgesagt-coral to-kurzgesagt-purple",
  }

  const typeColor = typeColors[agent.type as keyof typeof typeColors] || "from-gray-400 to-gray-600"

  const typeIcons = {
    conversational: "💬",
    voice: "🎙️",
    workflow: "⚙️",
    autonomous: "🤖",
  }

  const typeIcon = typeIcons[agent.type as keyof typeof typeIcons] || "🤖"

  const avatarUrl = agent.contract?.identity?.avatar_url

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    // TODO: Navigate to edit page
    alert(`Edit agent: ${agent.name}`)
  }

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    try {
      // TODO: Implement actual copy logic
      alert(`Copy agent: ${agent.name}`)
    } catch (error) {
      console.error("Failed to copy agent:", error)
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowMenu(false)
    if (confirm(`Are you sure you want to delete ${agent.name}?`)) {
      try {
        // TODO: Implement delete API call
        alert(`Delete agent: ${agent.name}`)
      } catch (error) {
        console.error("Failed to delete agent:", error)
      }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03 }}
      className={`relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br ${typeColor}`}
    >
      {/* Three-dot menu */}
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
          className="p-2 rounded-lg hover:bg-white/20 transition-all text-white"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="5" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="12" cy="19" r="2" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        <AnimatePresence>
          {showMenu && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="absolute right-0 mt-2 w-48 rounded-xl bg-white shadow-2xl overflow-hidden"
            >
              <button
                onClick={handleEdit}
                className="w-full px-4 py-3 text-left hover:bg-gray-100 transition-colors flex items-center gap-3 text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
              </button>
              <button
                onClick={handleCopy}
                className="w-full px-4 py-3 text-left hover:bg-gray-100 transition-colors flex items-center gap-3 text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy
              </button>
              <button
                onClick={handleDelete}
                className="w-full px-4 py-3 text-left hover:bg-red-50 transition-colors flex items-center gap-3 text-red-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Avatar or Icon */}
      <div className="mb-4">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={agent.name}
            className="w-16 h-16 rounded-full object-cover ring-4 ring-white/30"
          />
        ) : (
          <div className="text-4xl">{typeIcon}</div>
        )}
      </div>

      {/* Name */}
      <h3 className="text-xl font-bold text-white mb-2">{agent.name}</h3>

      {/* Type Badge */}
      <div className="inline-block px-3 py-1 rounded-full bg-white/20 text-white text-xs font-semibold mb-4">
        {agent.type}
      </div>

      {/* Stats */}
      <div className="space-y-2 text-white/80 text-sm">
        <div className="flex items-center gap-2">
          <span>💭</span>
          <span>{agent.interaction_count} interactions</span>
        </div>

        {agent.last_interaction_at && (
          <div className="flex items-center gap-2">
            <span>🕐</span>
            <span>Last active: {new Date(agent.last_interaction_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {/* Chat Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => router.push(`/chat/${agent.id}${sessionId ? `?sessionId=${sessionId}` : ''}`)}
        className="mt-4 w-full px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-semibold transition-all"
      >
        Chat with Agent →
      </motion.button>

      {/* Decorative Element */}
      <div className="absolute -right-8 -bottom-8 w-32 h-32 rounded-full bg-white/10 blur-2xl" />
    </motion.div>
  )
}

"use client"

import { motion } from "framer-motion"
import { useRouter } from "next/navigation"

interface Agent {
  id: string
  name: string
  type: string
  interaction_count: number
  last_interaction_at: string | null
  created_at: string
}

interface Props {
  agent: Agent
  sessionId?: string
}

export function AgentCard({ agent, sessionId }: Props) {
  const router = useRouter()
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

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03 }}
      className={`relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br ${typeColor} cursor-pointer`}
    >
      {/* Icon */}
      <div className="text-4xl mb-4">{typeIcon}</div>

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

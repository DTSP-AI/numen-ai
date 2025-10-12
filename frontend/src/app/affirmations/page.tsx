"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import { AffirmationCard } from "@/components/AffirmationCard"

interface Affirmation {
  id: string
  affirmation_text: string
  category: string
  audio_url: string | null
  play_count: number
  is_favorite: boolean
  created_at: string
}

export default function AffirmationsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const userId = searchParams.get("userId") || "00000000-0000-0000-0000-000000000001"

  const [affirmations, setAffirmations] = useState<Affirmation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAffirmations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  const loadAffirmations = async () => {
    try {
      const response = await fetch(`http://localhost:8003/api/affirmations/user/${userId}`)
      const data = await response.json()
      setAffirmations(data.affirmations || [])
    } catch (error) {
      console.error("Failed to load affirmations:", error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-white border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-kurzgesagt">
      <div className="container mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <h1 className="text-5xl lg:text-6xl font-bold text-white mb-4">
            Your Personalized Affirmations
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Based on your goals and preferences, we&apos;ve created these powerful affirmations for you
          </p>
        </motion.div>

        {/* Affirmations Grid */}
        {affirmations.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
          >
            {affirmations.map((affirmation, index) => (
              <motion.div
                key={affirmation.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <AffirmationCard affirmation={affirmation} onUpdate={loadAffirmations} />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card p-12 rounded-3xl text-center"
          >
            <p className="text-white/80 text-xl mb-6">
              No affirmations generated yet. Let&apos;s create some for you!
            </p>
            <button
              onClick={() => router.push("/")}
              className="px-8 py-4 bg-white text-kurzgesagt-purple font-semibold rounded-xl hover:bg-white/90 transition-all transform hover:scale-105"
            >
              Start Your Journey
            </button>
          </motion.div>
        )}

        {/* CTA Section */}
        {affirmations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-center"
          >
            <button
              onClick={() => router.push("/dashboard")}
              className="px-12 py-5 bg-white text-kurzgesagt-purple text-xl font-bold rounded-xl hover:bg-white/90 transition-all transform hover:scale-105 shadow-2xl"
            >
              Go to Dashboard
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

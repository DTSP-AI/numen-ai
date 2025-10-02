"use client"

import { motion } from "framer-motion"

export default function AboutPage() {
  return (
    <div className="min-h-screen gradient-kurzgesagt">
      <div className="container mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-4xl mx-auto"
        >
          <h1 className="text-5xl lg:text-6xl font-bold text-white mb-8">About Numen AI</h1>

          <div className="glass-card p-8 lg:p-12 rounded-3xl space-y-6">
            <p className="text-xl text-white/90 leading-relaxed">
              Numen AI is your personal manifestation companion, combining ancient wisdom
              with cutting-edge artificial intelligence to unlock your highest potential.
            </p>

            <h2 className="text-3xl font-bold text-white mt-8 mb-4">Our Mission</h2>
            <p className="text-lg text-white/80 leading-relaxed">
              We believe that everyone has a Divine Spark waiting to be ignited. Our mission
              is to provide personalized, AI-powered tools that help you manifest your dreams,
              transform limiting beliefs, and step into your most authentic self.
            </p>

            <h2 className="text-3xl font-bold text-white mt-8 mb-4">How It Works</h2>
            <p className="text-lg text-white/80 leading-relaxed">
              Through a compassionate intake process, our AI learns your unique goals,
              challenges, and aspirations. It then creates personalized affirmations, mantras,
              and hypnosis sessions tailored specifically to your transformation journey.
            </p>

            <div className="mt-8 pt-8 border-t border-white/20">
              <p className="text-white/60 text-sm">
                Built with love and powered by advanced AI technology to support your growth.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

"use client"

import { useRouter } from "next/navigation"
import { motion } from "framer-motion"

export default function Home() {
  const router = useRouter()

  return (
    <main className="min-h-screen gradient-kurzgesagt relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-kurzgesagt-purple/20 blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-kurzgesagt-aqua/20 blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      <div className="container mx-auto px-6 py-40 lg:py-48 relative z-10">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <motion.div
            className="text-center mb-32 lg:mb-40"
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h1 className="text-6xl lg:text-7xl font-bold text-white mb-12 font-[family-name:var(--font-heading)] tracking-tight">
              Numen AI
            </h1>
            <p className="text-xl lg:text-2xl text-white/90 max-w-2xl mx-auto leading-relaxed mb-16">
              Your personal AI companion for manifestation, alignment, and transformation.
              <span className="block mt-2">
                Discover the next evolution of intentional living.
              </span>
            </p>

            {/* Hero CTA */}
            <motion.button
              onClick={() => router.push('/create-agent?userId=00000000-0000-0000-0000-000000000001')}
              className="px-10 py-4 bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white text-xl font-bold rounded-xl shadow-2xl hover:shadow-kurzgesagt-purple/50 hover:scale-105 transition-all duration-300 inline-flex items-center gap-3"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Create Your Guide
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </motion.button>
          </motion.div>
        </div>
      </div>

      {/* Section 1: About (Mission Statement) */}
      <section className="relative py-24 lg:py-32 overflow-hidden bg-gradient-to-br from-kurzgesagt-teal via-kurzgesagt-purple to-kurzgesagt-indigo">
        {/* Decorative floating elements */}
        <motion.div
          className="absolute top-20 right-32 w-32 h-32 opacity-20"
          animate={{
            y: [0, -20, 0],
            rotate: [0, 10, 0],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="45" stroke="white" strokeWidth="2" />
            <circle cx="50" cy="50" r="30" stroke="white" strokeWidth="2" />
            <circle cx="50" cy="50" r="15" fill="white" />
          </svg>
        </motion.div>
        <motion.div
          className="absolute bottom-24 left-20 w-40 h-40 opacity-15"
          animate={{
            y: [0, 15, 0],
            rotate: [0, -15, 0],
          }}
          transition={{
            duration: 7,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 10 L90 90 L10 90 Z" stroke="white" strokeWidth="2" fill="none" />
            <path d="M50 30 L70 70 L30 70 Z" stroke="white" strokeWidth="2" fill="white" opacity="0.3" />
          </svg>
        </motion.div>

        <div className="container mx-auto px-6 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="max-w-4xl"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-8">
              About Numen AI
            </h2>
            <p className="text-xl lg:text-2xl text-white/90 leading-relaxed max-w-3xl">
              Our mission is to unlock the Divine Spark of Becoming. We blend the Law of Attraction,
              Positive Mindset Training, and Quantum Shifting with modern AI. Your Agent listens,
              learns, and personalizes affirmations, mantras, guided meditations, and hypnosis sessions
              tailored to your unique goals.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Section 2: How It Works */}
      <section className="py-24 lg:py-32 bg-white">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center max-w-7xl mx-auto">
            {/* Left: Illustration Placeholder */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="relative"
            >
              <div className="aspect-square bg-gradient-to-br from-kurzgesagt-aqua/20 to-kurzgesagt-purple/20 rounded-3xl flex items-center justify-center">
                <svg className="w-64 h-64 text-kurzgesagt-purple" viewBox="0 0 100 100" fill="none">
                  <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="2" />
                  <path d="M50 20 L50 80 M20 50 L80 50" stroke="currentColor" strokeWidth="2" />
                  <circle cx="50" cy="50" r="8" fill="currentColor" />
                  <circle cx="50" cy="30" r="4" fill="currentColor" opacity="0.6" />
                  <circle cx="50" cy="70" r="4" fill="currentColor" opacity="0.6" />
                  <circle cx="30" cy="50" r="4" fill="currentColor" opacity="0.6" />
                  <circle cx="70" cy="50" r="4" fill="currentColor" opacity="0.6" />
                </svg>
              </div>
            </motion.div>

            {/* Right: Features List */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
            >
              <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-12">
                How It Works
              </h2>

              <div className="space-y-8 mb-12">
                {/* Feature 1 */}
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-yellow to-kurzgesagt-orange rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Personalized Affirmations & Mantras</h3>
                    <p className="text-gray-600 leading-relaxed">
                      Tailored positive statements that rewire your subconscious mind for success.
                    </p>
                  </div>
                </div>

                {/* Feature 2 */}
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-aqua to-kurzgesagt-teal rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Guided Meditation & Visualization</h3>
                    <p className="text-gray-600 leading-relaxed">
                      Deep relaxation techniques combined with powerful visualization practices.
                    </p>
                  </div>
                </div>

                {/* Feature 3 */}
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-indigo to-kurzgesagt-purple rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Self-Guided Hypnosis</h3>
                    <p className="text-gray-600 leading-relaxed">
                      Aligned with your specific goals for deep subconscious transformation.
                    </p>
                  </div>
                </div>

                {/* Feature 4 */}
                <div className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-coral rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Adaptive AI</h3>
                    <p className="text-gray-600 leading-relaxed">
                      Continuously refines and optimizes content based on your progress every session.
                    </p>
                  </div>
                </div>
              </div>

              {/* CTA Button */}
              <motion.button
                onClick={() => {
                  router.push('/create-agent?userId=00000000-0000-0000-0000-000000000001')
                }}
                className="px-8 py-4 bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white text-lg font-bold rounded-xl shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Start My Journey
              </motion.button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Section 3: Benefits */}
      <section className="py-24 lg:py-32 bg-gradient-to-b from-gray-50 to-white">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
              Transform Your Reality
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Three powerful modalities working in harmony to unlock your highest potential.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
            {/* Card 1: Affirmation */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-kurzgesagt-yellow to-kurzgesagt-orange rounded-xl flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Affirmation</h3>
              <p className="text-gray-600 leading-relaxed">
                Anchor positive beliefs that rewire your subconscious. Daily affirmations create lasting neural pathways toward abundance and success.
              </p>
            </motion.div>

            {/* Card 2: Mantra */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-kurzgesagt-aqua to-kurzgesagt-teal rounded-xl flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Mantra</h3>
              <p className="text-gray-600 leading-relaxed">
                Repeat focused patterns that align with abundance. Sacred sounds and phrases that harmonize your energy with your deepest intentions.
              </p>
            </motion.div>

            {/* Card 3: Hypnotherapy */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-kurzgesagt-indigo to-kurzgesagt-purple rounded-xl flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Guided Hypnosis</h3>
              <p className="text-gray-600 leading-relaxed">
                Relax deeply and unlock change through suggestion. Access the subconscious mind where true transformation begins and old patterns dissolve.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Section 4: Final CTA */}
      <section className="relative py-32 lg:py-40 overflow-hidden bg-gradient-to-br from-kurzgesagt-purple via-kurzgesagt-indigo to-kurzgesagt-navy">
        {/* Floating decorative elements */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-kurzgesagt-teal/10 blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full bg-kurzgesagt-orange/10 blur-3xl"
          animate={{
            scale: [1.3, 1, 1.3],
            opacity: [0.4, 0.2, 0.4],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute top-1/3 right-1/3 w-20 h-20 opacity-20"
          animate={{
            rotate: [0, 360],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 10 L90 50 L50 90 L10 50 Z" stroke="white" strokeWidth="2" fill="white" opacity="0.3" />
          </svg>
        </motion.div>

        <div className="container mx-auto px-6 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h2 className="text-5xl lg:text-6xl font-bold text-white mb-6">
              Your Divine Spark Awaits.
            </h2>
            <p className="text-2xl lg:text-3xl text-white/90 mb-12 max-w-3xl mx-auto">
              Begin your personalized journey now.
            </p>

            <motion.button
              onClick={() => {
                router.push('/create-agent?userId=00000000-0000-0000-0000-000000000001')
              }}
              className="px-12 py-5 bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white text-xl font-bold rounded-xl shadow-2xl hover:shadow-kurzgesagt-purple/50 hover:scale-110 transition-all duration-300 inline-flex items-center gap-3"
              whileHover={{
                scale: 1.1,
                boxShadow: "0 0 40px rgba(124, 58, 237, 0.6)",
              }}
              whileTap={{ scale: 0.95 }}
            >
              Begin Session
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* Section 5: Responsible Use & Compliance - At Bottom */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-5xl mx-auto text-center"
          >
            <p className="text-sm text-gray-500 leading-relaxed">
              <strong>Disclaimer:</strong> Numen AI supports personal growth through affirmations and guided hypnosis.
              It is not a substitute for licensed medical or psychiatric care. All sessions are confidential,
              user data is SOC 2 and HIPAA compliant. If you are experiencing a mental health crisis,
              please contact a healthcare professional or emergency services immediately.
            </p>
          </motion.div>
        </div>
      </section>
    </main>
  )
}
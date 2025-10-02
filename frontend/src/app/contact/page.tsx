"use client"

import { motion } from "framer-motion"

export default function ContactPage() {
  return (
    <div className="min-h-screen gradient-kurzgesagt">
      <div className="container mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-4xl mx-auto"
        >
          <h1 className="text-5xl lg:text-6xl font-bold text-white mb-8">Contact Us</h1>

          <div className="glass-card p-8 lg:p-12 rounded-3xl space-y-6">
            <p className="text-xl text-white/90 leading-relaxed mb-8">
              Have questions or feedback? We&apos;d love to hear from you.
            </p>

            <div className="space-y-6">
              {/* Email */}
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-purple to-kurzgesagt-indigo rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">Email</h3>
                  <a href="mailto:support@numen.ai" className="text-kurzgesagt-aqua hover:text-kurzgesagt-teal transition-colors">
                    support@numen.ai
                  </a>
                </div>
              </div>

              {/* Support Hours */}
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-aqua to-kurzgesagt-teal rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">Support Hours</h3>
                  <p className="text-white/80">Monday - Friday: 9am - 6pm EST</p>
                  <p className="text-white/80">Saturday - Sunday: 10am - 4pm EST</p>
                </div>
              </div>

              {/* FAQ */}
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-kurzgesagt-yellow to-kurzgesagt-orange rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">FAQ</h3>
                  <p className="text-white/80">
                    Check out our{" "}
                    <a href="#" className="text-kurzgesagt-aqua hover:text-kurzgesagt-teal transition-colors">
                      Frequently Asked Questions
                    </a>
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-white/20">
              <p className="text-white/60 text-sm">
                We typically respond within 24 hours during business days.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

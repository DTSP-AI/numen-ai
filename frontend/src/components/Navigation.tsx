"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import { usePathname } from "next/navigation"

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const navItems = [
    { href: "/", label: "Home", icon: "🏠" },
    { href: "/dashboard", label: "Dashboard", icon: "📊" },
    { href: "/about", label: "About", icon: "ℹ️" },
    { href: "/contact", label: "Contact", icon: "📧" },
  ]

  const toggleMenu = () => setIsOpen(!isOpen)

  return (
    <>
      {/* Hamburger Button */}
      <motion.button
        onClick={toggleMenu}
        className="fixed top-6 left-6 z-50 flex flex-col items-center justify-center gap-1.5 hover:opacity-80 transition-all duration-300"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Toggle menu"
      >
        <motion.span
          className="w-7 h-0.5 bg-white rounded-full shadow-lg"
          animate={isOpen ? { rotate: 45, y: 4 } : { rotate: 0, y: 0 }}
          transition={{ duration: 0.3 }}
        />
        <motion.span
          className="w-7 h-0.5 bg-white rounded-full shadow-lg"
          animate={isOpen ? { opacity: 0 } : { opacity: 1 }}
          transition={{ duration: 0.3 }}
        />
        <motion.span
          className="w-7 h-0.5 bg-white rounded-full shadow-lg"
          animate={isOpen ? { rotate: -45, y: -4 } : { rotate: 0, y: 0 }}
          transition={{ duration: 0.3 }}
        />
      </motion.button>

      {/* Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={toggleMenu}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 h-full w-80 bg-gradient-to-br from-kurzgesagt-purple via-kurzgesagt-indigo to-kurzgesagt-navy shadow-2xl z-40 overflow-y-auto"
          >
            <div className="p-8">
              {/* Logo/Title */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="mb-12 mt-16"
              >
                <h2 className="text-3xl font-bold text-white mb-2">Numen AI</h2>
                <p className="text-white/60 text-sm">Your manifestation journey</p>
              </motion.div>

              {/* Navigation Items */}
              <nav className="space-y-2">
                {navItems.map((item, index) => {
                  const isActive = pathname === item.href
                  return (
                    <motion.div
                      key={item.href}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 + index * 0.05 }}
                    >
                      <Link
                        href={item.href}
                        onClick={toggleMenu}
                        className={`flex items-center gap-4 px-6 py-4 rounded-xl transition-all duration-300 ${
                          isActive
                            ? "bg-white text-kurzgesagt-purple shadow-lg"
                            : "text-white hover:bg-white/10"
                        }`}
                      >
                        <span className="text-2xl">{item.icon}</span>
                        <span className="text-lg font-semibold">{item.label}</span>
                      </Link>
                    </motion.div>
                  )
                })}
              </nav>

              {/* Divider */}
              <div className="my-8 h-px bg-white/20" />

              {/* Additional Info */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-white/60 text-sm space-y-4"
              >
                <div>
                  <p className="text-white/80 font-semibold mb-2">Quick Stats</p>
                  <p className="text-xs">Track your progress and manifestation journey</p>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                  <span>Secure & Confidential</span>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

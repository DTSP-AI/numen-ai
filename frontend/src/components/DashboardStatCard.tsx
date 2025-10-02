"use client"

import { motion } from "framer-motion"

interface DashboardStatCardProps {
  label: string
  value: number
  color: string
  delay?: number
}

export function DashboardStatCard({ label, value, color, delay = 0 }: DashboardStatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="glass-card p-6 rounded-2xl transition-all cursor-pointer hover:scale-105 hover:shadow-xl"
      role="button"
      aria-label={`${label}: ${value}`}
      tabIndex={0}
    >
      <div className="text-3xl font-bold mb-2" style={{ color }}>
        {value}
      </div>
      <div className="text-white/80">{label}</div>
    </motion.div>
  )
}

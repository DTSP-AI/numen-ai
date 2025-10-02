"use client"

import { useRef, useEffect } from "react"
import { motion } from "framer-motion"

interface Tab {
  id: string
  label: string
}

interface HorizontalTabsProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  className?: string
}

export function HorizontalTabs({ tabs, activeTab, onTabChange, className = "" }: HorizontalTabsProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Convert vertical scroll to horizontal on trackpads
  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return

    const handleWheel = (e: WheelEvent) => {
      // Only handle horizontal scrolling when deltaY is present but deltaX is minimal
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        e.preventDefault()
        container.scrollLeft += e.deltaY
      }
    }

    container.addEventListener("wheel", handleWheel, { passive: false })
    return () => container.removeEventListener("wheel", handleWheel)
  }, [])

  return (
    <div
      ref={scrollContainerRef}
      className={`flex gap-4 overflow-x-auto scrollbar-hide snap-x snap-mandatory touch-pan-x ${className}`}
      style={{
        WebkitOverflowScrolling: "touch",
        scrollbarWidth: "none",
        msOverflowStyle: "none",
      }}
      role="tablist"
      aria-label="Dashboard navigation"
    >
      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>

      {tabs.map((tab) => {
        const isActive = activeTab === tab.id

        return (
          <motion.button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              px-6 py-3 rounded-xl font-semibold transition-all whitespace-nowrap snap-start
              flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2
              focus:ring-offset-kurzgesagt-purple
              ${
                isActive
                  ? "bg-white text-kurzgesagt-purple shadow-lg"
                  : "glass-card text-white hover:bg-white/20"
              }
            `}
            whileTap={{ scale: 0.95 }}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
          >
            {tab.label}
          </motion.button>
        )
      })}
    </div>
  )
}

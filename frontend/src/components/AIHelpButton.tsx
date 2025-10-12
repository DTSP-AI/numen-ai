"use client"

import { useState } from "react"
import { Sparkles } from "lucide-react"

interface AIHelpButtonProps {
  value: string
  onResult: (suggestion: string) => void
}

export function AIHelpButton({ value, onResult }: AIHelpButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleClick = async () => {
    if (!value || !value.trim()) {
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8003/api/intake/assist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: value }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (data.suggestion) {
        onResult(data.suggestion)
      }
    } catch (error) {
      console.error("AI assist failed:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isLoading || !value?.trim()}
      className="absolute bottom-2 right-2 text-xs text-white/60 flex items-center gap-1 hover:text-kurzgesagt-aqua transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 group"
      aria-label="Get AI help to polish your answer"
      title="Let AI polish your answer"
    >
      <Sparkles
        size={14}
        className={isLoading ? "animate-pulse" : "group-hover:rotate-12 transition-transform"}
      />
      <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-150">
        {isLoading ? "Thinking..." : "AI Help"}
      </span>
    </button>
  )
}

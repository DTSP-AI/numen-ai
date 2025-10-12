"use client"

import React from "react"

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI or use default
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen gradient-kurzgesagt flex items-center justify-center p-4">
          <div className="glass-card p-8 rounded-2xl max-w-md w-full">
            <h2 className="text-2xl font-bold text-white mb-4">Something went wrong</h2>
            <p className="text-white/80 mb-6">
              We encountered an unexpected error. Please try refreshing the page.
            </p>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <p className="text-red-300 text-sm font-mono">
                {this.state.error?.message || "Unknown error"}
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-white text-kurzgesagt-purple font-semibold py-3 px-6 rounded-lg hover:bg-white/90 transition-all"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

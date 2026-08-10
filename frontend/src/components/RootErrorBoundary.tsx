'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class RootErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error('Root ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-4">
          <div className="text-center p-8 rounded-2xl border border-gray-800 bg-gray-900/50 max-w-md">
            <h1 className="text-2xl font-bold mb-3 text-gradient">Something went wrong</h1>
            <p className="text-gray-400 mb-4">
              An unexpected error occurred. Please try again or reload the page.
            </p>
            {this.state.error && (
              <p className="text-xs text-red-400 mb-4 break-all font-mono">
                {this.state.error.message}
              </p>
            )}
            <button
              onClick={this.handleReset}
              className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white hover:from-blue-500 hover:to-purple-500 transition-all"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
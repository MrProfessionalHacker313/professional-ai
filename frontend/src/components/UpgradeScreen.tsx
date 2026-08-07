'use client'

import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import CreditMeter from './CreditMeter'

interface UpgradeScreenProps {
  isOpen: boolean
  onClose?: () => void
  reason?: string
}

export default function UpgradeScreen({ isOpen, onClose, reason }: UpgradeScreenProps) {
  if (!isOpen) return null

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="glass-card p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            {/* Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}

            {/* Header */}
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                ⚡
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Upgrade Your Plan</h2>
              <p className="text-gray-400">
                {reason || "You've reached your plan's limit. Upgrade to unlock unlimited access!"}
              </p>
            </div>

            {/* Current Status */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-white mb-4">Your Current Plan</h3>
              <CreditMeter showDetails={true} />
            </div>

            {/* Benefits */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-white mb-4">Why Upgrade?</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-2xl mb-2">💎</div>
                  <h4 className="text-white font-medium mb-1">More Credits</h4>
                  <p className="text-gray-400 text-sm">Generate more content without daily limits</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-2xl mb-2">🌍</div>
                  <h4 className="text-white font-medium mb-1">All Languages</h4>
                  <p className="text-gray-400 text-sm">Access all 40+ premium languages</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-2xl mb-2">⚡</div>
                  <h4 className="text-white font-medium mb-1">Priority Speed</h4>
                  <p className="text-gray-400 text-sm">Faster response times and routing</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-2xl mb-2">🔒</div>
                  <h4 className="text-white font-medium mb-1">Offline Mode</h4>
                  <p className="text-gray-400 text-sm">Work without internet when needed</p>
                </div>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/pricing"
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white px-6 py-4 rounded-xl font-semibold text-center transition-all glow-purple"
              >
                View All Plans
              </Link>
              {onClose && (
                <button
                  onClick={onClose}
                  className="px-6 py-4 border border-gray-700 hover:border-gray-500 text-gray-300 rounded-xl font-medium transition-all"
                >
                  Maybe Later
                </button>
              )}
            </div>

            {/* Trust Badges */}
            <div className="mt-8 pt-6 border-t border-gray-800">
              <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-gray-400">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Cancel anytime</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>No hidden fees</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Secure payment (settled to Allied Bank, Pakistan)</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>20% credit rollover</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}


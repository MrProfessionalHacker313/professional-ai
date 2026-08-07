'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { creditsApi } from '@/lib/api'

interface CreditInfo {
  balance: number
  total_granted: number
  total_consumed: number
  plan: string
  last_reset_at: string | null
  next_reset_at: string | null
  rollover_percentage: number
  display_text: string
}

interface CreditMeterProps {
  showDetails?: boolean
  onUpgradeClick?: () => void
}

export default function CreditMeter({ showDetails = true, onUpgradeClick }: CreditMeterProps) {
  const [creditInfo, setCreditInfo] = useState<CreditInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCreditInfo()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchCreditInfo, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchCreditInfo = async () => {
    try {
      const response = await creditsApi.getInfo()
      setCreditInfo(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load credit information')
      console.error('Error fetching credits:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/2 mb-4"></div>
        <div className="h-4 bg-gray-700 rounded w-3/4"></div>
      </div>
    )
  }

  if (error || !creditInfo) {
    return (
      <div className="glass-card p-6 border-red-500/30">
        <p className="text-red-400 text-sm">{error || 'Unable to load credits'}</p>
      </div>
    )
  }

  const isFreePlan = creditInfo.plan === 'free'
  const isTrial = creditInfo.plan === 'trial'
  const isPro = creditInfo.plan === 'pro'
  
  // Calculate percentage for progress bar
  const maxCredits = 2000
  const percentage = isFreePlan ? 0 : Math.min((creditInfo.balance / maxCredits) * 100, 100)
  
  // Determine color based on remaining credits
  const getProgressColor = () => {
    if (isFreePlan) return 'from-gray-600 to-gray-500'
    if (percentage > 50) return 'from-green-600 to-green-500'
    if (percentage > 20) return 'from-yellow-600 to-yellow-500'
    return 'from-red-600 to-red-500'
  }

  const getStatusColor = () => {
    if (isFreePlan) return 'text-gray-400'
    if (percentage > 50) return 'text-green-400'
    if (percentage > 20) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">Credits</h3>
          <p className={`text-sm font-medium ${getStatusColor()}`}>
            {creditInfo.display_text}
          </p>
        </div>
        <div className="text-right">
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
            isFreePlan ? 'bg-gray-700 text-gray-300' :
            isTrial ? 'bg-blue-500/20 text-blue-400' :
            'bg-purple-500/20 text-purple-400'
          }`}>
            {isFreePlan ? 'FREE PLAN' : isTrial ? 'TRIAL' : 'PRO PLAN'}
          </span>
        </div>
      </div>

      {/* Progress Bar (only for Pro/Trial) */}
      {!isFreePlan && (
        <div className="mb-4">
          <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              className={`h-full bg-gradient-to-r ${getProgressColor()}`}
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-400">
            <span>0</span>
            <span>{maxCredits.toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* Details */}
      {showDetails && (
        <div className="space-y-2">
          {isFreePlan ? (
            <div className="bg-gray-800/50 rounded-lg p-4">
              <p className="text-sm text-gray-300 mb-2">Free Plan Limits:</p>
              <ul className="text-xs text-gray-400 space-y-1">
                <li>• 3 code generations per day</li>
                <li>• 50 chat messages per day</li>
                <li>• 3 MB vault storage</li>
                <li>• 4 languages (English, Urdu, Hindi, Bengali)</li>
              </ul>
              {onUpgradeClick && (
                <button
                  onClick={onUpgradeClick}
                  className="mt-3 w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                >
                  Upgrade to Pro
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-400 text-xs mb-1">Total Granted</p>
                <p className="text-white font-medium">{creditInfo.total_granted.toLocaleString()}</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-gray-400 text-xs mb-1">Total Consumed</p>
                <p className="text-white font-medium">{creditInfo.total_consumed.toLocaleString()}</p>
              </div>
              {creditInfo.next_reset_at && (
                <div className="bg-gray-800/50 rounded-lg p-3 col-span-2">
                  <p className="text-gray-400 text-xs mb-1">Next Reset</p>
                  <p className="text-white font-medium">
                    {new Date(creditInfo.next_reset_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Low Credits Warning */}
          {!isFreePlan && percentage < 20 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mt-3"
            >
              <p className="text-red-400 text-sm font-medium mb-1">⚠️ Low Credits</p>
              <p className="text-red-300 text-xs">
                You're running low on credits. Consider upgrading your plan or purchasing more credits.
              </p>
              {onUpgradeClick && (
                <button
                  onClick={onUpgradeClick}
                  className="mt-2 w-full bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all"
                >
                  Upgrade Now
                </button>
              )}
            </motion.div>
          )}

          {/* Trial Ending Soon Warning */}
          {isTrial && creditInfo.next_reset_at && (
            <TrialEndingWarning trialEnd={creditInfo.next_reset_at} onUpgrade={onUpgradeClick} />
          )}
        </div>
      )}
    </motion.div>
  )
}

// Trial Ending Warning Component
function TrialEndingWarning({ trialEnd, onUpgrade }: { trialEnd: string; onUpgrade?: () => void }) {
  const [daysLeft, setDaysLeft] = useState<number | null>(null)

  useEffect(() => {
    const calculateDaysLeft = () => {
      const now = new Date()
      const end = new Date(trialEnd)
      const diff = end.getTime() - now.getTime()
      const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
      setDaysLeft(days)
    }

    calculateDaysLeft()
    const interval = setInterval(calculateDaysLeft, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [trialEnd])

  if (daysLeft === null || daysLeft > 3) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg p-3 mt-3 ${
        daysLeft <= 1 
          ? 'bg-red-500/10 border border-red-500/30' 
          : 'bg-yellow-500/10 border border-yellow-500/30'
      }`}
    >
      <p className={`text-sm font-medium mb-1 ${daysLeft <= 1 ? 'text-red-400' : 'text-yellow-400'}`}>
        ⏰ Trial Ending Soon
      </p>
      <p className={`text-xs ${daysLeft <= 1 ? 'text-red-300' : 'text-yellow-300'}`}>
        {daysLeft === 0 
          ? 'Your trial ends today! Subscribe now to continue using Pro features.'
          : `Your trial ends in ${daysLeft} day${daysLeft > 1 ? 's' : ''}. Subscribe now to avoid interruption.`
        }
      </p>
      {onUpgrade && (
        <button
          onClick={onUpgrade}
          className={`mt-2 w-full px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            daysLeft <= 1
              ? 'bg-red-600 hover:bg-red-500 text-white'
              : 'bg-yellow-600 hover:bg-yellow-500 text-white'
          }`}
        >
          Subscribe Now
        </button>
      )}
    </motion.div>
  )
}
'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle2,
  AlertTriangle,
  Shield,
  FileCode,
  Globe,
  Zap,
  Lightbulb,
  TrendingUp,
  FileText,
  Monitor,
  Volume2,
  Radio,
  BookOpen,
  Briefcase,
  Download,
  GitCompare,
  Cpu,
  Mic,
  Newspaper,
} from 'lucide-react'

interface FeaturePanelProps {
  isOpen: boolean
  onClose: () => void
}

const features = [
  { id: 'language', name: 'Language Brain', icon: Globe, color: 'from-blue-500 to-cyan-500' },
  { id: 'hacking', name: 'Hacking Lab', icon: Shield, color: 'from-red-500 to-orange-500' },
  { id: 'project', name: 'Project Assistant', icon: FileCode, color: 'from-green-500 to-emerald-500' },
  { id: 'screenshot', name: 'Screenshot to App', icon: Monitor, color: 'from-purple-500 to-pink-500' },
  { id: 'detective', name: 'AI Detective', icon: AlertTriangle, color: 'from-yellow-500 to-amber-500' },
  { id: 'voice-command', name: 'Voice Command', icon: Mic, color: 'from-indigo-500 to-blue-500' },
  { id: 'memory', name: 'Memory Vault', icon: Zap, color: 'from-pink-500 to-rose-500' },
  { id: 'multi-task', name: 'Multi-Task Master', icon: Zap, color: 'from-orange-500 to-red-500' },
  { id: 'teacher', name: 'Teacher Mode', icon: BookOpen, color: 'from-teal-500 to-green-500' },
  { id: 'business', name: 'Business Advisor', icon: Briefcase, color: 'from-amber-500 to-yellow-500' },
  { id: 'format', name: 'Format Expert', icon: FileText, color: 'from-cyan-500 to-blue-500' },
  { id: 'compatibility', name: 'Compatibility', icon: GitCompare, color: 'from-violet-500 to-purple-500' },
  { id: 'router', name: 'Smart Router', icon: Cpu, color: 'from-fuchsia-500 to-pink-500' },
  { id: 'voice-clone', name: 'Voice Clone', icon: Volume2, color: 'from-sky-500 to-indigo-500' },
  { id: 'news', name: 'News Monitor', icon: Newspaper, color: 'from-lime-500 to-green-500' },
]

export default function NextGenFeaturesToolbar({ isOpen, onClose }: FeaturePanelProps) {
  const [activeFeature, setActiveFeature] = useState<string | null>(null)

  const handleFeatureClick = (featureId: string) => {
    setActiveFeature(featureId)
  }

  const handleBack = () => {
    setActiveFeature(null)
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        className="bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden"
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div>
            <h2 className="text-2xl font-bold text-white">Next-Gen AI Features</h2>
            <p className="text-gray-400 text-sm mt-1">15 world-first AI capabilities</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <CheckCircle2 className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeFeature ? (
            <div>
              <button
                onClick={handleBack}
                className="mb-4 text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                ← Back to features
              </button>
              <FeaturePanel featureId={activeFeature} onClose={onClose} />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {features.map((feature) => (
                <motion.button
                  key={feature.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleFeatureClick(feature.id)}
                  className={`p-4 rounded-xl bg-gradient-to-br ${feature.color} bg-opacity-10 border border-gray-800 hover:border-gray-700 transition-all group`}
                >
                  <feature.icon className="w-8 h-8 text-white mb-2 group-hover:scale-110 transition-transform" />
                  <h3 className="text-white font-medium text-sm">{feature.name}</h3>
                </motion.button>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

function FeaturePanel({ featureId, onClose }: { featureId: string; onClose: () => void }) {
  const feature = features.find(f => f.id === featureId)
  
  if (!feature) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${feature.color} bg-opacity-20`}>
          <feature.icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">{feature.name}</h3>
          <p className="text-gray-400 text-sm">Coming soon - {feature.name} feature panel</p>
        </div>
      </div>
      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
        <p className="text-gray-300">
          The {feature.name} feature is ready to use. Select a specific capability below to get started.
        </p>
      </div>
    </div>
  )
}

'use client'

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Camera, Upload, Loader2, X, Code, Smartphone, Monitor, Tablet, FileCode, Download, Check } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface ScreenshotToAppPanelProps {
  onClose: () => void
}

interface GenerationResult {
  framework: string
  files: { name: string; content: string }[]
  preview_url?: string
  instructions: string
}

export default function ScreenshotToAppPanel({ onClose }: ScreenshotToAppPanelProps) {
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [framework, setFramework] = useState('react')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const frameworks = [
    { value: 'react', label: 'React', icon: Code },
    { value: 'nextjs', label: 'Next.js', icon: Monitor },
    { value: 'flutter', label: 'Flutter', icon: Smartphone },
    { value: 'swiftui', label: 'SwiftUI', icon: Tablet },
    { value: 'html-css', label: 'HTML/CSS', icon: FileCode },
  ]

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImage(file)
      const reader = new FileReader()
      reader.onload = () => setImagePreview(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  const handleGenerate = async () => {
    if (!image) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', image)
      formData.append('framework', framework)
      const response = await featuresApi.screenshotToCode({ image_path: image.name, framework })
      setResult({
        framework,
        files: response.data.files || [
          { name: 'App.tsx', content: '// Generated code will appear here' },
        ],
        instructions: response.data.instructions || 'App generated successfully. Review the code and customize as needed.',
      })
    } catch {
      setError('Failed to generate app from screenshot. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <Camera className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Screenshot to App</h3>
            <p className="text-xs text-gray-400">Generate full app from an image</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs text-gray-400 mb-2 block">Upload Screenshot</label>
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-700 rounded-xl p-6 text-center cursor-pointer hover:border-purple-500/50 transition-colors"
          >
            {imagePreview ? (
              <img src={imagePreview} alt="Preview" className="max-h-32 mx-auto rounded-lg mb-2" />
            ) : (
              <Upload className="w-8 h-8 text-gray-500 mx-auto mb-2" />
            )}
            <p className="text-xs text-gray-400">{image ? image.name : 'Click to upload screenshot'}</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-400 mb-2 block">Target Framework</label>
          <div className="grid grid-cols-2 gap-2">
            {frameworks.map(fw => (
              <button
                key={fw.value}
                onClick={() => setFramework(fw.value)}
                className={`p-3 rounded-lg border transition-all flex items-center gap-2 ${
                  framework === fw.value
                    ? 'border-purple-500/50 bg-purple-500/10'
                    : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                }`}
              >
                <fw.icon className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-white">{fw.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={handleGenerate}
        disabled={!image || loading}
        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
        {loading ? 'Generating App...' : 'Generate App from Screenshot'}
      </button>

      {error && (
        <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 bg-gray-800/50 border border-gray-700 rounded-xl p-4"
        >
          <h4 className="text-sm font-medium text-white mb-2">Generated Files ({result.files.length})</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto mb-3">
            {result.files.map((file, i) => (
              <div key={i} className="flex items-center gap-2 bg-gray-900/50 rounded-lg p-2">
                <FileCode className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-gray-300 flex-1">{file.name}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mb-3">{result.instructions}</p>
          <div className="flex gap-2">
            <button
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(result.files.map(f => f.content).join('\n\n'))
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                } catch (err) {
                  console.error('Failed to copy to clipboard:', err)
                }
              }}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-xs px-3 py-2 rounded-lg flex items-center justify-center gap-1"
            >
              {copied ? <Check className="w-3 h-3" /> : <Download className="w-3 h-3" />}
              {copied ? 'Copied!' : 'Copy Code'}
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

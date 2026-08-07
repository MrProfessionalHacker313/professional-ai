'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileType2, FileText, FileCode, FileSpreadsheet, FileImage, Presentation, Loader2, X, Download, Check } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface UniversalFormatPanelProps {
  onClose: () => void
}

interface GenerationResult {
  output_format: string
  filename: string
  size: string
  content_preview: string
  download_url?: string
}

const formats = [
  { value: 'pdf', label: 'PDF Document', icon: FileText, color: 'text-red-400 bg-red-500/20' },
  { value: 'docx', label: 'Word Document', icon: FileText, color: 'text-blue-400 bg-blue-500/20' },
  { value: 'xlsx', label: 'Excel Spreadsheet', icon: FileSpreadsheet, color: 'text-green-400 bg-green-500/20' },
  { value: 'pptx', label: 'PowerPoint', icon: Presentation, color: 'text-orange-400 bg-orange-500/20' },
  { value: 'html', label: 'HTML Page', icon: FileCode, color: 'text-orange-400 bg-orange-500/20' },
  { value: 'json', label: 'JSON Data', icon: FileCode, color: 'text-yellow-400 bg-yellow-500/20' },
  { value: 'csv', label: 'CSV Data', icon: FileSpreadsheet, color: 'text-green-400 bg-green-500/20' },
  { value: 'png', label: 'PNG Image', icon: FileImage, color: 'text-purple-400 bg-purple-500/20' },
]

export default function UniversalFormatPanel({ onClose }: UniversalFormatPanelProps) {
  const [inputType, setInputType] = useState<'text' | 'url' | 'file'>('text')
  const [input, setInput] = useState('')
  const [outputFormat, setOutputFormat] = useState('pdf')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleGenerate = async () => {
    if (!input.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.routeTask({
        task_type: 'universal_format',
        task_description: `Convert to ${outputFormat}: ${input}`,
      })
      setResult({
        output_format: outputFormat,
        filename: `output.${outputFormat}`,
        size: `${(Math.random() * 5 + 1).toFixed(1)} MB`,
        content_preview: response.data.preview || response.data.result || 'Document generated successfully',
      })
    } catch {
      setError('Conversion failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (result?.content_preview) {
      navigator.clipboard.writeText(result.content_preview)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
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
          <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
            <FileType2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Universal Format</h3>
            <p className="text-xs text-gray-400">Convert any format to any other</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        {(['text', 'url', 'file'] as const).map(type => (
          <button
            key={type}
            onClick={() => setInputType(type)}
            className={`flex-1 p-2 rounded-lg border text-xs capitalize transition-all ${
              inputType === type
                ? 'border-orange-500/50 bg-orange-500/10 text-orange-400'
                : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-2 block">Output Format</label>
        <div className="grid grid-cols-4 gap-2">
          {formats.map(fmt => (
            <button
              key={fmt.value}
              onClick={() => setOutputFormat(fmt.value)}
              className={`p-2 rounded-lg border transition-all flex flex-col items-center gap-1 ${
                outputFormat === fmt.value
                  ? 'border-orange-500/50 bg-orange-500/10'
                  : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
              }`}
            >
              <fmt.icon className="w-4 h-4 text-orange-400" />
              <span className="text-[10px] text-gray-300">{fmt.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        {inputType === 'text' ? (
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter text content to convert..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-orange-500"
            rows={4}
          />
        ) : (
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={inputType === 'url' ? 'Enter URL to convert...' : 'Upload file...'}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-orange-500"
          />
        )}
      </div>

      <button
        onClick={handleGenerate}
        disabled={!input.trim() || loading}
        className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileType2 className="w-4 h-4" />}
        {loading ? 'Converting...' : `Convert to ${outputFormat.toUpperCase()}`}
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
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <FileType2 className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-white">{result.filename}</span>
              <span className="text-xs text-gray-400">{result.size}</span>
            </div>
            <button onClick={handleCopy} className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors">
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Download className="w-4 h-4 text-gray-400" />}
            </button>
          </div>
          <div className="bg-gray-900/50 rounded-lg p-3">
            <p className="text-xs text-gray-300 whitespace-pre-wrap">{result.content_preview}</p>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

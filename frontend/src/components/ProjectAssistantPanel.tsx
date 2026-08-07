'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { FolderOpen, Plus, FileCode, Image, FileText, Settings, Play, Download, Loader2, X, ChevronRight } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface ProjectAssistantPanelProps {
  onClose: () => void
}

interface FileNode {
  name: string
  type: 'file' | 'folder'
  size?: string
  children?: FileNode[]
}

interface ProjectResult {
  project_name: string
  description: string
  tech_stack: string[]
  file_tree: FileNode[]
  readme: string
}

const sampleFileTree: FileNode[] = [
  { name: 'src', type: 'folder', children: [
    { name: 'components', type: 'folder', children: [
      { name: 'Header.tsx', type: 'file', size: '2.1 KB' },
      { name: 'Footer.tsx', type: 'file', size: '1.5 KB' },
      { name: 'Sidebar.tsx', type: 'file', size: '3.2 KB' },
    ]},
    { name: 'pages', type: 'folder', children: [
      { name: 'index.tsx', type: 'file', size: '4.5 KB' },
      { name: 'about.tsx', type: 'file', size: '2.8 KB' },
    ]},
    { name: 'utils', type: 'folder', children: [
      { name: 'api.ts', type: 'file', size: '1.2 KB' },
      { name: 'helpers.ts', type: 'file', size: '0.8 KB' },
    ]},
    { name: 'App.tsx', type: 'file', size: '5.1 KB' },
    { name: 'index.tsx', type: 'file', size: '0.5 KB' },
  ]},
  { name: 'public', type: 'folder', children: [
    { name: 'index.html', type: 'file', size: '1.1 KB' },
    { name: 'favicon.ico', type: 'file', size: '0.2 KB' },
  ]},
  { name: 'package.json', type: 'file', size: '1.8 KB' },
  { name: 'tsconfig.json', type: 'file', size: '0.6 KB' },
  { name: 'README.md', type: 'file', size: '2.3 KB' },
]

export default function ProjectAssistantPanel({ onClose }: ProjectAssistantPanelProps) {
  const [description, setDescription] = useState('')
  const [projectType, setProjectType] = useState('web-app')
  const [framework, setFramework] = useState('react')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProjectResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const projectTypes = [
    { value: 'web-app', label: 'Web Application' },
    { value: 'mobile-app', label: 'Mobile Application' },
    { value: 'api-service', label: 'API Service' },
    { value: 'desktop-app', label: 'Desktop Application' },
    { value: 'library', label: 'Library / Package' },
    { value: 'cli-tool', label: 'CLI Tool' },
  ]

  const frameworks = {
    'web-app': ['react', 'nextjs', 'vue', 'angular', 'svelte'],
    'mobile-app': ['react-native', 'flutter', 'swift', 'kotlin'],
    'api-service': ['express', 'fastapi', 'spring-boot', 'go-gin'],
    'desktop-app': ['electron', 'tauri', 'flutter-desktop'],
    'library': ['typescript', 'python', 'rust'],
    'cli-tool': ['node', 'python', 'rust', 'go'],
  }

  const handleGenerate = async () => {
    if (!description.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.routeTask({
        task_type: 'project_builder',
        task_description: `${projectType} ${framework} ${description}`,
      })
      setResult({
        project_name: description.split(' ').slice(0, 3).join('_') || 'my_project',
        description,
        tech_stack: [framework, 'TypeScript', 'Tailwind CSS'],
        file_tree: sampleFileTree,
        readme: response.data.result || '# Project Generated\n\nYour project has been created successfully.',
      })
    } catch {
      setError('Failed to generate project. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const renderFileTree = (nodes: FileNode[], level = 0) => (
    <div className={`${level > 0 ? 'ml-4' : ''}`}>
      {nodes.map((node, i) => (
        <div key={i} className="flex items-center gap-2 py-1 hover:bg-gray-800/50 rounded px-2 transition-colors">
          {node.type === 'folder' ? (
            <FolderOpen className="w-4 h-4 text-yellow-400" />
          ) : (
            <FileCode className="w-4 h-4 text-blue-400" />
          )}
          <span className="text-xs text-gray-300">{node.name}</span>
          {node.size && <span className="text-[10px] text-gray-500 ml-auto">{node.size}</span>}
          {node.children && <ChevronRight className="w-3 h-3 text-gray-500" />}
        </div>
      ))}
    </div>
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
            <FolderOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Project Assistant</h3>
            <p className="text-xs text-gray-400">Build complete projects with AI</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Project Type</label>
          <select
            value={projectType}
            onChange={(e) => {
              setProjectType(e.target.value)
              setFramework(frameworks[e.target.value as keyof typeof frameworks]?.[0] || 'react')
            }}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500"
          >
            {projectTypes.map(pt => (
              <option key={pt.value} value={pt.value}>{pt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Framework</label>
          <select
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500"
          >
            {(frameworks[projectType as keyof typeof frameworks] || []).map(fw => (
              <option key={fw} value={fw}>{fw}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1 block">Project Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe your project (e.g., A task management app with drag-and-drop)..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:border-green-500"
          rows={3}
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={!description.trim() || loading}
        className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
        {loading ? 'Generating Project...' : 'Generate Project'}
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
          className="mt-4 grid grid-cols-2 gap-4"
        >
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-white mb-2">Project Structure</h4>
            <div className="max-h-48 overflow-y-auto">
              {renderFileTree(result.file_tree)}
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-white mb-2">Tech Stack</h4>
            <div className="flex flex-wrap gap-2 mb-3">
              {result.tech_stack.map(tech => (
                <span key={tech} className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">{tech}</span>
              ))}
            </div>
            <h4 className="text-sm font-medium text-white mb-2">README</h4>
            <div className="bg-gray-900/50 rounded-lg p-2 max-h-32 overflow-y-auto">
              <p className="text-xs text-gray-300 whitespace-pre-wrap">{result.readme}</p>
            </div>
            <div className="flex gap-2 mt-3">
              <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-xs px-3 py-2 rounded-lg flex items-center justify-center gap-1">
                <Download className="w-3 h-3" /> Download
              </button>
              <button className="flex-1 bg-green-600 hover:bg-green-500 text-white text-xs px-3 py-2 rounded-lg flex items-center justify-center gap-1">
                <Play className="w-3 h-3" /> Run
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

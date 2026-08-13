"use client"

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Video,
  Image as ImageIcon,
  Film,
  Sparkles,
  Mic,
  Type,
  Clapperboard,
  Loader2,
  Download,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Upload,
  Music,
  ShieldCheck,
  Wand2,
  Play,
  ChevronDown,
  Languages,
  MonitorPlay,
  BadgeCheck,
  Scissors,
  Sliders,
  Palette,
  Crop,
  Crown,
  Lock,
  Zap,
  WandSparkles
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { mediaApi } from '@/lib/api'
import toast from 'react-hot-toast'

type MediaType = 'video' | 'picture' | 'poster' | 'animation'

interface MediaJob {
  id: string
  media_type: string
  status: string
  progress: number
  progress_stage?: string
  topic: string
  script?: string
  scenes_text?: string
  voice_style?: string
  voice_prompt?: string
  language: string
  duration_seconds: number
  resolution?: string
  format: string
  aspect_ratio: string
  storyboard?: any[]
  scene_count: number
  voice_over_path?: string
  subtitles_path?: string
  accuracy_verified: boolean
  verification_report?: any
  output_path?: string
  output_url?: string
  output_resolution?: string
  output_size_bytes?: number
  error_message?: string
  created_at?: string
  completed_at?: string
}

interface MediaLimits {
  plan: string
  videos_used: number
  pictures_used: number
  animations_used: number
  video_limit: number
  picture_limit: number
  animation_limit: number
  available_durations: number[]
  unlimited: boolean
}

const VOICE_STYLES = [
  { value: 'young_girl', label: 'Young Girl', desc: 'Sweet, youthful female' },
  { value: 'young_boy', label: 'Young Boy', desc: 'Energetic, youthful male' },
  { value: 'adult_male', label: 'Adult Man', desc: 'Mature, deep male' },
  { value: 'adult_female', label: 'Adult Woman', desc: 'Mature, clear female' },
  { value: 'news_anchor', label: 'News Anchor', desc: 'Authoritative broadcast' },
  { value: 'teacher', label: 'Teacher', desc: 'Calm, instructive' },
  { value: 'cartoon', label: 'Cartoon', desc: 'Bright, animated, fun' },
  { value: 'robot', label: 'Robot', desc: 'Synthetic, mechanical' },
  { value: 'villain', label: 'Villain', desc: 'Dark, dramatic, menacing' },
  { value: 'hero', label: 'Hero', desc: 'Strong, confident, heroic' },
  { value: 'whisper', label: 'Whisper', desc: 'Soft, whispered, intimate' },
  { value: 'angry', label: 'Angry', desc: 'Intense, aggressive' },
  { value: 'happy', label: 'Happy', desc: 'Cheerful, upbeat, joyful' },
  { value: 'sad', label: 'Sad', desc: 'Melancholic, somber' },
  { value: 'excited', label: 'Excited', desc: 'Enthusiastic, high-energy' },
  { value: 'clone', label: 'My Cloned Voice', desc: 'Custom cloned voice' }
]

const RESOLUTIONS = ['720p', '1080p', '4k', '8k']
const FORMATS = ['mp4', 'png', 'gif', 'webp', 'mov']
const ASPECT_RATIOS = ['16:9', '9:16', '1:1']
const SCRIPT_STYLES = ['professional', 'cinematic', 'storytelling', 'educational', 'promotional', 'documentary', 'viral', 'news']
const PROMPT_STYLES = ['cinematic', 'photorealistic', 'anime', '3d', 'pixel_art', 'watercolor', 'cyberpunk', 'minimalist']
const PROMPT_MOODS = ['dramatic', 'happy', 'mysterious', 'epic', 'calm', 'dark', 'bright', 'nostalgic']
const CAMERA_ANGLES = ['wide', 'close_up', 'extreme_close_up', 'medium', 'low_angle', 'high_angle', 'overhead', 'dutch_angle', 'tracking', 'aerial']
const LIGHTING_OPTIONS = ['golden_hour', 'neon', 'studio', 'natural', 'dramatic', 'soft', 'hard', 'backlit', 'low_key', 'high_key']
const SPEED_OPTIONS = [
  { value: 'standard', label: 'Standard', desc: 'Normal speed' },
  { value: 'fast', label: 'Fast', desc: '2x faster' },
  { value: 'ultra_fast', label: '⚡ Ultra Fast', desc: 'PRO only — 4x faster', pro: true },
]
const LANGUAGES = [
  { code: 'en', name: 'English' }, { code: 'ur', name: 'Urdu' },
  { code: 'hi', name: 'Hindi' }, { code: 'bn', name: 'Bengali' },
  { code: 'ar', name: 'Arabic' }, { code: 'fa', name: 'Persian' },
  { code: 'pa', name: 'Punjabi' }, { code: 'ps', name: 'Pashto' },
  { code: 'sd', name: 'Sindhi' }, { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' }, { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' }, { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' }, { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' }, { code: 'ko', name: 'Korean' },
  { code: 'tr', name: 'Turkish' }, { code: 'nl', name: 'Dutch' },
  { code: 'pl', name: 'Polish' }, { code: 'uk', name: 'Ukrainian' },
  { code: 'id', name: 'Indonesian' }, { code: 'ms', name: 'Malay' },
  { code: 'th', name: 'Thai' }, { code: 'vi', name: 'Vietnamese' },
  { code: 'fil', name: 'Filipino' }, { code: 'sw', name: 'Swahili' },
  { code: 'ta', name: 'Tamil' }, { code: 'te', name: 'Telugu' },
  { code: 'ml', name: 'Malayalam' }, { code: 'kn', name: 'Kannada' },
  { code: 'mr', name: 'Marathi' }, { code: 'gu', name: 'Gujarati' },
  { code: 'cs', name: 'Czech' }, { code: 'el', name: 'Greek' },
  { code: 'he', name: 'Hebrew' }, { code: 'ro', name: 'Romanian' },
  { code: 'hu', name: 'Hungarian' }, { code: 'sv', name: 'Swedish' },
  { code: 'no', name: 'Norwegian' }, { code: 'da', name: 'Danish' },
  { code: 'fi', name: 'Finnish' }
]

export default function MediaStudioPage() {
  const router = useRouter()
  const [mediaType, setMediaType] = useState<MediaType>('video')
  const [topic, setTopic] = useState('')
  const [script, setScript] = useState('')
  const [scenesText, setScenesText] = useState('')
  const [voiceStyle, setVoiceStyle] = useState('adult_female')
  const [voicePrompt, setVoicePrompt] = useState('')
  const [language, setLanguage] = useState('en')
  const [duration, setDuration] = useState(15)
  const [resolution, setResolution] = useState('8k')
  const [format, setFormat] = useState('mp4')
  const [aspectRatio, setAspectRatio] = useState('16:9')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [model, setModel] = useState('')
  const [speed, setSpeed] = useState('standard')
  const [isGeneratingScript, setIsGeneratingScript] = useState(false)
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false)
  const [scriptStyle, setScriptStyle] = useState('professional')
  const [promptStyle, setPromptStyle] = useState('cinematic')
  const [promptMood, setPromptMood] = useState('dramatic')
  const [cameraAngle, setCameraAngle] = useState('wide')
  const [lighting, setLighting] = useState('golden_hour')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [trialExpired, setTrialExpired] = useState(false)
  const [isOwner, setIsOwner] = useState(false)
  
  const [limits, setLimits] = useState<MediaLimits | null>(null)
  const [jobs, setJobs] = useState<MediaJob[]>([])
  const [activeJob, setActiveJob] = useState<MediaJob | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  // Auto Editor mode
  const [editorMode, setEditorMode] = useState<'generate' | 'autoedit'>('generate')
  const [autoEditPreset, setAutoEditPreset] = useState('custom')
  const [autoEditFiles, setAutoEditFiles] = useState<File[]>([])
  const [autoEditJobId, setAutoEditJobId] = useState<string | null>(null)
  const [autoEditJobs, setAutoEditJobs] = useState<any[]>([])
  const [autoEditActiveJob, setAutoEditActiveJob] = useState<any>(null)
  const [autoEditPoll, setAutoEditPoll] = useState<NodeJS.Timeout | null>(null)
  const [autoEditOptions, setAutoEditOptions] = useState({
    add_transitions: true,
    add_captions: true,
    color_grade: true,
    stabilize: true,
    ken_burns: true,
    add_intro_outro: true,
    adjust_speed: true,
    background_music: true,
    watermark_toggle: true,
    caption_language: 'en',
    output_aspect_ratio: '16:9',
    output_resolution: '1080p',
    speed_factor: 1.0,
  })
  const [autoEditPresets, setAutoEditPresets] = useState<any>(null)
  const [isAutoEditing, setIsAutoEditing] = useState(false)

  // Voice clone
  const [cloneFile, setCloneFile] = useState<File | null>(null)
  const [cloneName, setCloneName] = useState('')
  const [cloneConsent, setCloneConsent] = useState(false)
  const [voiceClones, setVoiceClones] = useState<any[]>([])
  const [selectedClone, setSelectedClone] = useState('')

  const loadLimits = useCallback(async () => {
    try {
      const res = await mediaApi.getLimits()
      setLimits(res.data)
      // If current duration not available, reset to first available
      if (res.data.available_durations.length > 0 && !res.data.available_durations.includes(duration)) {
        setDuration(res.data.available_durations[0])
      }
    } catch (err) {
      console.error('Failed to load media limits:', err)
    }
  }, [duration])

  const loadJobs = useCallback(async () => {
    try {
      const res = await mediaApi.listJobs({ limit: 20 })
      setJobs(res.data.jobs || [])
    } catch (err) {
      console.error('Failed to load media jobs:', err)
    }
  }, [])

  const loadVoiceClones = useCallback(async () => {
    try {
      const res = await mediaApi.listVoiceClones()
      setVoiceClones(res.data.clones || [])
    } catch (err) {
      console.error('Failed to load voice clones:', err)
    }
  }, [])

  // Auth guard
  useEffect(() => {
    const hasLocalToken = typeof localStorage !== 'undefined' && !!localStorage.getItem('access_token')
    const hasCookieToken =
      typeof document !== 'undefined' &&
      document.cookie.split('; ').some((row) => row.startsWith('access_token='))
    const hasRefreshToken =
      typeof document !== 'undefined' &&
      document.cookie.split('; ').some((row) => row.startsWith('refresh_token='))
    if (!hasLocalToken && !hasCookieToken && !hasRefreshToken && mounted) {
      router.push('/login')
    }
  }, [mounted, router])

  // Owner/admin check - admin gets all paid features free
  useEffect(() => {
    if (!mounted) return
    let cancelled = false
    import('@/lib/api').then(({ authApi }) => {
      authApi.checkIsOwner().then((res) => {
        if (!cancelled) {
          const isOwner = Boolean(res.data?.is_owner)
          const isAdmin = Boolean(res.data?.is_admin)
          setIsOwner(isOwner || isAdmin)
        }
      }).catch(() => {
        if (!cancelled) setIsOwner(false)
      })
    })
    return () => { cancelled = true }
  }, [mounted])

  useEffect(() => {
    loadLimits()
    loadJobs()
    loadVoiceClones()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadLimits, loadJobs, loadVoiceClones])

  // Load auto-edit presets when in auto-edit mode
  useEffect(() => {
    if (editorMode === 'autoedit') {
      mediaApi.autoEditPresets().then(res => {
        setAutoEditPresets(res.data)
      }).catch(() => {})
      loadAutoEditJobs()
    }
  }, [editorMode])

  // Auto-edit polling
  useEffect(() => {
    return () => {
      if (autoEditPoll) clearInterval(autoEditPoll)
    }
  }, [autoEditPoll])

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [pollInterval])

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic')
      return
    }

    setIsGenerating(true)
    try {
      const res = await mediaApi.generate({
        media_type: mediaType,
        topic: topic.trim(),
        script: script.trim() || undefined,
        scenes_text: scenesText.trim() || undefined,
        voice_style: voiceStyle,
        voice_prompt: voicePrompt.trim() || undefined,
        language,
        duration_seconds: duration,
        resolution,
        format: mediaType === 'picture' || mediaType === 'poster' ? 'png' : format,
        aspect_ratio: aspectRatio,
        model: model.trim() || undefined,
        negative_prompt: negativePrompt.trim() || undefined,
        voice_clone_id: voiceStyle === 'clone' ? selectedClone || undefined : undefined,
        voice_consent: voiceStyle === 'clone' ? cloneConsent : false
      })

      toast.success('Media generation started!')
      
      // Start polling for the new job
      const jobId = res.data.job_id
      startPolling(jobId)
      loadJobs()
      loadLimits()
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Generation failed'
      toast.error(msg)
    } finally {
      setIsGenerating(false)
    }
  }

  const startPolling = (jobId: string) => {
    if (pollInterval) clearInterval(pollInterval)
    
    const interval = setInterval(async () => {
      try {
        const res = await mediaApi.getJob(jobId)
        setActiveJob(res.data)
        
        if (res.data.status === 'completed' || res.data.status === 'failed' || res.data.status === 'cancelled') {
          clearInterval(interval)
          setPollInterval(null)
          loadJobs()
          loadLimits()
          if (res.data.status === 'completed') {
            toast.success('Media generated successfully! ✅')
          } else if (res.data.status === 'failed') {
            toast.error(`Generation failed: ${res.data.error_message || 'Unknown error'}`)
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
        clearInterval(interval)
        setPollInterval(null)
      }
    }, 2000)
    
    setPollInterval(interval)
  }

  const handleDownload = async (job: MediaJob) => {
    try {
      const res = await mediaApi.downloadJob(job.id)
      const url = window.URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `proai_${job.media_type}_${job.id}.${job.format}`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success('Download started')
    } catch (err) {
      toast.error('Download failed')
    }
  }

  const handleCancel = async (job: MediaJob) => {
    try {
      await mediaApi.cancelJob(job.id)
      toast.success('Job cancelled')
      loadJobs()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Cancel failed')
    }
  }

  const handleCloneUpload = async () => {
    if (!cloneFile) {
      toast.error('Please select an audio file')
      return
    }
    if (!cloneConsent) {
      toast.error('You must agree to voice cloning consent')
      return
    }
    if (!cloneName) {
      toast.error('Please name your voice clone')
      return
    }

    const toastId = toast.loading('Uploading voice sample...')
    try {
      await mediaApi.uploadVoiceClone(cloneFile, cloneName, language, cloneConsent)
      toast.success('Voice clone created!', { id: toastId })
      setCloneFile(null)
      setCloneName('')
      setCloneConsent(false)
      loadVoiceClones()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Voice clone failed', { id: toastId })
    }
  }

  const loadAutoEditJobs = useCallback(async () => {
    try {
      const res = await mediaApi.autoEditJobs({ limit: 20 })
      setAutoEditJobs(res.data.jobs || [])
    } catch (err) {
      console.error('Failed to load auto-edit jobs:', err)
    }
  }, [])

  const handleAutoEditUpload = async () => {
    if (autoEditFiles.length === 0) {
      toast.error('Please upload at least one video clip')
      return
    }

    const toastId = toast.loading('Uploading clip...')
    try {
      const file = autoEditFiles[0]
      const res = await mediaApi.autoEditUpload(file)
      setAutoEditJobId(res.data.job_id)
      toast.success('Clip uploaded! Click Start Auto Edit.', { id: toastId })
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Upload failed', { id: toastId })
    }
  }

  const handleStartAutoEdit = async () => {
    if (!autoEditJobId) {
      toast.error('Please upload a clip first')
      return
    }

    setIsAutoEditing(true)
    try {
      const res = await mediaApi.autoEditStart({
        preset: autoEditPreset,
        raw_files: [`temp://autoedit/${autoEditJobId}`],
        ...autoEditOptions,
      })
      toast.success('Auto-editing started!')
      setAutoEditJobId(res.data.job_id)
      startAutoEditPolling(res.data.job_id)
      loadAutoEditJobs()
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Auto-edit failed'
      toast.error(msg)
    } finally {
      setIsAutoEditing(false)
    }
  }

  const startAutoEditPolling = (jobId: string) => {
    if (autoEditPoll) clearInterval(autoEditPoll)
    const interval = setInterval(async () => {
      try {
        const res = await mediaApi.autoEditJob(jobId)
        setAutoEditActiveJob(res.data)
        if (res.data.status === 'completed' || res.data.status === 'failed' || res.data.status === 'cancelled') {
          clearInterval(interval)
          setAutoEditPoll(null)
          loadAutoEditJobs()
          if (res.data.status === 'completed') {
            toast.success('Video edited professionally! ✅')
          } else if (res.data.status === 'failed') {
            toast.error(`Editing failed: ${res.data.error_message || 'Unknown error'}`)
          }
        }
      } catch (err) {
        console.error('Auto-edit polling error:', err)
        clearInterval(interval)
        setAutoEditPoll(null)
      }
    }, 2000)
    setAutoEditPoll(interval)
  }

  const handleAutoEditDownload = async (job: any) => {
    try {
      const res = await mediaApi.autoEditDownload(job.id)
      const url = window.URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `proai_autoedit_${job.preset}_${job.id}.mp4`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success('Download started')
    } catch (err) {
      toast.error('Download failed')
    }
  }

  const handleManualEdit = async (job: any, action: string, params: any) => {
    try {
      const res = await mediaApi.autoEditManual(job.id, { action, params })
      toast.success(res.data.message || 'Edit applied')
      // Refresh job status
      const updated = await mediaApi.autoEditJob(job.id)
      setAutoEditActiveJob(updated.data)
      loadAutoEditJobs()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Manual edit failed')
    }
  }

  const isProUser = isOwner || limits?.unlimited || ['pro','pro_yearly','max','business','enterprise','trial'].includes(limits?.plan || '')
  const isPaidTier = isOwner || ['pro','pro_yearly','max','business','enterprise'].includes(limits?.plan || '')
  const canUseUltraFast = isPaidTier
  const canUse4K = isPaidTier
  const availableResolutions = canUse4K ? RESOLUTIONS : RESOLUTIONS.filter(r => r !== '4k' && r !== '8k')
  const availableSpeeds = canUseUltraFast ? SPEED_OPTIONS : SPEED_OPTIONS.filter(s => !s.pro)

  const handleGenerateScript = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic first')
      return
    }

    setIsGeneratingScript(true)
    try {
      const res = await mediaApi.generateScript({
        topic: topic.trim(),
        duration_seconds: duration,
        style: scriptStyle,
        language,
      })
      if (res.data.script) {
        setScript(res.data.script)
        if (res.data.cinematic_prompt) {
          setScenesText(res.data.cinematic_prompt)
        }
        toast.success('Professional script generated!')
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Script generation failed')
    } finally {
      setIsGeneratingScript(false)
    }
  }

  const handleGeneratePrompt = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a topic first')
      return
    }

    setIsGeneratingPrompt(true)
    try {
      const res = await mediaApi.generatePrompt({
        topic: topic.trim(),
        media_type: mediaType,
        style: promptStyle,
        mood: promptMood,
        camera_angle: cameraAngle,
        lighting,
        aspect_ratio: aspectRatio,
      })
      if (res.data.prompt) {
        setGeneratedPrompt(res.data.prompt)
        toast.success('Professional prompt generated!')
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Prompt generation failed')
    } finally {
      setIsGeneratingPrompt(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'failed': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'cancelled': return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      case 'queued': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      default: return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    }
  }

  const getMediaIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video className="w-4 h-4" />
      case 'picture': case 'poster': return <ImageIcon className="w-4 h-4" />
      case 'animation': return <Film className="w-4 h-4" />
      default: return <Video className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              AI Media Studio
            </h1>
            <p className="text-gray-400 mt-1">Videos · Pictures · Posters · Animations — 8K · Voice Over · 100% Word Accuracy</p>
          </div>
          {limits && (
            <div className="flex items-center gap-4 text-sm">
              <div className="px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800">
                <span className="text-gray-400">Plan: </span>
                <span className="font-semibold text-purple-400 uppercase">{limits.plan}</span>
                {limits.unlimited && <BadgeCheck className="inline w-4 h-4 ml-1 text-green-400" />}
              </div>
            </div>
          )}
        </div>

        {/* Trial Expired Banner */}
        {trialExpired && limits?.plan === 'free' && !isOwner && (
          <div className="bg-gradient-to-r from-red-900/30 to-orange-800/20 border border-red-500/30 rounded-2xl p-6 mb-8">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-red-500/20">
                <Crown className="w-8 h-8 text-red-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-300 mb-1">
                  Your Trial Has Expired
                </h3>
                <p className="text-sm text-gray-300 mb-4">
                  Your free trial has ended. You've been downgraded to the Free plan. 
                  Upgrade to PRO to unlock longer videos (up to 10 minutes), 4K/8K resolution, 
                  Ultra Fast rendering, unlimited quota, and professional features.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => router.push('/pricing')}
                    className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-400 hover:to-orange-400 font-semibold text-sm transition-all"
                  >
                    Upgrade to PRO
                  </button>
                  <span className="text-xs text-gray-500 flex items-center">
                    <Lock className="w-3 h-3 mr-1" /> Videos above 30s, 4K/8K & unlimited quota are PRO features
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Limits Display */}
        {limits && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Videos', used: limits.videos_used, limit: limits.video_limit },
              { label: 'Pictures', used: limits.pictures_used, limit: limits.picture_limit },
              { label: 'Animations', used: limits.animations_used, limit: limits.animation_limit }
            ].map(item => (
              <div key={item.label} className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">{item.label}</span>
                  <span className={item.limit === -1 ? 'text-green-400' : 'text-gray-200'}>
                    {item.limit === -1 ? '∞' : `${item.used}/${item.limit}`}
                  </span>
                </div>
                {item.limit !== -1 && (
                  <div className="mt-2 h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all"
                      style={{ width: `${Math.min(100, (item.used / Math.max(item.limit, 1)) * 100)}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
        </div>
      )}

      {/* Mode Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { mode: 'generate' as const, label: 'AI Generation', icon: <Wand2 className="w-4 h-4" /> },
          { mode: 'autoedit' as const, label: 'Auto Editor', icon: <Scissors className="w-4 h-4" /> },
        ].map(tab => (
          <button
            key={tab.mode}
            onClick={() => setEditorMode(tab.mode)}
            className={`px-4 py-2 rounded-lg border text-sm font-medium flex items-center gap-2 transition-all ${
              editorMode === tab.mode
                ? 'bg-purple-900/30 border-purple-500/50 text-purple-300'
                : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-gray-300'
            }`}
          >
            {tab.icon}
            {tab.label}
            {tab.mode === 'autoedit' && !isOwner && !limits?.unlimited && (
              <Crown className="w-3 h-3 text-yellow-400" />
            )}
          </button>
        ))}
      </div>

      {/* PRO Gating Banner for Auto Editor */}
      {editorMode === 'autoedit' && !isOwner && !limits?.unlimited && limits?.plan !== 'pro' && limits?.plan !== 'pro_yearly' && limits?.plan !== 'max' && limits?.plan !== 'business' && limits?.plan !== 'enterprise' && (
        <div className="bg-gradient-to-r from-yellow-900/30 to-yellow-800/20 border border-yellow-500/30 rounded-2xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-yellow-500/20">
              <Crown className="w-8 h-8 text-yellow-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-yellow-300 mb-1">
                Professional Editing Available on PRO
              </h3>
              <p className="text-sm text-gray-300 mb-4">
                Upload raw clips → AI automatically cuts bad parts, adds smooth transitions, 
                color-grades each scene, adds animated captions, stabilizes shaky footage, 
                adds Ken Burns zoom, intro + outro with eagle logo, and exports a fully 
                professional video. TikTok/YouTube/Reels presets included.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => router.push('/pricing')}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 font-semibold text-sm transition-all"
                >
                  Upgrade to PRO
                </button>
                <span className="text-xs text-gray-500 flex items-center">
                  <Lock className="w-3 h-3 mr-1" /> PRO feature — no free access
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Creation Form */}
        <div className="lg:col-span-2 space-y-6">

        {/* AUTO EDITOR PANEL */}
        {editorMode === 'autoedit' && (
          <>
            {/* Upload Zone */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Upload Raw Clips
              </h2>
              <div
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
                onDrop={(e) => {
                  e.preventDefault()
                  const files = Array.from(e.dataTransfer.files).filter(f =>
                    ['.mp4','.mov','.avi','.mkv','.webm','.m4v'].some(ext =>
                      f.name.toLowerCase().endsWith(ext)
                    )
                  )
                  setAutoEditFiles(files)
                }}
                className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500/50 transition-all"
              >
                <Upload className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                <p className="text-sm text-gray-400 mb-2">
                  Drag & drop video clips here, or click to browse
                </p>
                <p className="text-xs text-gray-500 mb-4">
                  MP4, MOV, AVI, MKV, WEBM — max 500MB per file
                </p>
                <input
                  type="file"
                  accept=".mp4,.mov,.avi,.mkv,.webm,.m4v"
                  multiple
                  onChange={(e) => {
                    const files = Array.from(e.target.files || [])
                    setAutoEditFiles(files)
                  }}
                  className="hidden"
                  id="auto-edit-upload"
                />
                <label htmlFor="auto-edit-upload" className="cursor-pointer">
                  <span className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-medium transition-all">
                    Select Files
                  </span>
                </label>
                {autoEditFiles.length > 0 && (
                  <div className="mt-4 space-y-1">
                    {autoEditFiles.map((f, i) => (
                      <div key={i} className="text-xs text-gray-400 bg-gray-900 rounded-lg px-3 py-2 flex items-center justify-between">
                        <span>{f.name} ({(f.size / 1024 / 1024).toFixed(1)} MB)</span>
                        <button
                          onClick={() => setAutoEditFiles(autoEditFiles.filter((_, idx) => idx !== i))}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={handleAutoEditUpload}
                disabled={autoEditFiles.length === 0}
                className="w-full mt-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 font-medium transition-all flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" /> Upload Clip
              </button>
            </div>

            {/* Platform Preset + Options */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Crop className="w-5 h-5 text-purple-400" />
                Platform Preset & Options
              </h2>

              {/* Preset Selector */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Platform Preset</label>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                  {autoEditPresets ? Object.entries(autoEditPresets.presets || {}).map(([key, cfg]: [string, any]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setAutoEditPreset(key)
                        setAutoEditOptions(prev => ({
                          ...prev,
                          output_aspect_ratio: cfg.aspect_ratio,
                          output_resolution: key === 'tiktok' || key === 'reels' || key === 'story' ? '1080p' : '1080p',
                        }))
                      }}
                      className={`p-3 rounded-lg border text-xs font-medium transition-all ${
                        autoEditPreset === key
                          ? 'bg-purple-900/30 border-purple-500/50 text-purple-300'
                          : 'bg-gray-900 border-gray-800 text-gray-400 hover:text-gray-300'
                      }`}
                    >
                      <div className="font-semibold">{cfg.name}</div>
                      <div className="text-[10px] text-gray-500 mt-1">{cfg.aspect_ratio}</div>
                    </button>
                  )) : (
                    ['tiktok','youtube','reels','instagram','story','custom'].map(p => (
                      <button key={p} className="p-3 rounded-lg border border-gray-800 bg-gray-900 text-xs text-gray-500">
                        {p}
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Editing Options */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                {[
                  { key: 'add_transitions', label: 'Transitions', icon: <Film className="w-3 h-3" /> },
                  { key: 'add_captions', label: 'Auto Captions', icon: <Type className="w-3 h-3" /> },
                  { key: 'color_grade', label: 'Color Grade', icon: <Palette className="w-3 h-3" /> },
                  { key: 'stabilize', label: 'Stabilize', icon: <Zap className="w-3 h-3" /> },
                  { key: 'ken_burns', label: 'Ken Burns', icon: <MonitorPlay className="w-3 h-3" /> },
                   { key: 'add_intro_outro', label: 'Intro + Outro', icon: <Film className="w-3 h-3" /> },
                  { key: 'adjust_speed', label: 'Speed FX', icon: <Zap className="w-3 h-3" /> },
                  { key: 'background_music', label: 'BG Music', icon: <Music className="w-3 h-3" /> },
                  { key: 'watermark_toggle', label: 'Watermark', icon: <ShieldCheck className="w-3 h-3" /> },
                ].map(opt => (
                  <label
                    key={opt.key}
                    className="flex items-center gap-2 p-3 rounded-lg bg-gray-900 border border-gray-800 cursor-pointer hover:border-gray-700"
                  >
                    <input
                      type="checkbox"
                      checked={autoEditOptions[opt.key as keyof typeof autoEditOptions] as boolean}
                      onChange={(e) => setAutoEditOptions(prev => ({
                        ...prev,
                        [opt.key]: e.target.checked,
                      }))}
                      className="w-4 h-4 accent-purple-500"
                    />
                    {opt.icon}
                    <span className="text-xs text-gray-300">{opt.label}</span>
                  </label>
                ))}
              </div>

              {/* Caption Language */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Caption Language</label>
                <select
                  value={autoEditOptions.caption_language}
                  onChange={(e) => setAutoEditOptions(prev => ({ ...prev, caption_language: e.target.value }))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.name} ({l.code.toUpperCase()})</option>)}
                </select>
              </div>

              {/* Start Button */}
              <button
                onClick={handleStartAutoEdit}
                disabled={isAutoEditing || !autoEditJobId}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 font-semibold text-lg shadow-lg shadow-purple-500/20 transition-all flex items-center justify-center gap-2"
              >
                {isAutoEditing ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Auto-Editing...</>
                ) : (
                  <><WandSparkles className="w-5 h-5" /> Start Auto Edit</>
                )}
              </button>
            </div>

            {/* Auto Edit Progress */}
            {autoEditActiveJob && autoEditActiveJob.status !== 'completed' && autoEditActiveJob.status !== 'failed' && autoEditActiveJob.status !== 'cancelled' && (
              <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                  Auto-Editing...
                </h3>
                <div className="text-2xl font-bold text-purple-400 mb-2">{Math.round(autoEditActiveJob.progress || 0)}%</div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                    style={{ width: `${autoEditActiveJob.progress || 0}%` }}
                  />
                </div>
                <div className="text-sm text-gray-400 mb-2">{autoEditActiveJob.progress_stage}</div>
                {autoEditActiveJob.scene_analysis && (
                  <div className="text-xs text-gray-500">
                    {autoEditActiveJob.cuts_made || 0} cuts made from {autoEditActiveJob.scene_analysis?.length || 0} segments
                  </div>
                )}
              </div>
            )}

            {/* Auto Edit Result */}
            {autoEditActiveJob && autoEditActiveJob.status === 'completed' && (
              <div className="bg-green-900/20 border border-green-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <h3 className="font-semibold text-green-300">Video Edited Professionally!</h3>
                </div>
                <div className="text-sm text-gray-300 mb-4">
                  <p><span className="text-gray-500">Preset:</span> {autoEditActiveJob.preset}</p>
                  <p><span className="text-gray-500">Duration:</span> {autoEditActiveJob.duration_seconds?.toFixed(1)}s</p>
                  {autoEditActiveJob.output_size_bytes && (
                    <p><span className="text-gray-500">Size:</span> {(autoEditActiveJob.output_size_bytes / (1024 * 1024)).toFixed(2)} MB</p>
                  )}
                  {autoEditActiveJob.cuts_made > 0 && (
                    <p><span className="text-gray-500">Cuts:</span> {autoEditActiveJob.cuts_made} segments removed</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAutoEditDownload(autoEditActiveJob)}
                    className="flex-1 py-3 rounded-xl bg-green-600 hover:bg-green-500 font-medium transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" /> Download MP4
                  </button>
                  <button
                    onClick={() => setAutoEditActiveJob(null)}
                    className="px-4 py-3 rounded-xl bg-gray-800 hover:bg-gray-700 text-sm font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* AI GENERATION FORM (existing - conditionally rendered) */}
        {editorMode === 'generate' && (
          <>
            {/* Media Type Selector */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Wand2 className="w-5 h-5 text-purple-400" />
                Create Media
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                {[
                  { type: 'video' as MediaType, label: 'AI Video', icon: <Video className="w-5 h-5" />, desc: 'Hacking, coding, cartoons, stories' },
                  { type: 'picture' as MediaType, label: 'AI Picture', icon: <ImageIcon className="w-5 h-5" />, desc: 'Posters, wallpapers, logos' },
                  { type: 'poster' as MediaType, label: 'Poster', icon: <Sparkles className="w-5 h-5" />, desc: 'Exact text rendered on top' },
                  { type: 'animation' as MediaType, label: 'Animation', icon: <Film className="w-5 h-5" />, desc: '2D, motion posters, intros' }
                ].map(item => (
                  <button
                    key={item.type}
                    onClick={() => setMediaType(item.type)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      mediaType === item.type
                        ? 'bg-purple-900/30 border-purple-500/50 shadow-lg shadow-purple-500/10'
                        : 'bg-gray-900 border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    <div className={`mb-2 ${mediaType === item.type ? 'text-purple-400' : 'text-gray-500'}`}>{item.icon}</div>
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs text-gray-500 mt-1">{item.desc}</div>
                  </button>
                ))}
              </div>

              {/* Topic */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Topic *</label>
                <textarea
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. Hacker strike video — a hacker breaks into a secure system..."
                  rows={2}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-600"
                />
              </div>

              {/* Script */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                  <Type className="w-4 h-4" />
                  Script (for voice over + subtitles)
                </label>
                <div className="flex flex-col md:flex-row gap-2 mb-2">
                  <select
                    value={scriptStyle}
                    onChange={(e) => setScriptStyle(e.target.value)}
                    className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {SCRIPT_STYLES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                  </select>
                  <button
                    onClick={handleGenerateScript}
                    disabled={isGeneratingScript}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm font-medium transition-all flex items-center justify-center gap-2"
                  >
                    {isGeneratingScript ? <Loader2 className="w-4 h-4 animate-spin" /> : <WandSparkles className="w-4 h-4" />}
                    Generate Script
                  </button>
                </div>
                <textarea
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  placeholder="e.g. In a world where security is everything, one hacker will change it all..."
                  rows={3}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-600"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Your script is rendered 100% exactly — voice over + burned subtitles with word-for-word verification.
                </p>
              </div>

              {/* Scenes */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                  <Clapperboard className="w-4 h-4" />
                  Scene Description (optional — AI builds storyboard automatically)
                </label>
                <textarea
                  value={scenesText}
                  onChange={(e) => setScenesText(e.target.value)}
                  placeholder={'Scene 1: Hacker typing in dark room\nScene 2: Code streams on screen\nScene 3: Shield breaks'}
                  rows={4}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-600 font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  No scene missing — every scene you describe is generated and combined into ONE video.
                </p>
              </div>

              {/* Professional Prompt Generator */}
              <div className="mb-4 p-4 rounded-xl bg-blue-900/20 border border-blue-500/30">
                <label className="block text-sm text-blue-300 mb-3 flex items-center gap-2">
                  <WandSparkles className="w-4 h-4" />
                  Professional Cinematography Prompt Generator
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Style</label>
                    <select
                      value={promptStyle}
                      onChange={(e) => setPromptStyle(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {PROMPT_STYLES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Mood</label>
                    <select
                      value={promptMood}
                      onChange={(e) => setPromptMood(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {PROMPT_MOODS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Camera Angle</label>
                    <select
                      value={cameraAngle}
                      onChange={(e) => setCameraAngle(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {CAMERA_ANGLES.map(a => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Lighting</label>
                    <select
                      value={lighting}
                      onChange={(e) => setLighting(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {LIGHTING_OPTIONS.map(l => <option key={l} value={l}>{l.replace(/_/g, ' ')}</option>)}
                    </select>
                  </div>
                </div>
                <button
                  onClick={handleGeneratePrompt}
                  disabled={isGeneratingPrompt}
                  className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium transition-all flex items-center justify-center gap-2"
                >
                  {isGeneratingPrompt ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                  Generate Professional Prompt
                </button>
                {generatedPrompt && (
                  <div className="mt-3">
                    <div className="text-xs text-gray-400 mb-1">Generated Prompt:</div>
                    <textarea
                      value={generatedPrompt}
                      onChange={(e) => setGeneratedPrompt(e.target.value)}
                      rows={4}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => { setScenesText(generatedPrompt); toast.success('Prompt added to scenes!') }}
                        className="flex-1 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium"
                      >
                        Use as Scene Description
                      </button>
                      <button
                        onClick={() => { setTopic(`${topic ? topic + ' ' : ''}${generatedPrompt}`); toast.success('Prompt added to topic!') }}
                        className="flex-1 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium"
                      >
                        Use as Topic
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Voice & Language */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Mic className="w-4 h-4" />
                    Voice Style
                  </label>
                  <select
                    value={voiceStyle}
                    onChange={(e) => setVoiceStyle(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {VOICE_STYLES.map(v => <option key={v.value} value={v.value}>{v.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Languages className="w-4 h-4" />
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.name} ({l.code.toUpperCase()})</option>)}
                  </select>
                </div>
              </div>

              {/* Voice prompt */}
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Voice Prompt (optional)</label>
                <input
                  value={voicePrompt}
                  onChange={(e) => setVoicePrompt(e.target.value)}
                  placeholder={'e.g. young girl voice, sweet, Urdu'}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-600"
                />
              </div>

              {/* Voice clone selector */}
              {voiceStyle === 'clone' && (
                <div className="mb-4 p-4 rounded-lg bg-purple-900/20 border border-purple-500/30">
                  <label className="block text-sm text-purple-300 mb-2">Select Voice Clone</label>
                  {voiceClones.length > 0 ? (
                    <select
                      value={selectedClone}
                      onChange={(e) => setSelectedClone(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 mb-3"
                    >
                      <option value="">Select a clone...</option>
                      {voiceClones.map(c => (
                        <option key={c.id} value={c.id}>
                          {c.name} ({c.language.toUpperCase()} · {c.duration_seconds}s)
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-sm text-gray-400 mb-3">No voice clones yet. Upload a 30-second sample below.</p>
                  )}
                </div>
              )}

              {/* Duration, Resolution, Format, Aspect */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Duration
                  </label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {(limits?.available_durations || [5, 15, 30]).map(d => (
                      <option key={d} value={d}>{d}s</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <MonitorPlay className="w-4 h-4" />
                    Resolution
                    {!canUse4K && <Lock className="w-3 h-3 text-yellow-400" />}
                  </label>
                  <select
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {availableResolutions.map(r => <option key={r} value={r}>{r.toUpperCase()}{!canUse4K && (r === '4k' || r === '8k') ? ' 🔒' : ''}</option>)}
                  </select>
                  {!canUse4K && (
                    <p className="text-[10px] text-yellow-400/80 mt-1 flex items-center gap-1">
                      <Lock className="w-2.5 h-2.5" /> 4K/8K requires PRO
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Speed
                    {!canUseUltraFast && <Lock className="w-3 h-3 text-yellow-400" />}
                  </label>
                  <select
                    value={speed}
                    onChange={(e) => setSpeed(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {availableSpeeds.map(s => <option key={s.value} value={s.value}>{s.label}{!canUseUltraFast && s.pro ? ' 🔒' : ''}</option>)}
                  </select>
                  {!canUseUltraFast && (
                    <p className="text-[10px] text-yellow-400/80 mt-1 flex items-center gap-1">
                      <Lock className="w-2.5 h-2.5" /> Ultra Fast requires PRO
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Format</label>
                  <select
                    value={format}
                    onChange={(e) => setFormat(e.target.value)}
                    disabled={mediaType === 'picture' || mediaType === 'poster'}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                  >
                    {FORMATS.map(f => <option key={f} value={f}>{f.toUpperCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Aspect Ratio</label>
                  <select
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {ASPECT_RATIOS.map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 font-semibold text-lg shadow-lg shadow-purple-500/20 transition-all flex items-center justify-center gap-2"
              >
                {isGenerating ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Creating...</>
                ) : (
                  <><Sparkles className="w-5 h-5" /> Generate {mediaType === 'video' ? 'Video' : mediaType === 'picture' ? 'Picture' : mediaType === 'poster' ? 'Poster' : 'Animation'}</>
                )}
              </button>
            </div>

            {/* Voice Clone Upload */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Voice Cloning (30-second sample)
              </h2>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Clone Name</label>
                  <input
                    value={cloneName}
                    onChange={(e) => setCloneName(e.target.value)}
                    placeholder="e.g. My Voice"
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-600"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Audio File (WAV, MP3, M4A, OGG — max 30s)</label>
                  <input
                    type="file"
                    accept=".wav,.mp3,.m4a,.ogg"
                    onChange={(e) => setCloneFile(e.target.files?.[0] || null)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-500"
                  />
                  {cloneFile && (
                    <p className="text-xs text-gray-500 mt-1">{cloneFile.name} ({(cloneFile.size / 1024).toFixed(1)} KB)</p>
                  )}
                </div>
                <label className="flex items-start gap-3 p-4 rounded-lg bg-gray-900 border border-gray-800 cursor-pointer hover:border-gray-700">
                  <input
                    type="checkbox"
                    checked={cloneConsent}
                    onChange={(e) => setCloneConsent(e.target.checked)}
                    className="mt-1 w-4 h-4 accent-blue-500"
                  />
                  <span className="text-sm text-gray-300">
                    I consent to my voice being cloned and used for AI video generation.
                    I confirm this is my own voice and I have the right to use it.
                  </span>
                </label>
                <button
                  onClick={handleCloneUpload}
                  className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 font-medium transition-all flex items-center justify-center gap-2"
                >
                  <Music className="w-4 h-4" /> Clone My Voice
                </button>
              </div>
            </div>
            </>
          )}
        </div>

          {/* Right: Jobs & Progress */}
          <div className="space-y-6">
            {/* Active Job Progress */}
            {activeJob && activeJob.status !== 'completed' && activeJob.status !== 'failed' && activeJob.status !== 'cancelled' && (
              <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                  Generating...
                </h3>
                <div className="text-2xl font-bold text-purple-400 mb-2">{Math.round(activeJob.progress)}%</div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                    style={{ width: `${activeJob.progress}%` }}
                  />
                </div>
                <div className="text-sm text-gray-400 mb-2">{activeJob.progress_stage}</div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-2 py-1 rounded bg-gray-800 text-gray-300">{activeJob.media_type}</span>
                  <span className="px-2 py-1 rounded bg-gray-800 text-gray-300">{activeJob.scene_count} scenes</span>
                  <span className="px-2 py-1 rounded bg-gray-800 text-gray-300">{activeJob.duration_seconds}s</span>
                  <span className="px-2 py-1 rounded bg-gray-800 text-gray-300">{activeJob.resolution?.toUpperCase()}</span>
                </div>
              </div>
            )}

            {/* Completed Job Result */}
            {activeJob && activeJob.status === 'completed' && (
              <div className="bg-green-900/20 border border-green-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <h3 className="font-semibold text-green-300">Ready!</h3>
                  {activeJob.accuracy_verified && (
                    <span className="ml-auto flex items-center gap-1 text-xs text-green-400">
                      <ShieldCheck className="w-3 h-3" /> 100% Accuracy Verified
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-300 mb-4">
                  <p><span className="text-gray-500">Topic:</span> {activeJob.topic}</p>
                  <p><span className="text-gray-500">Resolution:</span> {activeJob.output_resolution || activeJob.resolution}</p>
                  {activeJob.output_size_bytes && (
                    <p><span className="text-gray-500">Size:</span> {(activeJob.output_size_bytes / (1024 * 1024)).toFixed(2)} MB</p>
                  )}
                  {activeJob.verification_report && (
                    <p className="mt-2 flex items-center gap-1 text-green-400">
                      <BadgeCheck className="w-3 h-3" />
                      Word match: {activeJob.verification_report.match_percentage}%
                    </p>
                  )}
                </div>
                <button
                  onClick={() => handleDownload(activeJob)}
                  className="w-full py-3 rounded-xl bg-green-600 hover:bg-green-500 font-medium transition-all flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" /> Download {activeJob.format.toUpperCase()}
                </button>
              </div>
            )}

            {/* Job History */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
              <h3 className="font-semibold mb-4">Recent Jobs</h3>
              {jobs.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No media generated yet</p>
              ) : (
                <div className="space-y-3">
                  {jobs.map(job => (
                    <div key={job.id} className="p-4 rounded-xl bg-gray-900 border border-gray-800 hover:border-gray-700 transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-purple-400">{getMediaIcon(job.media_type)}</span>
                          <span className="text-sm font-medium truncate max-w-[150px]">{job.topic}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded-full text-xs border ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{job.duration_seconds}s</span>
                        <span>{job.scene_count} scenes</span>
                        {job.accuracy_verified && (
                          <span className="text-green-400 flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3" /> Accurate
                          </span>
                        )}
                      </div>
                      {job.status === 'completed' && job.output_path && (
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => handleDownload(job)}
                            className="flex-1 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium flex items-center justify-center gap-1"
                          >
                            <Download className="w-3 h-3" /> Download
                          </button>
                          <button
                            onClick={() => setActiveJob(job)}
                            className="flex-1 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium flex items-center justify-center gap-1"
                          >
                            <Play className="w-3 h-3" /> View
                          </button>
                        </div>
                      )}
                      {job.status === 'queued' || job.status === 'storyboarding' || job.status === 'generating' || job.status === 'voice_over' || job.status === 'subtitling' || job.status === 'verifying' || job.status === 'upscaling' ? (
                        <div className="flex items-center gap-2 mt-3">
                          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-purple-500 transition-all"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-purple-400">{Math.round(job.progress)}%</span>
                        </div>
                      ) : (
                        <>
                          {job.status === 'failed' && job.error_message && (
                            <p className="text-xs text-red-400 mt-2">{job.error_message}</p>
                          )}
                          <button
                            onClick={() => setActiveJob(job)}
                            className="mt-3 w-full py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium"
                          >
                            View Details
                          </button>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Auto Edit Jobs */}
            {editorMode === 'autoedit' && (
              <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-blue-400" />
                  Auto Edit Jobs
                </h3>
                {autoEditJobs.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-8">No auto-edits yet</p>
                ) : (
                  <div className="space-y-3">
                    {autoEditJobs.map(job => (
                      <div key={job.id} className="p-4 rounded-xl bg-gray-900 border border-gray-800 hover:border-gray-700 transition-all">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Scissors className="w-4 h-4 text-blue-400" />
                            <span className="text-sm font-medium">{job.preset?.toUpperCase() || 'CUSTOM'}</span>
                          </div>
                          <span className={`px-2 py-0.5 rounded-full text-xs border ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        {job.status === 'completed' && (
                          <div className="flex gap-2 mt-3">
                            <button
                              onClick={() => handleAutoEditDownload(job)}
                              className="flex-1 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-xs font-medium flex items-center justify-center gap-1"
                            >
                              <Download className="w-3 h-3" /> Download
                            </button>
                            <button
                              onClick={() => setAutoEditActiveJob(job)}
                              className="flex-1 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium"
                            >
                              Details
                            </button>
                          </div>
                        )}
                        {job.status === 'failed' && job.error_message && (
                          <p className="text-xs text-red-400 mt-2">{job.error_message}</p>
                        )}
                        {job.status === 'analyzing' || job.status === 'editing' || job.status === 'rendering' ? (
                          <div className="flex items-center gap-2 mt-3">
                            <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500 transition-all"
                                style={{ width: `${job.progress || 0}%` }}
                              />
                            </div>
                            <span className="text-xs text-blue-400">{Math.round(job.progress || 0)}%</span>
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

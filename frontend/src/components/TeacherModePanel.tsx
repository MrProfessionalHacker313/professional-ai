'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { GraduationCap, Plus, BookOpen, Clock, Users, Loader2, X, Check } from 'lucide-react'
import { featuresApi } from '@/lib/api'

interface TeacherModePanelProps {
  onClose: () => void
}

interface Lesson {
  id: string
  title: string
  duration: string
  type: 'video' | 'reading' | 'quiz' | 'practice'
  completed: boolean
}

interface CourseResult {
  course_title: string
  description: string
  difficulty: string
  duration: string
  lessons: Lesson[]
  prerequisites: string[]
}

export default function TeacherModePanel({ onClose }: TeacherModePanelProps) {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('beginner')
  const [duration, setDuration] = useState('1-week')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CourseResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const difficulties = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
  ]

  const durations = [
    { value: '1-day', label: '1 Day' },
    { value: '1-week', label: '1 Week' },
    { value: '2-weeks', label: '2 Weeks' },
    { value: '1-month', label: '1 Month' },
  ]

  const sampleLessons: Lesson[] = [
    { id: '1', title: 'Introduction & Fundamentals', duration: '15 min', type: 'video', completed: false },
    { id: '2', title: 'Core Concepts Explained', duration: '20 min', type: 'reading', completed: false },
    { id: '3', title: 'Hands-on Practice', duration: '30 min', type: 'practice', completed: false },
    { id: '4', title: 'Knowledge Check', duration: '10 min', type: 'quiz', completed: false },
    { id: '5', title: 'Advanced Techniques', duration: '25 min', type: 'video', completed: false },
  ]

  const handleCreateCourse = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await featuresApi.routeTask({
        task_type: 'teacher_mode',
        task_description: `Create a ${difficulty} course on ${topic} over ${duration}`,
      })
      setResult({
        course_title: topic,
        description: response.data.description || `A comprehensive ${difficulty}-level course on ${topic}.`,
        difficulty,
        duration,
        lessons: sampleLessons,
        prerequisites: response.data.prerequisites || ['Basic computer literacy', 'Interest in the subject'],
      })
    } catch {
      setError('Failed to create course. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getLessonIcon = (type: string) => {
    switch (type) {
      case 'video': return <BookOpen className="w-4 h-4" />
      case 'reading': return <BookOpen className="w-4 h-4" />
      case 'quiz': return <Users className="w-4 h-4" />
      case 'practice': return <Check className="w-4 h-4" />
      default: return <BookOpen className="w-4 h-4" />
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
          <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-500 rounded-xl flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Teacher Mode</h3>
            <p className="text-xs text-gray-400">Create AI-powered courses & lessons</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Difficulty</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
          >
            {difficulties.map(d => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Duration</label>
          <select
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
          >
            {durations.map(d => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <div className="bg-violet-500/10 border border-violet-500/30 rounded-lg px-3 py-2 w-full">
            <p className="text-[10px] text-violet-400">Level</p>
            <p className="text-xs text-white font-medium capitalize">{difficulty}</p>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1 block">Course Topic</label>
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., Machine Learning Basics, Web Development..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500"
        />
      </div>

      <button
        onClick={handleCreateCourse}
        disabled={!topic.trim() || loading}
        className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
        {loading ? 'Creating Course...' : 'Create Course'}
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
          className="mt-4 space-y-3"
        >
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-white mb-1">{result.course_title}</h4>
            <p className="text-xs text-gray-400 mb-3">{result.description}</p>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs bg-violet-500/20 text-violet-400 px-2 py-1 rounded-full capitalize">{result.difficulty}</span>
              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full">{result.duration}</span>
              <span className="text-xs text-gray-400">{result.lessons.length} lessons</span>
            </div>
            {result.prerequisites.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-gray-400 mb-1">Prerequisites:</p>
                <div className="flex flex-wrap gap-1">
                  {result.prerequisites.map((prereq, i) => (
                    <span key={i} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">{prereq}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-xs font-medium text-gray-400 mb-3">LESSONS</h4>
            <div className="space-y-2">
              {result.lessons.map((lesson, i) => (
                <div key={lesson.id} className="flex items-center gap-3 bg-gray-900/50 rounded-lg p-2.5 hover:bg-gray-900 transition-colors">
                  <div className="w-6 h-6 bg-violet-500/20 rounded-full flex items-center justify-center text-xs text-violet-400 font-medium">
                    {i + 1}
                  </div>
                  {getLessonIcon(lesson.type)}
                  <div className="flex-1">
                    <p className="text-xs text-white">{lesson.title}</p>
                    <div className="flex items-center gap-2 text-[10px] text-gray-400">
                      <Clock className="w-3 h-3" />
                      {lesson.duration}
                      <span className="capitalize">{lesson.type}</span>
                    </div>
                  </div>
                  {lesson.completed && <Check className="w-4 h-4 text-green-400" />}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

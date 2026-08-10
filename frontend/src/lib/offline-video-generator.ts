/**
 * Professional AI - Offline Video Generator
 * Creates simple videos using Canvas + MediaRecorder in the browser.
 * Works 100% offline when no cloud video API is available.
 *
 * Features:
 * - Slideshow with text overlays
 * - Generated backgrounds (gradients, patterns)
 * - Optional built-in audio tones (Web Audio API)
 * - Export as WebM video
 */

export type Slide = {
  text: string
  duration: number
  backgroundColor?: string
  textColor?: string
  fontSize?: number
  subtitle?: string
}

export type VideoOptions = {
  width: number
  height: number
  fps: number
  slides: Slide[]
  audioEnabled: boolean
  audioType: 'tone' | 'silence'
  transitionMs: number
}

const DEFAULT_OPTIONS: VideoOptions = {
  width: 1280,
  height: 720,
  fps: 30,
  slides: [],
  audioEnabled: true,
  audioType: 'tone',
  transitionMs: 500,
}

export interface OfflineVideoJob {
  id: string
  status: 'queued' | 'processing' | 'done' | 'error'
  progress: number
  blobUrl?: string
  error?: string
}

class OfflineVideoGenerator {
  private activeJobs: Map<string, { options: VideoOptions; cancel: () => void }> = new Map()

  /**
   * Generate a video from slides.
   * Returns a job ID that can be polled for progress.
   */
  async generateVideo(options: Partial<VideoOptions>): Promise<OfflineVideoJob> {
    const opts: VideoOptions = { ...DEFAULT_OPTIONS, ...options }
    const jobId = crypto.randomUUID()
    const job: OfflineVideoJob = {
      id: jobId,
      status: 'processing',
      progress: 0,
    }

    if (opts.slides.length === 0) {
      job.status = 'error'
      job.error = 'No slides provided'
      return job
    }

    try {
      const blob = await this._renderVideo(opts, (progress) => {
        job.progress = Math.round(progress * 100)
      })
      job.status = 'done'
      job.progress = 100
      job.blobUrl = URL.createObjectURL(blob)
    } catch (error) {
      job.status = 'error'
      job.error = error instanceof Error ? error.message : 'Video generation failed'
    }

    return job
  }

  /**
   * Quick generate: text overlay + gradient background -> WebM blob
   */
  async quickVideo(params: {
    text: string
    subtitle?: string
    durationSec?: number
    width?: number
    height?: number
    bgGradient?: [string, string]
    textColor?: string
  }): Promise<Blob> {
    const durationSec = params.durationSec || 5
    const slides: Slide[] = [
      {
        text: params.text,
        duration: durationSec,
        backgroundColor: undefined,
        textColor: params.textColor || '#ffffff',
        fontSize: 48,
        subtitle: params.subtitle,
      },
    ]
    const result = await this.generateVideo({
      width: params.width || 1280,
      height: params.height || 720,
      fps: 30,
      slides,
      audioEnabled: true,
      audioType: 'tone',
      transitionMs: 0,
    })
    if (result.status !== 'done' || !result.blobUrl) {
      throw new Error(result.error || 'Video generation failed')
    }
    const response = await fetch(result.blobUrl)
    return await response.blob()
  }

  /**
   * Create a slideshow video from multiple text slides.
   */
  async slideshowVideo(params: {
    slides: Array<{ text: string; subtitle?: string; bgGradient?: [string, string] }>
    slideDurationSec?: number
    width?: number
    height?: number
    fps?: number
    transitionMs?: number
  }): Promise<Blob> {
    const slideDurationSec = params.slideDurationSec || 4
    const slides: Slide[] = params.slides.map((s) => ({
      text: s.text,
      duration: slideDurationSec,
      subtitle: s.subtitle,
    }))
    const result = await this.generateVideo({
      width: params.width || 1280,
      height: params.height || 720,
      fps: params.fps || 30,
      slides,
      audioEnabled: true,
      audioType: 'tone',
      transitionMs: params.transitionMs || 300,
    })
    if (result.status !== 'done' || !result.blobUrl) {
      throw new Error(result.error || 'Slideshow generation failed')
    }
    const response = await fetch(result.blobUrl)
    return await response.blob()
  }

  private async _renderVideo(
    opts: VideoOptions,
    onProgress: (progress: number) => void
  ): Promise<Blob> {
    const { width, height, fps, slides, audioEnabled, audioType, transitionMs } = opts
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')!
    if (!ctx) throw new Error('Canvas 2D not available')

    const totalDurationSec = slides.reduce((sum, s) => sum + s.duration, 0) + (slides.length - 1) * (transitionMs / 1000)
    const totalFrames = Math.ceil(totalDurationSec * fps)

    const stream = canvas.captureStream(fps)

    // Add audio track if enabled
    if (audioEnabled) {
      const audioStream = this._createAudioStream(totalDurationSec, audioType)
      audioStream.getAudioTracks().forEach((track) => stream.addTrack(track))
    }

    const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
      ? 'video/webm;codecs=vp9'
      : MediaRecorder.isTypeSupported('video/webm;codecs=vp8')
        ? 'video/webm;codecs=vp8'
        : 'video/webm'

    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 2_500_000 })
    const chunks: Blob[] = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }

    const donePromise = new Promise<Blob>((resolve, reject) => {
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeType })
        resolve(blob)
      }
      recorder.onerror = () => reject(new Error('MediaRecorder error'))
    })

    recorder.start(100)

    let frame = 0
    const slideFrames = slides.map((s) => Math.ceil(s.duration * fps))
    const transitionFrames = Math.ceil((transitionMs / 1000) * fps)

    const drawFrame = () => {
      if (frame >= totalFrames) {
        recorder.stop()
        stream.getTracks().forEach((t) => t.stop())
        return
      }

      // Determine which slide we're on
      let slideIndex = 0
      let framesIntoSlide = frame
      for (let i = 0; i < slideFrames.length; i++) {
        if (framesIntoSlide < slideFrames[i]) {
          slideIndex = i
          break
        }
        framesIntoSlide -= slideFrames[i]
        if (i < slideFrames.length - 1) {
          framesIntoSlide -= transitionFrames
          if (framesIntoSlide < 0) {
            slideIndex = i
            framesIntoSlide = slideFrames[i] + framesIntoSlide
            break
          }
        }
        if (i === slideFrames.length - 1) slideIndex = i
      }

      const slide = slides[slideIndex]
      const bg = slide.backgroundColor || this._randomGradient(ctx, width, height, slideIndex)
      this._drawSlide(ctx, slide, width, height, bg)

      frame++
      onProgress(frame / totalFrames)
      requestAnimationFrame(drawFrame)
    }

    drawFrame()

    return donePromise
  }

  private _drawSlide(
    ctx: CanvasRenderingContext2D,
    slide: Slide,
    width: number,
    height: number,
    bgGradient: CanvasGradient | string
  ) {
    // Background
    ctx.fillStyle = bgGradient
    ctx.fillRect(0, 0, width, height)

    // Optional subtle pattern overlay
    this._drawSubtlePattern(ctx, width, height)

    // Text shadow
    ctx.shadowColor = 'rgba(0,0,0,0.5)'
    ctx.shadowBlur = 20
    ctx.shadowOffsetX = 2
    ctx.shadowOffsetY = 2

    // Main text
    const fontSize = slide.fontSize || Math.max(32, Math.min(width / 20, 64))
    ctx.fillStyle = slide.textColor || '#ffffff'
    ctx.font = `bold ${fontSize}px "Segoe UI", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    // Word wrap
    const maxWidth = width * 0.8
    const words = slide.text.split(' ')
    const lines: string[] = []
    let currentLine = ''

    for (const word of words) {
      const testLine = currentLine ? `${currentLine} ${word}` : word
      const metrics = ctx.measureText(testLine)
      if (metrics.width > maxWidth && currentLine) {
        lines.push(currentLine)
        currentLine = word
      } else {
        currentLine = testLine
      }
    }
    if (currentLine) lines.push(currentLine)

    const lineHeight = fontSize * 1.3
    const totalHeight = lines.length * lineHeight
    let y = height / 2 - totalHeight / 2 + lineHeight / 2

    for (const line of lines) {
      ctx.fillText(line, width / 2, y)
      y += lineHeight
    }

    // Subtitle
    if (slide.subtitle) {
      ctx.shadowBlur = 10
      ctx.fillStyle = slide.textColor === '#ffffff' ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.6)'
      ctx.font = `${fontSize * 0.5}px "Segoe UI", system-ui, sans-serif`
      ctx.fillText(slide.subtitle, width / 2, height - fontSize)
    }

    // Reset shadow
    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
    ctx.shadowOffsetX = 0
    ctx.shadowOffsetY = 0
  }

  private _randomGradient(ctx: CanvasRenderingContext2D, w: number, h: number, seed: number): CanvasGradient {
    const palettes = [
      ['#1e3a5f', '#3b82f6'],
      ['#4c1d95', '#8b5cf6'],
      ['#065f46', '#10b981'],
      ['#7c2d12', '#f97316'],
      ['#881337', '#f43f5e'],
      ['#0f172a', '#334155'],
      ['#1e40af', '#60a5fa'],
      ['#4a1942', '#c026d3'],
    ]
    const colors = palettes[seed % palettes.length]
    const gradient = ctx.createLinearGradient(0, 0, w, h)
    gradient.addColorStop(0, colors[0])
    gradient.addColorStop(1, colors[1])
    return gradient
  }

  private _drawSubtlePattern(ctx: CanvasRenderingContext2D, w: number, h: number) {
    ctx.strokeStyle = 'rgba(255,255,255,0.03)'
    ctx.lineWidth = 1
    const step = 40
    for (let x = 0; x < w; x += step) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, h)
      ctx.stroke()
    }
    for (let y = 0; y < h; y += step) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(w, y)
      ctx.stroke()
    }
  }

  private _createAudioStream(durationSec: number, type: 'tone' | 'silence'): MediaStream {
    if (type === 'silence') {
      // Create a silent audio track using a silent oscillator
      const audioCtx = new AudioContext()
      const oscillator = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      gain.gain.value = 0
      oscillator.connect(gain)
      const dest = audioCtx.createMediaStreamDestination()
      gain.connect(dest)
      oscillator.start()
      const stream = dest.stream
      setTimeout(() => {
        oscillator.stop()
        audioCtx.close()
      }, durationSec * 1000 + 500)
      return stream
    }

    // Generate a pleasant tone sequence
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const dest = audioCtx.createMediaStreamDestination()
    const sampleRate = audioCtx.sampleRate
    const totalSamples = Math.floor(durationSec * sampleRate)
    const buffer = audioCtx.createBuffer(1, totalSamples, sampleRate)
    const data = buffer.getChannelData(0)

    // Generate a soft ambient tone
    const baseFreq = 220
    for (let i = 0; i < totalSamples; i++) {
      const t = i / sampleRate
      const envelope = Math.min(1, t * 2) * Math.max(0, 1 - (t / durationSec) * 0.5)
      data[i] = (
        Math.sin(2 * Math.PI * baseFreq * t) * 0.3 +
        Math.sin(2 * Math.PI * baseFreq * 1.5 * t) * 0.15 +
        Math.sin(2 * Math.PI * baseFreq * 2 * t) * 0.05
      ) * envelope * 0.15
    }

    const source = audioCtx.createBufferSource()
    source.buffer = buffer
    source.connect(dest)
    source.start()

    setTimeout(() => {
      source.stop()
      audioCtx.close()
    }, durationSec * 1000 + 500)

    return dest.stream
  }

  cancelJob(jobId: string) {
    const job = this.activeJobs.get(jobId)
    if (job) {
      job.cancel()
      this.activeJobs.delete(jobId)
    }
  }
}

export const offlineVideoGenerator = new OfflineVideoGenerator()

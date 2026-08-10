/**
 * Professional AI - Offline Image Generator
 * Canvas-based image generation that works 100% offline.
 *
 * Features:
 * - Gradient backgrounds
 * - Text posters (quote posters, social media cards)
 * - Simple art (geometric patterns, abstract art)
 * - Avatar generation (initials-based)
 * - Banner/header generation
 *
 * All generated using HTML5 Canvas — no cloud APIs needed.
 */

export type ImageOptions = {
  width: number
  height: number
  format: 'png' | 'jpeg' | 'webp'
  quality?: number
}

export type GradientImageOptions = ImageOptions & {
  type: 'gradient'
  colors: string[]
  direction?: 'horizontal' | 'vertical' | 'diagonal' | 'radial'
}

export type TextPosterOptions = ImageOptions & {
  type: 'text-poster'
  text: string
  subtitle?: string
  backgroundColor?: string
  textColor?: string
  fontSize?: number
  fontFamily?: string
  textAlign?: 'center' | 'left' | 'right'
}

export type ArtOptions = ImageOptions & {
  type: 'art'
  style: 'geometric' | 'abstract' | 'circles' | 'waves' | 'noise'
  colorPalette: string[]
  complexity?: number
}

export type AvatarOptions = ImageOptions & {
  type: 'avatar'
  initials: string
  backgroundColor?: string
  textColor?: string
  fontSize?: number
}

export type BannerOptions = ImageOptions & {
  type: 'banner'
  title: string
  subtitle?: string
  gradientColors: [string, string]
  pattern?: 'dots' | 'lines' | 'none'
}

export type AnyImageOptions =
  | GradientImageOptions
  | TextPosterOptions
  | ArtOptions
  | AvatarOptions
  | BannerOptions

const DEFAULT_QUALITY = 0.92

class OfflineImageGenerator {
  /**
   * Generate an image from options.
   * Returns a Blob URL.
   */
  async generate(options: AnyImageOptions): Promise<string> {
    const canvas = document.createElement('canvas')
    canvas.width = options.width
    canvas.height = options.height
    const ctx = canvas.getContext('2d')!
    if (!ctx) throw new Error('Canvas 2D not available')

    switch (options.type) {
      case 'gradient':
        this._drawGradient(ctx, options)
        break
      case 'text-poster':
        this._drawTextPoster(ctx, options)
        break
      case 'art':
        this._drawArt(ctx, options)
        break
      case 'avatar':
        this._drawAvatar(ctx, options)
        break
      case 'banner':
        this._drawBanner(ctx, options)
        break
      default:
        this._drawGradient(ctx, options as GradientImageOptions)
    }

    const mimeType = options.format === 'jpeg' ? 'image/jpeg' : options.format === 'webp' ? 'image/webp' : 'image/png'
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error('Canvas toBlob failed'))),
        mimeType,
        options.quality ?? DEFAULT_QUALITY
      )
    })

    return URL.createObjectURL(blob)
  }

  /**
   * Generate and return a Blob directly.
   */
  async generateBlob(options: AnyImageOptions): Promise<Blob> {
    const canvas = document.createElement('canvas')
    canvas.width = options.width
    canvas.height = options.height
    const ctx = canvas.getContext('2d')!
    if (!ctx) throw new Error('Canvas 2D not available')

    switch (options.type) {
      case 'gradient':
        this._drawGradient(ctx, options)
        break
      case 'text-poster':
        this._drawTextPoster(ctx, options)
        break
      case 'art':
        this._drawArt(ctx, options)
        break
      case 'avatar':
        this._drawAvatar(ctx, options)
        break
      case 'banner':
        this._drawBanner(ctx, options)
        break
    }

    const mimeType = options.format === 'jpeg' ? 'image/jpeg' : options.format === 'webp' ? 'image/webp' : 'image/png'
    return new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error('Canvas toBlob failed'))),
        mimeType,
        options.quality ?? DEFAULT_QUALITY
      )
    })
  }

  // ===================================================================
  // Gradient
  // ===================================================================

  private _drawGradient(ctx: CanvasRenderingContext2D, opts: GradientImageOptions) {
    const { width, height, colors, direction = 'diagonal' } = opts
    let gradient: CanvasGradient

    switch (direction) {
      case 'horizontal':
        gradient = ctx.createLinearGradient(0, 0, width, 0)
        break
      case 'vertical':
        gradient = ctx.createLinearGradient(0, 0, 0, height)
        break
      case 'radial':
        gradient = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, Math.max(width, height) / 2)
        break
      case 'diagonal':
      default:
        gradient = ctx.createLinearGradient(0, 0, width, height)
        break
    }

    colors.forEach((color, i) => {
      gradient.addColorStop(i / Math.max(colors.length - 1, 1), color)
    })

    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, width, height)

    // Add subtle noise texture
    this._addNoiseTexture(ctx, width, height, 0.03)
  }

  // ===================================================================
  // Text Poster
  // ===================================================================

  private _drawTextPoster(ctx: CanvasRenderingContext2D, opts: TextPosterOptions) {
    const { width, height, text, subtitle, backgroundColor, textColor, fontSize, fontFamily, textAlign } = opts

    // Background
    const bg = backgroundColor || this._randomColor()
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, width, height)

    // Decorative element
    this._drawDecorations(ctx, width, height)

    // Main text
    const mainFontSize = fontSize || Math.max(36, Math.min(width / 15, 80))
    ctx.fillStyle = textColor || '#ffffff'
    ctx.font = `bold ${mainFontSize}px ${fontFamily || '"Segoe UI", system-ui, sans-serif'}`
    ctx.textAlign = textAlign || 'center'
    ctx.textBaseline = 'middle'

    const maxWidth = width * 0.85
    const words = text.split(' ')
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

    const lineHeight = mainFontSize * 1.3
    const totalHeight = lines.length * lineHeight
    let y = height / 2 - totalHeight / 2 + lineHeight / 2
    const x = textAlign === 'center' ? width / 2 : textAlign === 'right' ? width * 0.85 : width * 0.1

    ctx.shadowColor = 'rgba(0,0,0,0.4)'
    ctx.shadowBlur = 15
    ctx.shadowOffsetX = 2
    ctx.shadowOffsetY = 2

    for (const line of lines) {
      ctx.fillText(line, x, y)
      y += lineHeight
    }

    // Subtitle
    if (subtitle) {
      ctx.shadowBlur = 8
      ctx.fillStyle = textColor === '#ffffff' ? 'rgba(255,255,255,0.75)' : 'rgba(0,0,0,0.5)'
      ctx.font = `${mainFontSize * 0.45}px ${fontFamily || '"Segoe UI", system-ui, sans-serif'}`
      ctx.fillText(subtitle, width / 2, height - mainFontSize)
    }

    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
  }

  // ===================================================================
  // Art
  // ===================================================================

  private _drawArt(ctx: CanvasRenderingContext2D, opts: ArtOptions) {
    const { width, height, style, colorPalette, complexity = 5 } = opts
    const colors = colorPalette.length > 0 ? colorPalette : this._randomPalette()

    // Background
    ctx.fillStyle = colors[0] || '#0f172a'
    ctx.fillRect(0, 0, width, height)

    switch (style) {
      case 'geometric':
        this._drawGeometric(ctx, width, height, colors, complexity)
        break
      case 'abstract':
        this._drawAbstract(ctx, width, height, colors, complexity)
        break
      case 'circles':
        this._drawCircles(ctx, width, height, colors, complexity)
        break
      case 'waves':
        this._drawWaves(ctx, width, height, colors, complexity)
        break
      case 'noise':
        this._drawNoise(ctx, width, height, colors, complexity)
        break
    }
  }

  private _drawGeometric(ctx: CanvasRenderingContext2D, w: number, h: number, colors: string[], complexity: number) {
    const count = complexity * 8
    for (let i = 0; i < count; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const size = Math.random() * 100 + 20
      ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)] + '40'
      ctx.strokeStyle = colors[Math.floor(Math.random() * colors.length)] + '80'
      ctx.lineWidth = 2

      if (Math.random() > 0.5) {
        ctx.fillRect(x - size / 2, y - size / 2, size, size)
        ctx.strokeRect(x - size / 2, y - size / 2, size, size)
      } else {
        ctx.beginPath()
        ctx.moveTo(x, y - size / 2)
        ctx.lineTo(x + size / 2, y + size / 2)
        ctx.lineTo(x - size / 2, y + size / 2)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      }
    }
  }

  private _drawAbstract(ctx: CanvasRenderingContext2D, w: number, h: number, colors: string[], complexity: number) {
    for (let i = 0; i < complexity * 5; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const radius = Math.random() * 150 + 30
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
      const color = colors[Math.floor(Math.random() * colors.length)]
      gradient.addColorStop(0, color + 'cc')
      gradient.addColorStop(1, color + '00')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  private _drawCircles(ctx: CanvasRenderingContext2D, w: number, h: number, colors: string[], complexity: number) {
    const cx = w / 2
    const cy = h / 2
    const maxR = Math.min(w, h) * 0.45
    const count = complexity * 3

    for (let i = count; i > 0; i--) {
      const r = (maxR / count) * i
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.fillStyle = colors[i % colors.length] + '60'
      ctx.fill()
      ctx.strokeStyle = colors[i % colors.length] + 'aa'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }
  }

  private _drawWaves(ctx: CanvasRenderingContext2D, w: number, h: number, colors: string[], complexity: number) {
    const layers = complexity * 3
    for (let l = 0; l < layers; l++) {
      ctx.beginPath()
      const yBase = (h / layers) * l + h / layers / 2
      const amplitude = 30 + l * 10
      const frequency = 0.005 + l * 0.002
      const color = colors[l % colors.length]

      ctx.moveTo(0, yBase)
      for (let x = 0; x <= w; x += 2) {
        const y = yBase + Math.sin(x * frequency + l * 0.5) * amplitude
        ctx.lineTo(x, y)
      }
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fillStyle = color + '50'
      ctx.fill()
    }
  }

  private _drawNoise(ctx: CanvasRenderingContext2D, w: number, h: number, colors: string[], complexity: number) {
    const imageData = ctx.getImageData(0, 0, w, h)
    const data = imageData.data
    for (let i = 0; i < data.length; i += 4) {
      const noise = (Math.random() - 0.5) * 60 * (complexity / 5)
      data[i] = Math.min(255, Math.max(0, data[i] + noise))
      data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise))
      data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise))
    }
    ctx.putImageData(imageData, 0, 0)

    // Overlay color blobs
    for (let i = 0; i < complexity; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const r = Math.random() * 200 + 50
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, r)
      const color = colors[Math.floor(Math.random() * colors.length)]
      gradient.addColorStop(0, color + '30')
      gradient.addColorStop(1, color + '00')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, w, h)
    }
  }

  // ===================================================================
  // Avatar
  // ===================================================================

  private _drawAvatar(ctx: CanvasRenderingContext2D, opts: AvatarOptions) {
    const { width, height, initials, backgroundColor, textColor } = opts
    const size = Math.min(width, height)
    const cx = width / 2
    const cy = height / 2
    const radius = size / 2 - 4

    // Circle background
    const bg = backgroundColor || this._randomColor()
    ctx.fillStyle = bg
    ctx.beginPath()
    ctx.arc(cx, cy, radius, 0, Math.PI * 2)
    ctx.fill()

    // Inner highlight
    const highlight = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, 0, cx, cy, radius)
    highlight.addColorStop(0, 'rgba(255,255,255,0.3)')
    highlight.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = highlight
    ctx.beginPath()
    ctx.arc(cx, cy, radius, 0, Math.PI * 2)
    ctx.fill()

    // Initials
    const displayInitials = initials.slice(0, 2).toUpperCase()
    const fontSize = Math.max(24, radius * 0.6)
    ctx.fillStyle = textColor || '#ffffff'
    ctx.font = `bold ${fontSize}px "Segoe UI", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(displayInitials, cx, cy + fontSize * 0.1)
  }

  // ===================================================================
  // Banner
  // ===================================================================

  private _drawBanner(ctx: CanvasRenderingContext2D, opts: BannerOptions) {
    const { width, height, title, subtitle, gradientColors, pattern } = opts

    // Background gradient
    const gradient = ctx.createLinearGradient(0, 0, width, 0)
    gradient.addColorStop(0, gradientColors[0])
    gradient.addColorStop(1, gradientColors[1])
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, width, height)

    // Pattern overlay
    if (pattern === 'dots') {
      ctx.fillStyle = 'rgba(255,255,255,0.08)'
      for (let x = 20; x < width; x += 30) {
        for (let y = 20; y < height; y += 30) {
          ctx.beginPath()
          ctx.arc(x, y, 2, 0, Math.PI * 2)
          ctx.fill()
        }
      }
    } else if (pattern === 'lines') {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)'
      ctx.lineWidth = 1
      for (let x = 0; x < width; x += 20) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, height)
        ctx.stroke()
      }
    }

    // Title
    const fontSize = Math.max(32, Math.min(width / 12, 64))
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold ${fontSize}px "Segoe UI", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.shadowColor = 'rgba(0,0,0,0.3)'
    ctx.shadowBlur = 10
    ctx.fillText(title, width / 2, height / 2 - (subtitle ? fontSize * 0.5 : 0))

    // Subtitle
    if (subtitle) {
      ctx.shadowBlur = 5
      ctx.fillStyle = 'rgba(255,255,255,0.8)'
      ctx.font = `${fontSize * 0.4}px "Segoe UI", system-ui, sans-serif`
      ctx.fillText(subtitle, width / 2, height / 2 + fontSize * 0.6)
    }

    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
  }

  // ===================================================================
  // Helpers
  // ===================================================================

  private _drawDecorations(ctx: CanvasRenderingContext2D, w: number, h: number) {
    // Subtle corner accent
    ctx.fillStyle = 'rgba(255,255,255,0.05)'
    ctx.fillRect(0, 0, w, 4)
    ctx.fillRect(0, 0, 4, h)
    ctx.fillRect(w - 4, 0, 4, h)
    ctx.fillRect(0, h - 4, w, 4)
  }

  private _addNoiseTexture(ctx: CanvasRenderingContext2D, w: number, h: number, intensity: number) {
    const imageData = ctx.getImageData(0, 0, w, h)
    const data = imageData.data
    for (let i = 0; i < data.length; i += 4) {
      const noise = (Math.random() - 0.5) * 255 * intensity
      data[i] = Math.min(255, Math.max(0, data[i] + noise))
      data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise))
      data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise))
    }
    ctx.putImageData(imageData, 0, 0)
  }

  private _randomColor(): string {
    const colors = [
      '#1e3a5f', '#4c1d95', '#065f46', '#7c2d12', '#881337',
      '#0f172a', '#1e40af', '#4a1942', '#0f766e', '#6b21a8',
      '#0369a1', '#b91c1c', '#166534', '#a21caf', '#1d4ed8',
    ]
    return colors[Math.floor(Math.random() * colors.length)]
  }

  private _randomPalette(): string[] {
    const palettes = [
      ['#1e3a5f', '#3b82f6', '#93c5fd', '#1e40af'],
      ['#4c1d95', '#8b5cf6', '#c4b5fd', '#6d28d9'],
      ['#065f46', '#10b981', '#6ee7b7', '#047857'],
      ['#7c2d12', '#f97316', '#fdba74', '#c2410c'],
      ['#0f172a', '#334155', '#64748b', '#cbd5e1'],
      ['#881337', '#f43f5e', '#fda4af', '#be123c'],
      ['#1e40af', '#60a5fa', '#bfdbfe', '#1d4ed8'],
    ]
    return palettes[Math.floor(Math.random() * palettes.length)]
  }

  /**
   * Convenience: Generate a gradient image and return the blob URL.
   */
  async gradient(params: { colors: string[]; width?: number; height?: number; direction?: 'horizontal' | 'vertical' | 'diagonal' | 'radial' }): Promise<string> {
    return this.generate({
      type: 'gradient',
      width: params.width || 1920,
      height: params.height || 1080,
      format: 'png',
      colors: params.colors,
      direction: params.direction || 'diagonal',
    })
  }

  /**
   * Convenience: Generate a text poster.
   */
  async poster(params: { text: string; subtitle?: string; width?: number; height?: number }): Promise<string> {
    return this.generate({
      type: 'text-poster',
      width: params.width || 1080,
      height: params.height || 1080,
      format: 'png',
      text: params.text,
      subtitle: params.subtitle,
    })
  }

  /**
   * Convenience: Generate abstract art.
   */
  async art(params: { style?: 'geometric' | 'abstract' | 'circles' | 'waves' | 'noise'; width?: number; height?: number }): Promise<string> {
    return this.generate({
      type: 'art',
      width: params.width || 1920,
      height: params.height || 1080,
      format: 'png',
      style: params.style || 'abstract',
      colorPalette: ['#3b82f6', '#8b5cf6', '#06b6d4', '#f43f5e'],
      complexity: 6,
    })
  }

  /**
   * Convenience: Generate an avatar.
   */
  async avatar(params: { initials: string; size?: number; backgroundColor?: string }): Promise<string> {
    const size = params.size || 256
    return this.generate({
      type: 'avatar',
      width: size,
      height: size,
      format: 'png',
      initials: params.initials,
      backgroundColor: params.backgroundColor,
    })
  }

  /**
   * Convenience: Generate a banner.
   */
  async banner(params: { title: string; subtitle?: string; width?: number; height?: number }): Promise<string> {
    return this.generate({
      type: 'banner',
      width: params.width || 1920,
      height: params.height || 600,
      format: 'png',
      title: params.title,
      subtitle: params.subtitle,
      gradientColors: ['#1e3a5f', '#4c1d95'],
      pattern: 'dots',
    })
  }
}

export const offlineImageGenerator = new OfflineImageGenerator()

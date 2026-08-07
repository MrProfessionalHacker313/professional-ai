/**
 * Professional AI - Local AI Engine (transformers.js)
 * Runs DeepSeek Coder 1.3B / Qwen2.5 Coder 0.5B / Phi-3 Mini ONNX models
 * entirely on-device. No Ollama, no GPU, no internet needed.
 */

// Dynamic import of transformers.js (loaded on demand to keep initial bundle small)
let pipelineModule: any = null

export type OfflineModelId = 'qwen2.5-coder-0.5b' | 'deepseek-coder-1.3b' | 'phi-3-mini'

export interface OfflineModelInfo {
  id: OfflineModelId
  name: string
  size: string
  description: string
  huggingFaceId: string
  quantized: boolean
}

export const OFFLINE_MODELS: OfflineModelInfo[] = [
  {
    id: 'qwen2.5-coder-0.5b',
    name: 'Qwen2.5 Coder 0.5B',
    size: '~250 MB',
    description: 'Fastest, lightest. Great for code completion & simple fixes.',
    huggingFaceId: 'onnx-community/Qwen2.5-Coder-0.5B-Instruct',
    quantized: true,
  },
  {
    id: 'deepseek-coder-1.3b',
    name: 'DeepSeek Coder 1.3B',
    size: '~700 MB',
    description: 'Best quality-to-size ratio for offline coding.',
    huggingFaceId: 'onnx-community/deepseek-coder-1.3b-instruct',
    quantized: true,
  },
  {
    id: 'phi-3-mini',
    name: 'Phi-3 Mini 3.8B',
    size: '~2.2 GB',
    description: 'Highest quality offline model. Needs more RAM.',
    huggingFaceId: 'onnx-community/Phi-3-mini-4k-instruct',
    quantized: true,
  },
]

const MODEL_STORAGE_KEY = 'proai_offline_model'
const MODEL_DOWNLOADED_KEY = 'proai_model_downloaded'

class OfflineAIEngine {
  private generator: any = null
  private currentModel: OfflineModelId | null = null
  private loading = false
  private loadPromise: Promise<any> | null = null

  /**
   * Check if transformers.js is available (loaded on demand).
   */
  async isAvailable(): Promise<boolean> {
    try {
      if (pipelineModule) return true
      // Try to load the module
      await this._loadModule()
      return true
    } catch (e) {
      return false
    }
  }

  private async _loadModule(): Promise<any> {
    if (pipelineModule) return pipelineModule
    // Dynamic import — transformers.js is loaded at runtime from CDN to avoid
    // bundling onnxruntime-web (which uses import.meta and native .node files).
    // This keeps the app bundle small. After first load it's cached by the
    // service worker for fully offline operation.
    const moduleUrl = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.0/+esm'
    const mod = await new Function('url', `return import(url)`)(moduleUrl)
    pipelineModule = mod
    return mod
  }

  /**
   * Load the selected model into memory (runs once, stays loaded).
   */
  async loadModel(modelId: OfflineModelId = 'qwen2.5-coder-0.5b'): Promise<any> {
    if (this.generator && this.currentModel === modelId) {
      return this.generator
    }
    if (this.loadPromise) return this.loadPromise

    this.loading = true
    this.loadPromise = (async () => {
      try {
        const mod = await this._loadModule()
        const model = OFFLINE_MODELS.find((m) => m.id === modelId) || OFFLINE_MODELS[0]

        // Use the pipeline API for text generation
        this.generator = await mod.pipeline('text-generation', model.huggingFaceId, {
          dtype: 'q8',
          device: 'wasm',
          progress_callback: (progress: any) => {
            if (progress.status === 'progress') {
              this._emitProgress(progress.file, progress.progress)
            }
          },
        })
        this.currentModel = modelId
        localStorage.setItem(MODEL_STORAGE_KEY, modelId)
        localStorage.setItem(MODEL_DOWNLOADED_KEY, 'true')
        return this.generator
      } finally {
        this.loading = false
        this.loadPromise = null
      }
    })()

    return this.loadPromise
  }

  private _emitProgress(file: string, progress: number) {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('proai-model-progress', {
        detail: { file, progress },
      }))
    }
  }

  /**
   * Check if a model has been downloaded to device.
   */
  isModelDownloaded(): boolean {
    if (typeof window === 'undefined') return false
    return localStorage.getItem(MODEL_DOWNLOADED_KEY) === 'true'
  }

  /**
   * Get the currently selected model.
   */
  getSelectedModel(): OfflineModelId {
    if (typeof window === 'undefined') return 'qwen2.5-coder-0.5b'
    return (localStorage.getItem(MODEL_STORAGE_KEY) as OfflineModelId) || 'qwen2.5-coder-0.5b'
  }

  /**
   * Generate a response using the local model.
   * Falls back to knowledge-index answers if model not loaded.
   */
  async generate(
    prompt: string,
    mode: 'chat' | 'code' | 'security' | 'bugfix' = 'chat',
    knowledgeContext?: string
  ): Promise<{ content: string; model: string; offline: boolean }> {
    // If model not downloaded, use knowledge index fallback
    if (!this.isModelDownloaded()) {
      return {
        content: this._knowledgeFallback(prompt, mode, knowledgeContext),
        model: 'knowledge-index',
        offline: true,
      }
    }

    try {
      const gen = await this.loadModel(this.getSelectedModel())
      const systemPrompt = this._getSystemPrompt(mode)

      const result = await gen(
        `${systemPrompt}\n\nUser: ${prompt}\n\nAssistant:`,
        {
          max_new_tokens: 512,
          temperature: 0.7,
          top_p: 0.9,
          do_sample: true,
        }
      )

      const text = Array.isArray(result)
        ? result[0]?.generated_text || ''
        : result?.generated_text || ''

      // Strip the prompt from the output
      const content = text.replace(`${systemPrompt}\n\nUser: ${prompt}\n\nAssistant:`, '').trim()

      return {
        content: content || 'No response generated.',
        model: this.getSelectedModel(),
        offline: true,
      }
    } catch (e) {
      console.error('[OfflineAI] Generation failed:', e)
      return {
        content: this._knowledgeFallback(prompt, mode, knowledgeContext),
        model: 'knowledge-index',
        offline: true,
      }
    }
  }

  private _getSystemPrompt(mode: string): string {
    const prompts: Record<string, string> = {
      chat: 'You are Professional AI running fully offline. Answer accurately and concisely.',
      code: 'You are an offline code assistant. Write complete, working code with imports and comments.',
      security: 'You are a cybersecurity expert running offline. Provide accurate security information.',
      bugfix: 'You are a bug fixer running offline. Identify root causes and provide complete fixes.',
    }
    return prompts[mode] || prompts.chat
  }

  private _knowledgeFallback(prompt: string, mode: string, knowledgeContext?: string): string {
    if (knowledgeContext) {
      return `📚 **Offline Knowledge Answer**\n\n${knowledgeContext}\n\n---\n*This answer came from the local knowledge index. Download the Offline AI Pack for full local model responses.*`
    }
    return `You are offline and the local AI model is not yet downloaded.\n\n**To enable full offline AI:**\n1. Go online once\n2. Open Settings → Offline AI Pack\n3. Download the model (~250 MB)\n4. After that, all coding/chat works 100% offline\n\nMeanwhile, use the **Offline Search** for instant knowledge answers.`
  }
}

export const offlineAI = new OfflineAIEngine()
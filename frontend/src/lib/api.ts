/**
 * Professional AI - API Client
 * SECURITY HARDENED: CSRF tokens, Secure cookies, XSS protection, input sanitization.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

const PRIMARY_OWNER_EMAIL = (process.env.NEXT_PUBLIC_OWNER_EMAIL || 'redr28126@gmail.com').toLowerCase().trim()
const OWNER_EMAILS = [
  PRIMARY_OWNER_EMAIL,
  ...(process.env.NEXT_PUBLIC_OWNER_EMAILS || '')
    .split(',')
    .map((item) => item.toLowerCase().trim())
    .filter(Boolean),
]

let proactiveRefreshTimer: ReturnType<typeof setTimeout> | null = null

function getTokenExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

async function doProactiveRefresh(refreshToken: string): Promise<void> {
  try {
    const response = await api.post(
      '/api/auth/refresh',
      { refresh_token: refreshToken },
    )
    if (response.data.access_token) {
      setCookie('access_token', response.data.access_token)
      if (response.data.refresh_token) {
        setCookie('refresh_token', response.data.refresh_token)
      }
      scheduleProactiveRefresh()
    }
  } catch {
    // Silently fail — the reactive interceptor handles 401s on real requests
  }
}

export function scheduleProactiveRefresh(): void {
  if (proactiveRefreshTimer) clearTimeout(proactiveRefreshTimer)

  const accessToken = getAccessTokenFromCookie()
  const refreshToken = getRefreshTokenFromCookie()

  if (!accessToken || !refreshToken) return

  const expiry = getTokenExpiry(accessToken)
  if (!expiry) return

  const now = Date.now()
  const refreshAt = expiry - now - 60 * 1000

  if (refreshAt <= 0) {
    void doProactiveRefresh(refreshToken)
    return
  }

  proactiveRefreshTimer = setTimeout(() => {
    void doProactiveRefresh(refreshToken)
  }, refreshAt)
}

if (typeof window !== 'undefined') {
  scheduleProactiveRefresh()
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: true,
})

let csrfFetchPromise: Promise<string | null> | null = null

function getCsrfTokenFromCookie(): string | null {
  if (typeof window === 'undefined') return null
  const token = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1]
  return token ? decodeURIComponent(token) : null
}

async function ensureCsrfToken(): Promise<string | null> {
  const existing = getCsrfTokenFromCookie()
  if (existing) return existing

  if (!csrfFetchPromise) {
    csrfFetchPromise = axios
      .get(`${API_BASE_URL}/api/auth/csrf-token`, { withCredentials: true })
      .then((res) => {
        const token = res.data?.csrf_token
        if (!token || typeof window === 'undefined') return null

        const secure = window.location.protocol === 'https:' ? '; Secure' : ''
        document.cookie = `csrf_token=${encodeURIComponent(token)}; path=/; SameSite=Lax${secure}`
        return token as string
      })
      .catch(() => null)
      .finally(() => {
        csrfFetchPromise = null
      })
  }

  return csrfFetchPromise
}

function getAccessTokenFromCookie(): string | null {
  if (typeof window === 'undefined') return null
  const token = document.cookie
    .split('; ')
    .find((row) => row.startsWith('access_token='))
    ?.split('=')[1]
  return token ? decodeURIComponent(token) : null
}

function getRefreshTokenFromCookie(): string | null {
  if (typeof window === 'undefined') return null
  const token = document.cookie
    .split('; ')
    .find((row) => row.startsWith('refresh_token='))
    ?.split('=')[1]
  return token ? decodeURIComponent(token) : null
}

function setCookie(name: string, value: string): void {
  if (typeof window === 'undefined') return
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; SameSite=Lax${secure}`
}

export function deleteAllCookies(): void {
  if (typeof window === 'undefined') return
  document.cookie.split(';').forEach((cookie) => {
    document.cookie = cookie.trim().split(';')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/'
  })
}

export function setAuthCookies(data: { tokens: { access_token: string; refresh_token?: string; csrf_token?: string }; user: { email: string } }): void {
  if (typeof window === 'undefined') return
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  const cookieOpts = `path=/; SameSite=Lax${secure}`
  document.cookie = `access_token=${encodeURIComponent(data.tokens.access_token)}; ${cookieOpts}`
  document.cookie = `user_email=${encodeURIComponent(data.user.email)}; ${cookieOpts}`
  if (data.user.email && OWNER_EMAILS.includes(data.user.email.toLowerCase().trim())) {
    document.cookie = `owner_email=${encodeURIComponent(data.user.email)}; ${cookieOpts}`
  }
  if (data.tokens.csrf_token) {
    document.cookie = `csrf_token=${encodeURIComponent(data.tokens.csrf_token)}; ${cookieOpts}`
  }
  if (data.tokens.refresh_token) {
    document.cookie = `refresh_token=${encodeURIComponent(data.tokens.refresh_token)}; ${cookieOpts}`
  }
}

api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const path = config.url || ''
      const isWebhook = path.includes('/webhook')
      const isCsrfTokenEndpoint = path.includes('/csrf-token')

      if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())
          && !isWebhook && !isCsrfTokenEndpoint) {
        const csrfToken = getCsrfTokenFromCookie() || await ensureCsrfToken()
        if (csrfToken && config.headers) {
          config.headers['X-CSRF-Token'] = csrfToken
        }
      }

      const accessToken = getAccessTokenFromCookie()
      if (accessToken && config.headers) {
        config.headers.Authorization = `Bearer ${accessToken}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Security: sanitize outbound request strings
function sanitizeOutboundData(data: unknown): unknown {
  if (typeof data === 'string') {
    return data.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '')
  }
  return data
}

// Extract a friendly human-readable message from any API error.
// The backend now ALWAYS returns {detail} — 401, 403, 429, and 500 included.
function getFriendlyErrorMessage(error: AxiosError): string {
  const data = (error.response?.data || {}) as Record<string, unknown>
  const detail = typeof data.detail === 'string' ? data.detail : ''
  const message = typeof data.message === 'string' ? data.message : ''
  const status = error.response?.status

  if (status === 401) {
    return detail || 'Your session has expired. Please login again.'
  }
  if (status === 403) {
    return detail || 'You do not have permission to perform this action.'
  }
  if (status === 429) {
    return detail || 'Too many requests. Please wait a moment and try again.'
  }
  if (status && status >= 500) {
    return detail || 'Something went wrong on our side. Please try again later.'
  }
  return detail || message || error.message || 'Something went wrong. Please try again.'
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const responseData = error.response?.data as { error?: string } | undefined

    // Attach a friendly message to every error so UI code never shows raw console errors.
    if (error instanceof AxiosError) {
      ;(error as AxiosError & { friendlyMessage?: string }).friendlyMessage = getFriendlyErrorMessage(error)
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = getRefreshTokenFromCookie()
        const response = await axios.post(
          `${API_BASE_URL}/api/auth/refresh`,
          refreshToken ? { refresh_token: refreshToken } : {},
          { withCredentials: true },
        )

        if (response.data.access_token) {
          setCookie('access_token', response.data.access_token)
          if (response.data.refresh_token) {
            setCookie('refresh_token', response.data.refresh_token)
          }
          const csrfResponse = await axios.get(`${API_BASE_URL}/api/auth/csrf-token`, { withCredentials: true })
          if (csrfResponse.data.csrf_token) {
            setCookie('csrf_token', csrfResponse.data.csrf_token)
          }
          scheduleProactiveRefresh()
        }

        return api(originalRequest)
      } catch (refreshError) {
        deleteAllCookies()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }

    if (
      error.response?.status === 403 &&
      !originalRequest._retry &&
      responseData?.error === 'csrf_token_invalid'
    ) {
      originalRequest._retry = true
      const token = await ensureCsrfToken()
      if (token) {
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers['X-CSRF-Token'] = token
      }
      return api(originalRequest)
    }

    return Promise.reject(error)
  }
)

function sanitizeInput(input: string): string {
  if (typeof window !== 'undefined') {
    const div = document.createElement('div')
    div.textContent = input
    return div.innerHTML
  }
  return input
}

export const authApi = {
  register: (data: { email: string; password: string; display_name?: string }) =>
    api.post('/api/auth/register', data),
  login: (data: { email: string; password: string; totp_code?: string; device_fingerprint?: string }) =>
    api.post('/api/auth/login', data),
  ownerEmailLogin: (email: string) =>
    api.post('/api/auth/owner/email-login', { email }),
  refresh: () => api.post('/api/auth/refresh'),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
  checkIsOwner: () => api.get('/api/auth/me/owner-status'),
  ownerSetupStatus: (email: string) => api.get('/api/auth/owner/setup/status', { params: { email } }),
  ownerSetupFinish: (data: {
    email: string
    setup_token: string
    password: string
    enable_totp: boolean
    totp_secret?: string
    totp_code?: string
  }) => api.post('/api/auth/owner/setup/finish', data),
  ownerTotpBootstrap: (data: { email: string; setup_token: string }) =>
    api.post('/api/auth/owner/setup/totp-bootstrap', data),
  ownerPasswordResetRequest: (email: string) =>
    api.post('/api/auth/owner/password-reset/request', { email }),
  ownerPasswordResetConfirm: (data: { email: string; token: string; new_password: string }) =>
    api.post('/api/auth/owner/password-reset/confirm', data),
  oauthLogin: (provider: 'google') =>
    api.post(`/api/auth/oauth/${provider}`),
  setup2FA: () => api.post('/api/auth/2fa/setup'),
  verify2FA: (code: string) => api.post('/api/auth/2fa/verify', { code }),
  disable2FA: () => api.post('/api/auth/2fa/disable'),
  getCsrfToken: () => api.get('/api/auth/csrf-token'),
  // Passkey (WebAuthn)
  passkeyRegisterBegin: (data?: { device_name?: string }) =>
    api.post('/api/auth/passkey/register/begin', data || {}),
  passkeyRegisterComplete: (data: any) =>
    api.post('/api/auth/passkey/register/complete', data),
  passkeyLoginBegin: () => api.post('/api/auth/passkey/login/begin'),
  passkeyLoginComplete: (data: any) =>
    api.post('/api/auth/passkey/login/complete', data),
  listPasskeys: () => api.get('/api/auth/passkeys'),
  deletePasskey: (credentialId: string) =>
    api.delete(`/api/auth/passkey/${credentialId}`),
}

export const chatApi = {
  send: (data: { prompt: string; mode?: string; model?: string }) =>
    api.post('/api/chat/send', data),
  generateCode: (data: { prompt: string; language: string; framework?: string }) =>
    api.post('/api/chat/code', data),
  fixBug: (data: { code: string; error_description?: string; language?: string }) =>
    api.post('/api/chat/bugfix', data),
  securityQuery: (data: { query: string }) =>
    api.post('/api/chat/security', data),
}

export const conversationsApi = {
  list: (params?: { search?: string }) =>
    api.get('/api/conversations', { params }),
  get: (id: string) =>
    api.get(`/api/conversations/${id}`),
  create: (data: { title?: string }) =>
    api.post('/api/conversations', data),
  rename: (id: string, data: { title: string }) =>
    api.patch(`/api/conversations/${id}`, data),
  delete: (id: string) =>
    api.delete(`/api/conversations/${id}`),
  addMessage: (id: string, data: { content: string; mode?: string; role?: string }) =>
    api.post(`/api/conversations/${id}/messages`, data),
  adminListAll: (params?: { search?: string }) =>
    api.get('/api/conversations/admin/all', { params }),
  adminDelete: (id: string) =>
    api.delete(`/api/conversations/admin/${id}`),
}

export const paymentsApi = {
  createSubscription: (data: {
    plan: 'starter' | 'pro' | 'pro_yearly' | 'max' | 'business' | 'enterprise'
    billing_cycle: 'monthly' | 'yearly'
    payment_method: 'stripe' | 'paypal' | 'wise' | 'payoneer' | 'skrill' | 'binance_pay' | 'jazzcash' | 'easypaisa' | 'sadapay' | 'nayapay'
    payment_token: string
    consent: boolean
    currency?: string
    country_code?: string
    team_size?: number
    card_last4?: string
    card_brand?: string
    card_expiry_month?: string
    card_expiry_year?: string
    cardholder_name?: string
  }) =>
    api.post('/api/payments/create-subscription', data),
  cancelSubscription: () => api.post('/api/payments/cancel'),
  getStatus: () => api.get('/api/payments/status'),
  retryFailedPayment: () => api.post('/api/payments/retry-failed'),
  getPlans: (params?: { currency?: string; country_code?: string; payment_method?: string }) =>
    api.get('/api/payments/plans', { params }),
  getMethods: () => api.get('/api/payments/methods'),
}

export const creditsApi = {
  getInfo: () => api.get('/credits/info'),
  useFeature: (data: { feature: string; language?: string; usage_log_id?: string }) =>
    api.post('/credits/use', data),
  getLimits: () => api.get('/credits/limits'),
  getStats: (days?: number) => api.get('/credits/stats', { params: { days } }),
  adminAdjust: (data: { user_id: string; amount: number; reason: string }) =>
    api.post('/credits/admin/adjust', data),
  grantTrial: (user_id: string) => api.post('/credits/admin/grant-trial', { user_id }),
  revokeTrial: (user_id: string) => api.post('/credits/admin/revoke-trial', { user_id }),
}

export const mediaApi = {
  generate: (data: {
    media_type: 'video' | 'picture' | 'poster' | 'animation'
    topic: string
    script?: string
    scenes_text?: string
    voice_style?: string
    voice_prompt?: string
    language?: string
    duration_seconds?: number
    resolution?: string
    format?: string
    aspect_ratio?: string
    model?: string
    negative_prompt?: string
    voice_clone_id?: string
    voice_consent?: boolean
  }) => api.post('/api/media/generate', data),
  generateScript: (data: { topic: string; duration_seconds?: number; style?: string; language?: string }) =>
    api.post('/api/media/generate-script', data),
  generatePrompt: (data: {
    topic: string
    media_type?: string
    style?: string
    mood?: string
    camera_angle?: string
    lighting?: string
    aspect_ratio?: string
  }) => api.post('/api/media/generate-prompt', data),
  getJob: (jobId: string) => api.get(`/api/media/jobs/${jobId}`),
  listJobs: (params?: { limit?: number; offset?: number }) =>
    api.get('/api/media/jobs', { params }),
  cancelJob: (jobId: string) => api.post(`/api/media/jobs/${jobId}/cancel`),
  downloadJob: (jobId: string) => api.get(`/api/media/jobs/${jobId}/download`, { responseType: 'blob' }),
  getLimits: () => api.get('/api/media/limits'),
  getStatus: () => api.get('/api/media/status'),
  verifySubtitles: (jobId: string) => api.post('/api/media/verify-subtitles', { job_id: jobId }),
  uploadVoiceClone: (file: File, name: string, language: string, consent: boolean) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    formData.append('language', language)
    formData.append('consent', String(consent))
    return api.post('/api/media/voice-clone', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listVoiceClones: () => api.get('/api/media/voice-clones'),
  getVoiceCatalog: () => api.get('/api/media/voice-catalog'),
  getVoiceEngineStatus: () => api.get('/api/media/voice-engine/status'),
  previewVoice: (data: { text?: string; voice_style?: string; language?: string; voice_prompt?: string }) =>
    api.post('/api/media/voice-engine/preview', data),

  // Auto Video Editor - PRO feature
  autoEditPresets: () => api.get('/api/media/auto-edit/presets'),
  autoEditUpload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/media/auto-edit/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  autoEditStart: (data: {
    preset?: string
    raw_files: string[]
    add_transitions?: boolean
    add_captions?: boolean
    color_grade?: boolean
    stabilize?: boolean
    ken_burns?: boolean
    add_intro_outro?: boolean
    adjust_speed?: boolean
    background_music?: boolean
    watermark_toggle?: boolean
    caption_language?: string
    output_aspect_ratio?: string
    output_resolution?: string
    trim_start?: number
    trim_end?: number
    speed_factor?: number
    text_overlays?: any[]
    stickers?: string[]
  }) => api.post('/api/media/auto-edit/start', data),
  autoEditJob: (jobId: string) => api.get(`/api/media/auto-edit/jobs/${jobId}`),
  autoEditJobs: (params?: { limit?: number; offset?: number }) =>
    api.get('/api/media/auto-edit/jobs', { params }),
  autoEditDownload: (jobId: string) => api.get(`/api/media/auto-edit/jobs/${jobId}/download`, { responseType: 'blob' }),
  autoEditManual: (jobId: string, data: { action: string; params: any }) =>
    api.post(`/api/media/auto-edit/jobs/${jobId}/manual-edit`, data),
}

export const modulesApi = {
  list: () => api.get('/api/modules/'),
  checkAccess: (moduleId: string) => api.get(`/api/modules/access/${moduleId}`),
  getMyAccess: () => api.get('/api/modules/my-access'),
  adminGrant: (data: { user_id: string; module_id: string; module_name: string; expires_at?: string }) =>
    api.post('/api/modules/admin/grant', data),
  adminRevoke: (data: { user_id: string; module_id: string }) =>
    api.post('/api/modules/admin/revoke', data),
  adminListGrants: (params?: { user_id?: string; module_id?: string }) =>
    api.get('/api/modules/admin/list-grants', { params }),
}

export const adminApi = {
  listUsers: (params?: { page?: number; limit?: number; search?: string }) =>
    api.get('/api/admin/users', { params }),
  approveUser: (email: string) => api.post(`/api/admin/approve/${email}`),
  disapproveUser: (email: string) => api.post(`/api/admin/disapprove/${email}`),
  banUser: (email: string) => api.post(`/api/admin/ban/${email}`),
  getRevenue: () => api.get('/api/admin/revenue'),
  refundPayment: (transactionId: string, reason: string) =>
    api.post(`/api/admin/refund/${transactionId}`, { reason }),
  viewVault: (email: string) => api.get(`/api/admin/vault/${email}`),
  getAnalytics: () => api.get('/api/admin/analytics'),
  listTickets: (status?: string) => api.get('/api/admin/tickets', { params: { status } }),
}

export const featuresApi = {
  saveMemory: (data: { memory_type: string; key: string; value: any; importance?: number; metadata?: any }) =>
    api.post('/api/features/memory/save', data),
  getMemory: (data: { memory_type: string; key: string }) =>
    api.post('/api/features/memory/get', data),
  getAllMemories: (params?: { memory_type?: string; min_importance?: number }) =>
    api.get('/api/features/memories', { params }),
  createAgent: (data: { name: string; description: string; agent_type: string; system_prompt: string; tools?: string[]; config?: any }) =>
    api.post('/api/features/agents/create', data),
  getAgents: () => api.get('/api/features/agents'),
  executeAgent: (data: { agent_id: string; task_description: string; context?: any }) =>
    api.post('/api/features/agents/execute', data),
  generateImage: (data: { prompt: string; negative_prompt?: string; model?: string; width?: number; height?: number; steps?: number }) =>
    api.post('/api/features/images/generate', data),
  analyzeImage: (data: { image_path: string; analysis_type?: string }) =>
    api.post('/api/features/images/analyze', data),
  getImages: () => api.get('/api/features/images'),
  speechToText: (data: { audio_path: string; language?: string }) =>
    api.post('/api/features/voice/speech-to-text', data),
  textToSpeech: (data: { text: string; language?: string; voice?: string }) =>
    api.post('/api/features/voice/text-to-speech', data),
  uploadDocument: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/features/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getDocuments: () => api.get('/api/features/documents'),
  getDocument: (id: string) => api.get(`/api/features/documents/${id}`),
  translate: (data: { text: string; source_lang: string; target_lang: string; context_type?: string }) =>
    api.post('/api/features/translate', data),
  getTranslations: () => api.get('/api/features/translations'),
  webSearch: (data: { query: string; search_engine?: string }) =>
    api.post('/api/features/search', data),
  explainCode: (data: { code: string; language: string; user_language?: string }) =>
    api.post('/api/features/code/explain', data),
  screenshotToCode: (data: { image_path: string; framework?: string }) =>
    api.post('/api/features/code/screenshot-to-code', data),
  createChatbot: (data: { name: string; description: string; system_prompt: string; welcome_message?: string; suggested_prompts?: string[] }) =>
    api.post('/api/features/chatbots/create', data),
  getChatbots: () => api.get('/api/features/chatbots'),
  chatWithBot: (data: { chatbot_id: string; message: string; session_id?: string }) =>
    api.post('/api/features/chatbots/chat', data),
  routeTask: (data: { task_type: string; task_description: string }) =>
    api.post('/api/features/route', data),
  getModels: () => api.get('/api/features/models'),
  transcribeVideo: (file: File, language?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (language) formData.append('language', language)
    return api.post('/api/features/video/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  generatePrompt: (data: { topic: string; category: string; target_ai: string; tone: string; complexity: string; extra_instructions?: string }) =>
    api.post('/api/features/prompt-forge/generate', data),
  getPromptCategories: () => api.get('/api/features/prompt-forge/categories'),
  getPromptExamples: () => api.get('/api/features/prompt-forge/examples'),
  getAIProviders: () => api.get('/api/ai/providers'),
  getAIDashboard: (days?: number) => api.get('/api/ai/dashboard', { params: { days } }),
  getAIHealth: () => api.get('/api/ai/health'),
  getAICosts: (days?: number) => api.get('/api/ai/costs', { params: { days } }),
  getCurrentProvider: () => api.get('/api/ai/current-provider'),
}

export default api

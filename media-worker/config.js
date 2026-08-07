/**
 * Media Worker Configuration
 * Reads from environment variables with sensible defaults.
 */

const DEFAULT_TIMEOUT_MS = 10_000; // 10 seconds max per external call
const BULLMQ_PREFIX = "media-vault";
const PROGRESS_UPDATE_INTERVAL_MS = 1_000;

module.exports = {
  REDIS_URL: process.env.REDIS_URL || "redis://localhost:6379",
  REDIS_PASSWORD: process.env.REDIS_PASSWORD || undefined,
  BULLMQ_PREFIX,
  DEFAULT_TIMEOUT_MS: Number(process.env.MEDIA_TIMEOUT_MS) || DEFAULT_TIMEOUT_MS,
  PROGRESS_UPDATE_INTERVAL_MS,
  CONCURRENCY: Number(process.env.MEDIA_WORKER_CONCURRENCY) || 8,
  MAX_RETRIES: Number(process.env.MEDIA_MAX_RETRIES) || 3,
  BACKOFF_DELAY_MS: Number(process.env.MEDIA_BACKOFF_MS) || 5_000,

  // Provider keys (comma-separated, auto-rotated)
  FAL_KEYS: (process.env.FAL_KEYS || process.env.FAL_AI_API_KEY || "").split(",").filter(Boolean),
  REPLICATE_KEYS: (process.env.REPLICATE_KEYS || process.env.REPLICATE_API_KEY || "").split(",").filter(Boolean),
  KLING_KEYS: (process.env.KLING_KEYS || process.env.KLING_API_KEY || "").split(",").filter(Boolean),
  RUNWAY_KEYS: (process.env.RUNWAY_KEYS || process.env.RUNWAY_API_KEY || "").split(",").filter(Boolean),
  ELEVENLABS_KEYS: (process.env.ELEVENLABS_KEYS || process.env.ELEVENLABS_API_KEY || "").split(",").filter(Boolean),

  // Provider URLs
  FAL_API_URL: process.env.FAL_API_URL || "https://queue.fal.run",
  REPLICATE_API_URL: process.env.REPLICATE_API_URL || "https://api.replicate.com/v1",
  KLING_API_URL: process.env.KLING_API_URL || "https://api.klingai.com",
  RUNWAY_API_URL: process.env.RUNWAY_API_URL || "https://api.dev.runwayml.com/v1",
  ELEVENLABS_API_URL: process.env.ELEVENLABS_API_URL || "https://api.elevenlabs.io/v1",

  // GPU Server
  COMFYUI_URL: process.env.COMFYUI_URL || "http://localhost:8188",
  COMFYUI_ANIMATEDIFF_MODEL: process.env.COMFYUI_ANIMATEDIFF_MODEL || "guoyingzheng/animatediff",

  // GCS
  GOOGLE_CLOUD_PROJECT: process.env.GOOGLE_CLOUD_PROJECT,
  GOOGLE_CLOUD_STORAGE_BUCKET: process.env.GOOGLE_CLOUD_STORAGE_BUCKET,
  GOOGLE_APPLICATION_CREDENTIALS: process.env.GOOGLE_APPLICATION_CREDENTIALS,

  // Backend callback
  BACKEND_API_URL: process.env.BACKEND_API_URL || "http://localhost:8000",

  // Health monitor
  HEALTH_CHECK_INTERVAL_MS: Number(process.env.MEDIA_HEALTH_INTERVAL_MS) || 60_000,
};

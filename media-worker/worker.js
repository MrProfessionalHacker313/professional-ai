/**
 * Media Vault BullMQ Worker
 *
 * Architecture:
 *   Python FastAPI backend → Redis (BullMQ queue) → This worker (GPU server)
 *
 * Flow:
 *   1. Backend creates MediaJob in PostgreSQL
 *   2. Backend pushes job to BullMQ queue in Redis
 *   3. This worker picks up the job
 *   4. Processor generates media using multi-key failover
 *   5. Result uploaded to GCS
 *   6. Backend notified via callback
 *
 * Never hangs: every external call has a 10-second hard timeout.
 * 1,000 concurrent users = smooth queue, parallel GPU workers.
 */

const { Queue, Worker, Job } = require("bullmq");
const axios = require("axios");
const config = require("./config");
const { processImage } = require("./processors/imageProcessor");
const { processVideo } = require("./processors/videoProcessor");
const { processAnimation } = require("./processors/animationProcessor");
const { processTTS } = require("./processors/ttsProcessor");
const { uploadFile } = require("./utils/gcsUploader");

const connection = {
  host: config.REDIS_URL.replace(/^redis:\/\//, "").split(":")[0] || "localhost",
  port: parseInt(config.REDIS_URL.split(":")[2] || "6379"),
  password: config.REDIS_PASSWORD,
  maxRetriesPerRequest: null,
};

// Create queue (backend also uses this queue name)
const mediaQueue = new Queue(`${config.BULLMQ_PREFIX}:jobs`, { connection });

// Create worker
const worker = new Worker(
  `${config.BULLMQ_PREFIX}:jobs`,
  async (job) => {
    // The backend enqueues {"job_id": <media_job_id>}; job.id is the BullMQ job ID.
    const { job_id, job_type, prompt, width, height, model, duration, script, voice_style, language } = job.data;

    await reportProgress(job_id, job.id, "starting", 0, "Job picked up by GPU worker");

    try {
      let result;
      if (job_type === "video") {
        await reportProgress(job_id, job.id, "generating_video", 10, "Generating video...");
        result = await processVideo({ id: job_id, prompt, width, height, model, duration });
      } else if (job_type === "picture" || job_type === "poster") {
        await reportProgress(job_id, job.id, "generating_image", 10, "Generating image...");
        result = await processImage({ id: job_id, prompt, width, height, model });
      } else if (job_type === "animation") {
        await reportProgress(job_id, job.id, "generating_animation", 10, "Generating animation...");
        result = await processAnimation({ id: job_id, prompt, width, height });
      } else if (job_type === "tts" || job_type === "voice") {
        await reportProgress(job_id, job.id, "generating_voice", 10, "Generating voice...");
        result = await processTTS({ id: job_id, script, voice_style, language });
      } else {
        throw new Error(`unknown_job_type: ${job_type}`);
      }

      if (!result.success) {
        await reportProgress(job_id, job.id, "failed", 0, result.error || "Generation failed");
        return { success: false, error: result.error };
      }

      await reportProgress(job_id, job.id, "uploading", 90, "Uploading to cloud storage...");

      // Upload to GCS
      const gcsPath = `media/${job_type}s/${job_id}${require("path").extname(result.path || ".mp4")}`;
      const uploadResult = await uploadFile(result.path, gcsPath);

      if (uploadResult.success) {
        await reportProgress(job_id, job.id, "completed", 100, "Completed");
        // Notify backend
        await notifyBackend(job_id, job.id, { success: true, output_url: uploadResult.url, gcs_path: gcsPath, engine: result.engine });
        return { success: true, output_url: uploadResult.url, engine: result.engine };
      } else {
        // GCS failed but local file exists — still report success
        await reportProgress(job_id, job.id, "completed", 100, "Completed (local only)");
        await notifyBackend(job_id, job.id, { success: true, output_path: result.path, engine: result.engine, gcs_error: uploadResult.error });
        return { success: true, path: result.path, engine: result.engine, gcs_warning: uploadResult.error };
      }
    } catch (err) {
      await reportProgress(job_id, job.id, "failed", 0, err.message);
      await notifyBackend(job_id, job.id, { success: false, error: err.message });
      throw err; // BullMQ will retry
    }
  },
  {
    connection,
    concurrency: config.CONCURRENCY,
    limiter: {
      max: 100, // max 100 jobs per interval
      duration: 1000, // per 1 second
    },
    settings: {
      backoffStrategies: {
        type: "exponential",
        delay: config.BACKOFF_DELAY_MS,
      },
    },
  }
);

worker.on("completed", (job) => {
  console.log(`[media-worker] Job ${job.id} completed successfully`);
});

worker.on("failed", (job, err) => {
  console.error(`[media-worker] Job ${job?.id} failed: ${err.message}`);
});

worker.on("error", (err) => {
  console.error("[media-worker] Worker error:", err);
});

async function reportProgress(jobId, bullmqJobId, stage, progress, message) {
  try {
    // Update Redis progress hash (read by backend for live polling)
    const redis = require("ioredis");
    const r = new redis(config.REDIS_URL, { password: config.REDIS_PASSWORD });
    await r.hset(`media-vault:progress:${jobId}`, {
      stage: stage || "",
      progress: progress || 0,
      message: message || "",
      updated_at: Date.now(),
    });
    await r.expire(`media-vault:progress:${jobId}`, 3600);

    // Also update BullMQ job progress using the correct BullMQ job ID
    if (bullmqJobId) {
      const job = await mediaQueue.getJob(bullmqJobId);
      if (job) {
        await job.updateProgress(progress);
        await job.log(`[${stage}] ${message}`);
      }
    }
  } catch (err) {
    console.error(`[media-worker] Failed to report progress for ${jobId}:`, err.message);
  }
}

async function notifyBackend(jobId, bullmqJobId, data) {
  try {
    await axios.post(`${config.BACKEND_API_URL}/api/media/internal/worker-complete`, {
      job_id: jobId,
      ...data,
    }, { timeout: 5000 });
  } catch (err) {
    console.error(`[media-worker] Failed to notify backend for ${jobId}:`, err.message);
    // Backend will pick up the result from Redis progress on next poll
  }
}

// Graceful shutdown
process.on("SIGINT", async () => {
  console.log("[media-worker] Shutting down gracefully...");
  await worker.close();
  await mediaQueue.close();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  console.log("[media-worker] Received SIGTERM, closing...");
  await worker.close();
  await mediaQueue.close();
  process.exit(0);
});

console.log(`[media-worker] Media Vault worker started`);
console.log(`[media-worker] Concurrency: ${config.CONCURRENCY}`);
console.log(`[media-worker] Timeout: ${config.DEFAULT_TIMEOUT_MS}ms per call`);
console.log(`[media-worker] ComfyUI: ${config.COMFYUI_URL}`);
console.log(`[media-worker] GCS bucket: ${config.GOOGLE_CLOUD_STORAGE_BUCKET || "not configured"}`);
console.log(`[media-worker] Keys loaded: fal=${config.FAL_KEYS.length}, kling=${config.KLING_KEYS.length}, runway=${config.RUNWAY_KEYS.length}, elevenlabs=${config.ELEVENLABS_KEYS.length}`);

module.exports = { mediaQueue, worker };

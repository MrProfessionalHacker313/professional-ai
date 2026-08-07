/**
 * Video Processor - Kling 1.6 / Runway Gen-3 / fal.ai video
 * Failover chain: Kling → Runway → fal.ai video
 * Multi-key rotation. Max 10s per call.
 */

const axios = require("axios");
const config = require("../config");
const { KeyRotator } = require("../utils/keyRotator");
const { uploadFile } = require("../utils/gcsUploader");

const klingRotator = new KeyRotator(config.KLING_KEYS);
const runwayRotator = new KeyRotator(config.RUNWAY_KEYS);
const falRotator = new KeyRotator(config.FAL_KEYS);

function buildKlingHeaders(key) {
  return { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
}

function buildRunwayHeaders(key) {
  return { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
}

function buildFalHeaders(key) {
  return { Authorization: `Key ${key}`, "Content-Type": "application/json" };
}

async function callWithTimeout(fn, ms = config.DEFAULT_TIMEOUT_MS) {
  return Promise.race([
    fn(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

async function pollKlingTask(client, taskId, key) {
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const resp = await callWithTimeout(() =>
      client.get(`${config.KLING_API_URL}/v1/videos/text2video/${taskId}`, {
        headers: buildKlingHeaders(key),
        timeout: config.DEFAULT_TIMEOUT_MS,
      })
    );
    if (resp.status === 429) {
      klingRotator.markRateLimited(key);
      throw new Error("kling_rate_limited");
    }
    const data = resp.data?.data || {};
    if (data.task_status === "succeed") return data.task_result?.videos?.[0]?.url;
    if (data.task_status === "failed") throw new Error("kling_task_failed");
  }
  throw new Error("kling_timeout");
}

async function generateWithKling(prompt, duration, width, height, outputPath) {
  const key = klingRotator.next();
  if (!key) throw new Error("no_kling_keys");

  const client = axios.create();
  const submitResp = await callWithTimeout(() =>
    client.post(`${config.KLING_API_URL}/v1/videos/text2video`, {
      model_name: "kling-v1",
      prompt,
      duration: String(duration),
      width,
      height,
      cfg_scale: 0.5,
    }, { headers: buildKlingHeaders(key), timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (submitResp.status !== 200) {
    if (submitResp.status === 429) klingRotator.markRateLimited(key);
    else klingRotator.markError(key);
    throw new Error(`kling_http_${submitResp.status}`);
  }

  const taskId = submitResp.data?.data?.task_id;
  if (!taskId) throw new Error("kling_no_task_id");

  const videoUrl = await pollKlingTask(client, taskId, key);
  if (!videoUrl) throw new Error("kling_no_video_url");

  const videoResp = await callWithTimeout(() =>
    axios.get(videoUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS })
  );

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  videoResp.data.pipe(writer);
  await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });

  klingRotator.markSuccess(key);
  return { success: true, path: outputPath, engine: "kling", duration };
}

async function pollRunwayTask(client, taskId, key) {
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 5000));
    const resp = await callWithTimeout(() =>
      client.get(`${config.RUNWAY_API_URL}/tasks/${taskId}`, {
        headers: buildRunwayHeaders(key),
        timeout: config.DEFAULT_TIMEOUT_MS,
      })
    );
    if (resp.status === 429) {
      runwayRotator.markRateLimited(key);
      throw new Error("runway_rate_limited");
    }
    const data = resp.data;
    if (data.status === "SUCCEEDED") return data.output?.[0];
    if (data.status === "FAILED") throw new Error("runway_task_failed");
  }
  throw new Error("runway_timeout");
}

async function generateWithRunway(prompt, duration, width, height, outputPath) {
  const key = runwayRotator.next();
  if (!key) throw new Error("no_runway_keys");

  const client = axios.create();
  const submitResp = await callWithTimeout(() =>
    client.post(`${config.RUNWAY_API_URL}/text_to_video`, {
      prompt,
      duration,
      ratio: `${width}:${height}`,
    }, { headers: buildRunwayHeaders(key), timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (submitResp.status !== 200) {
    if (submitResp.status === 429) runwayRotator.markRateLimited(key);
    else runwayRotator.markError(key);
    throw new Error(`runway_http_${submitResp.status}`);
  }

  const taskId = submitResp.data?.id;
  if (!taskId) throw new Error("runway_no_task_id");

  const videoUrl = await pollRunwayTask(client, taskId, key);
  if (!videoUrl) throw new Error("runway_no_video_url");

  const videoResp = await callWithTimeout(() =>
    axios.get(videoUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS })
  );

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  videoResp.data.pipe(writer);
  await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });

  runwayRotator.markSuccess(key);
  return { success: true, path: outputPath, engine: "runway", duration };
}

async function generateWithFalVideo(prompt, duration, width, height, outputPath) {
  // fal.ai video endpoint (if available)
  const key = falRotator.next();
  if (!key) throw new Error("no_fal_keys");

  const resp = await callWithTimeout(() =>
    axios.post(`${config.FAL_API_URL}/fal-ai/veo2`, {
      prompt,
      duration,
      resolution: `${width}x${height}`,
    }, { headers: buildFalHeaders(key), timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (resp.status !== 200) {
    if (resp.status === 429) falRotator.markRateLimited(key);
    else falRotator.markError(key);
    throw new Error(`fal_video_http_${resp.status}`);
  }

  const videoUrl = resp.data?.video_url || resp.data?.url;
  if (!videoUrl) throw new Error("fal_no_video_url");

  const videoResp = await callWithTimeout(() =>
    axios.get(videoUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS })
  );

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  videoResp.data.pipe(writer);
  await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });

  falRotator.markSuccess(key);
  return { success: true, path: outputPath, engine: "fal_video", duration };
}

async function processVideo(job) {
  const { prompt, duration = 5, width = 1920, height = 1080, engine = "kling" } = job;
  const outputPath = job.output_path || `/tmp/media_${job.id}.mp4`;

  const providers =
    engine === "runway"
      ? [
          { name: "runway", fn: () => generateWithRunway(prompt, duration, width, height, outputPath) },
          { name: "kling", fn: () => generateWithKling(prompt, duration, width, height, outputPath) },
          { name: "fal_video", fn: () => generateWithFalVideo(prompt, duration, width, height, outputPath) },
        ]
      : [
          { name: "kling", fn: () => generateWithKling(prompt, duration, width, height, outputPath) },
          { name: "runway", fn: () => generateWithRunway(prompt, duration, width, height, outputPath) },
          { name: "fal_video", fn: () => generateWithFalVideo(prompt, duration, width, height, outputPath) },
        ];

  const errors = [];
  for (const provider of providers) {
    try {
      const result = await provider.fn();
      return { ...result, provider: provider.name };
    } catch (err) {
      errors.push(`${provider.name}: ${err.message}`);
      await updateProgress(job.id, `Video provider ${provider.name} failed, trying next...`);
    }
  }

  throw new Error(`all_video_providers_failed: ${errors.join("; ")}`);
}

async function updateProgress(jobId, stage, progress) {
  const redis = require("ioredis");
  const r = new redis(config.REDIS_URL, { password: config.REDIS_PASSWORD });
  await r.hset(`media-vault:progress:${jobId}`, {
    stage: stage || "",
    progress: progress || 0,
    updated_at: Date.now(),
  });
  await r.expire(`media-vault:progress:${jobId}`, 3600);
}

module.exports = {
  processVideo,
  updateProgress,
  getKlingStatus: () => klingRotator.getStatus(),
  getRunwayStatus: () => runwayRotator.getStatus(),
  getFalStatus: () => falRotator.getStatus(),
};

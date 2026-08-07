/**
 * Image Processor - fal.ai (SDXL + Flux) + Replicate backup
 * Multi-key rotation with automatic failover.
 * Max 10s per external call → failover to next provider.
 */

const axios = require("axios");
const config = require("../config");
const { KeyRotator } = require("../utils/keyRotator");
const { uploadFile } = require("../utils/gcsUploader");

const falRotator = new KeyRotator(config.FAL_KEYS);
const replicateRotator = new KeyRotator(config.REPLICATE_KEYS);

function buildFalHeaders(key) {
  return { Authorization: `Key ${key}`, "Content-Type": "application/json" };
}

function buildReplicateHeaders(key) {
  return { Authorization: `Token ${key}`, "Content-Type": "application/json" };
}

async function callWithTimeout(fn, ms = config.DEFAULT_TIMEOUT_MS) {
  return Promise.race([
    fn(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

async function generateWithFal(prompt, width, height, model, outputPath) {
  const key = falRotator.next();
  if (!key) throw new Error("no_fal_keys");

  const endpoint = model === "flux" ? "fal-ai/flux/dev" : "fal-ai/stable-diffusion-xl";
  const submitUrl = `${config.FAL_API_URL}/${endpoint}`;

  const submitResp = await callWithTimeout(() =>
    axios.post(submitUrl, {
      prompt,
      image_size: { width, height },
      num_inference_steps: 30,
      guidance_scale: 7.5,
    }, { headers: buildFalHeaders(key), timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (submitResp.status !== 200) {
    if (submitResp.status === 429) {
      const retryAfter = submitResp.headers?.["retry-after"] || 60;
      falRotator.markRateLimited(key, retryAfter * 1000);
    } else {
      falRotator.markError(key);
    }
    throw new Error(`fal_http_${submitResp.status}`);
  }

  const imageUrl = submitResp.data?.images?.[0]?.url || submitResp.data?.url;
  if (!imageUrl) throw new Error("fal_no_image_url");

  const imgResp = await callWithTimeout(() =>
    axios.get(imageUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS })
  );

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  imgResp.data.pipe(writer);

  await new Promise((resolve, reject) => {
    writer.on("finish", resolve);
    writer.on("error", reject);
  });

  falRotator.markSuccess(key);
  return { success: true, path: outputPath, engine: "fal_ai", model, width, height };
}

async function generateWithReplicate(prompt, width, height, model, outputPath) {
  const key = replicateRotator.next();
  if (!key) throw new Error("no_replicate_keys");

  const version = model === "flux" ? "black-forest-labs/flux-dev" : "stability-ai/sdxl";
  const startResp = await callWithTimeout(() =>
    axios.post(`${config.REPLICATE_API_URL}/predictions`, {
      version,
      input: { prompt, width, height, num_inference_steps: 30, guidance_scale: 7.5 },
    }, { headers: buildReplicateHeaders(key), timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (startResp.status !== 201 && startResp.status !== 200) {
    if (startResp.status === 429) replicateRotator.markRateLimited(key);
    else replicateRotator.markError(key);
    throw new Error(`replicate_http_${startResp.status}`);
  }

  const prediction = startResp.data;
  let result = prediction;

  // Poll for completion (max 60 * 2s = 120s, but individual calls timeout at 10s)
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const pollResp = await callWithTimeout(() =>
      axios.get(`${config.REPLICATE_API_URL}/predictions/${prediction.id}`, {
        headers: buildReplicateHeaders(key),
        timeout: config.DEFAULT_TIMEOUT_MS,
      })
    );
    if (pollResp.status === 429) {
      replicateRotator.markRateLimited(key);
      throw new Error("replicate_rate_limited");
    }
    result = pollResp.data;
    if (result.status === "succeeded") break;
    if (result.status === "failed") throw new Error("replicate_failed");
  }

  const outputUrl = Array.isArray(result.output) ? result.output[0] : result.output;
  if (!outputUrl) throw new Error("replicate_no_output");

  const imgResp = await callWithTimeout(() =>
    axios.get(outputUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS })
  );

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  imgResp.data.pipe(writer);
  await new Promise((resolve, reject) => {
    writer.on("finish", resolve);
    writer.on("error", reject);
  });

  replicateRotator.markSuccess(key);
  return { success: true, path: outputPath, engine: "replicate", model, width, height };
}

async function processImage(job) {
  const { prompt, width = 1024, height = 1024, model = "flux" } = job;
  const outputPath = job.output_path || `/tmp/media_${job.id}.png`;

  const providers = [
    { name: "fal_ai", fn: () => generateWithFal(prompt, width, height, model, outputPath) },
    { name: "replicate", fn: () => generateWithReplicate(prompt, width, height, model, outputPath) },
  ];

  const errors = [];
  for (const provider of providers) {
    try {
      const result = await provider.fn();
      return { ...result, provider: provider.name };
    } catch (err) {
      errors.push(`${provider.name}: ${err.message}`);
      await updateProgress(job.id, `Image provider ${provider.name} failed, trying next...`);
    }
  }

  throw new Error(`all_image_providers_failed: ${errors.join("; ")}`);
}

async function updateProgress(jobId, stage, progress) {
  // Publish to Redis for real-time frontend updates
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
  processImage,
  updateProgress,
  getFalStatus: () => falRotator.getStatus(),
  getReplicateStatus: () => replicateRotator.getStatus(),
};

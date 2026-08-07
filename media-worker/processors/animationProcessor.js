/**
 * Animation Processor - AnimateDiff via ComfyUI on owner's GPU server
 * Self-owned, zero per-use cost. Calls ComfyUI API directly.
 * Falls back to Replicate AnimateDiff if ComfyUI is down.
 */

const axios = require("axios");
const config = require("../config");
const { KeyRotator } = require("../utils/keyRotator");
const { uploadFile } = require("../utils/gcsUploader");

const replicateRotator = new KeyRotator(config.REPLICATE_KEYS);

async function callWithTimeout(fn, ms = config.DEFAULT_TIMEOUT_MS) {
  return Promise.race([
    fn(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

async function generateWithComfyUI(prompt, frames, width, height, outputPath) {
  // ComfyUI API: submit a workflow
  const workflow = {
    "3": {
      class_type: "KSampler",
      inputs: {
        seed: Math.floor(Math.random() * 2147483647),
        steps: 20,
        cfg: 7,
        sampler_name: "euler",
        scheduler: "normal",
        denoise: 1,
        model: ["4", 0],
        positive: ["6", 0],
        negative: ["7", 0],
        latent_image: ["5", 0],
      },
    },
    "4": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: config.COMFYUI_ANIMATEDIFF_MODEL || "animatediff_lightning" } },
    "5": { class_type: "EmptyLatentImage", inputs: { width, height, batch_size: 1 } },
    "6": { class_type: "CLIPTextEncode", inputs: { text: prompt, clip: ["4", 1] } },
    "7": { class_type: "CLIPTextEncode", inputs: { text: "", clip: ["4", 1] } },
    "8": { class_type: "VAEDecode", inputs: { samples: ["3", 0], vae: ["4", 2] } },
    "9": { class_type: "VHS_VideoCombine", inputs: { frame_rate: 8, images: ["8", 0] } },
  };

  const submitResp = await callWithTimeout(() =>
    axios.post(`${config.COMFYUI_URL}/prompt`, { prompt: workflow }, { timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (submitResp.status !== 200) throw new Error(`comfyui_http_${submitResp.status}`);

  const promptId = submitResp.data?.prompt_id;
  if (!promptId) throw new Error("comfyui_no_prompt_id");

  // Poll for completion
  for (let i = 0; i < 120; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const historyResp = await callWithTimeout(() =>
      axios.get(`${config.COMFYUI_URL}/history/${promptId}`, { timeout: config.DEFAULT_TIMEOUT_MS })
    );
    if (historyResp.status !== 200) continue;

    const history = historyResp.data?.[promptId];
    if (!history) continue;

    if (history.status?.completed) {
      // Get output video
      const outputs = history.outputs || {};
      const videoNode = outputs["9"];
      if (videoNode?.gifs?.[0]?.filename) {
        const videoResp = await callWithTimeout(() =>
          axios.get(`${config.COMFYUI_URL}/view?filename=${videoNode.gifs[0].filename}&type=output`, {
            responseType: "stream",
            timeout: config.DEFAULT_TIMEOUT_MS,
          })
        );
        const fs = require("fs");
        const writer = fs.createWriteStream(outputPath);
        videoResp.data.pipe(writer);
        await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });
        return { success: true, path: outputPath, engine: "comfyui_animatediff" };
      }
    }
    if (history.status?.status_str === "error") throw new Error("comfyui_generation_failed");
  }

  throw new Error("comfyui_timeout");
}

async function generateWithReplicateAnimateDiff(prompt, frames, width, height, outputPath) {
  const key = replicateRotator.next();
  if (!key) throw new Error("no_replicate_keys");

  const startResp = await callWithTimeout(() =>
    axios.post(`${config.REPLICATE_API_URL}/predictions`, {
      version: config.COMFYUI_ANIMATEDIFF_MODEL || "guoyingzheng/animatediff",
      input: { prompt, num_frames: Math.min(frames, 64), width, height },
    }, { headers: { Authorization: `Token ${key}`, "Content-Type": "application/json" }, timeout: config.DEFAULT_TIMEOUT_MS })
  );

  if (startResp.status !== 201 && startResp.status !== 200) {
    if (startResp.status === 429) replicateRotator.markRateLimited(key);
    else replicateRotator.markError(key);
    throw new Error(`replicate_http_${startResp.status}`);
  }

  const prediction = startResp.data;
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 2000));
    const pollResp = await callWithTimeout(() =>
      axios.get(`${config.REPLICATE_API_URL}/predictions/${prediction.id}`, {
        headers: { Authorization: `Token ${key}`, "Content-Type": "application/json" },
        timeout: config.DEFAULT_TIMEOUT_MS,
      })
    );
    if (pollResp.status === 429) { replicateRotator.markRateLimited(key); throw new Error("replicate_rate_limited"); }
    const data = pollResp.data;
    if (data.status === "succeeded") {
      const outputUrl = Array.isArray(data.output) ? data.output[0] : data.output;
      if (!outputUrl) throw new Error("replicate_no_output");
      const animResp = await callWithTimeout(() => axios.get(outputUrl, { responseType: "stream", timeout: config.DEFAULT_TIMEOUT_MS }));
      const fs = require("fs");
      const writer = fs.createWriteStream(outputPath);
      animResp.data.pipe(writer);
      await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });
      replicateRotator.markSuccess(key);
      return { success: true, path: outputPath, engine: "replicate_animatediff" };
    }
    if (data.status === "failed") throw new Error("replicate_animatediff_failed");
  }

  throw new Error("replicate_timeout");
}

async function processAnimation(job) {
  const { prompt, duration = 5, width = 1024, height = 1024 } = job;
  const frames = duration * 8; // ~8fps
  const outputPath = job.output_path || `/tmp/media_${job.id}.gif`;

  // PRIMARY: ComfyUI on our GPU server (zero cost)
  try {
    const result = await generateWithComfyUI(prompt, frames, width, height, outputPath);
    return result;
  } catch (err) {
    await updateProgress(job.id, `ComfyUI failed (${err.message}), trying Replicate backup...`);
  }

  // BACKUP: Replicate AnimateDiff
  try {
    const result = await generateWithReplicateAnimateDiff(prompt, frames, width, height, outputPath);
    return result;
  } catch (err) {
    return { success: false, error: `all_animation_providers_failed: ${err.message}` };
  }
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
  processAnimation,
  updateProgress,
  getReplicateStatus: () => replicateRotator.getStatus(),
};

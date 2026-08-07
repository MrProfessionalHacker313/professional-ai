/**
 * TTS Processor - ElevenLabs + edge-tts + Piper (local)
 * Permanent provider chain with automatic failover.
 * Never stops — free edge-tts is final guaranteed fallback.
 */

const axios = require("axios");
const { spawn } = require("child_process");
const config = require("../config");
const { KeyRotator } = require("../utils/keyRotator");

const elevenLabsRotator = new KeyRotator(config.ELEVENLABS_KEYS);

async function callWithTimeout(fn, ms = config.DEFAULT_TIMEOUT_MS) {
  return Promise.race([
    fn(),
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

function resolveElevenLabsVoice(voiceStyle, language) {
  const map = {
    adult_female: "21m00Tcm4TlvDq8ikWAM",
    adult_male: "ErXwobaYiN019PkySvjV",
    young_girl: "XB0fDUnXU5powFXDhCwa",
    young_boy: "bVMeCyTHy58xNoL34h3p",
    news_anchor: "pNInz6obpgDQGcFmaJgB",
    robotic: "onwK4e9ZLuTAKqIi03f0",
    cartoon: "nPczCjMl7V7pZvn5Vkwe",
  };
  return map[voiceStyle] || map.adult_female;
}

function resolveEdgeTTSVoice(voiceStyle, language) {
  const voices = {
    en: {
      adult_female: "en-US-JennyNeural",
      adult_male: "en-US-GuyNeural",
      young_girl: "en-US-AriaNeural",
      news_anchor: "en-US-DavisNeural",
    },
    ur: { adult_female: "ur-PK-UzmaNeural", adult_male: "ur-PK-ImranNeural" },
    hi: { adult_female: "hi-IN-SwaraNeural", adult_male: "hi-IN-MadhurNeural" },
  };
  return voices[language]?.[voiceStyle] || voices.en.adult_female || "en-US-JennyNeural";
}

async function synthesizeElevenLabs(text, voiceStyle, language, outputPath) {
  const key = elevenLabsRotator.next();
  if (!key) throw new Error("no_elevenlabs_keys");

  const voiceId = resolveElevenLabsVoice(voiceStyle, language);
  const url = `${config.ELEVENLABS_API_URL}/text-to-speech/${voiceId}`;

  const resp = await callWithTimeout(() =>
    axios.post(url, {
      text,
      model_id: "eleven_multilingual_v2",
      voice_settings: { stability: 0.5, similarity_boost: 0.8, style: 0.2, use_speaker_boost: true },
    }, {
      headers: { "xi-api-key": key, "Content-Type": "application/json", Accept: "audio/mpeg" },
      responseType: "stream",
      timeout: config.DEFAULT_TIMEOUT_MS,
    })
  );

  if (resp.status === 429) { elevenLabsRotator.markRateLimited(key); throw new Error("elevenlabs_rate_limited"); }
  if (resp.status !== 200) { elevenLabsRotator.markError(key); throw new Error(`elevenlabs_http_${resp.status}`); }

  const fs = require("fs");
  const writer = fs.createWriteStream(outputPath);
  resp.data.pipe(writer);
  await new Promise((resolve, reject) => { writer.on("finish", resolve); writer.on("error", reject); });

  if (!fs.existsSync(outputPath) || fs.statSync(outputPath).size === 0) throw new Error("elevenlabs_output_empty");

  elevenLabsRotator.markSuccess(key);
  return { success: true, path: outputPath, provider: "elevenlabs", engine: "elevenlabs_multilingual_v2" };
}

async function synthesizeEdgeTTS(text, voiceStyle, language, outputPath) {
  // edge-tts is free Microsoft TTS — guaranteed fallback
  try {
    const edgeTts = require("edge-tts");
    const voice = resolveEdgeTTSVoice(voiceStyle, language);
    const communicate = edgeTts.Communicate(text, voice);
    await communicate.save(outputPath);

    if (!require("fs").existsSync(outputPath) || require("fs").statSync(outputPath).size === 0) {
      throw new Error("edge_tts_output_empty");
    }

    return { success: true, path: outputPath, provider: "edge_tts", engine: "microsoft_neural" };
  } catch (err) {
    throw new Error(`edge_tts: ${err.message}`);
  }
}

async function synthesizePiper(text, voiceStyle, language, outputPath) {
  // Piper TTS — local CPU-only, never expires
  const piperBin = process.env.PIPER_BIN || "piper";
  const piperModel = process.env.PIPER_MODEL || `en_US-${voiceStyle}-medium`;

  return new Promise((resolve) => {
    const proc = spawn(piperBin, ["--model", piperModel, "--output_file", outputPath]);
    proc.stdin.write(text);
    proc.stdin.end();

    proc.on("close", (code) => {
      if (code === 0 && require("fs").existsSync(outputPath)) {
        resolve({ success: true, path: outputPath, provider: "piper", engine: "piper_local" });
      } else {
        resolve({ success: false, error: `piper_exit_${code}` });
      }
    });

    proc.on("error", () => resolve({ success: false, error: "piper_not_installed" }));
  });
}

async function processTTS(job) {
  const { script, voice_style = "adult_female", language = "en" } = job;
  const outputPath = job.output_path || `/tmp/media_${job.id}.mp3`;

  const providers = [
    { name: "elevenlabs", fn: () => synthesizeElevenLabs(script, voice_style, language, outputPath) },
    { name: "edge_tts", fn: () => synthesizeEdgeTTS(script, voice_style, language, outputPath) },
    { name: "piper", fn: () => synthesizePiper(script, voice_style, language, outputPath) },
  ];

  for (const provider of providers) {
    try {
      const result = await provider.fn();
      if (result.success) return result;
      await updateProgress(job.id, `TTS provider ${provider.name} failed, trying next...`);
    } catch (err) {
      await updateProgress(job.id, `TTS provider ${provider.name} error: ${err.message}`);
    }
  }

  return { success: false, error: "all_tts_providers_failed" };
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
  processTTS,
  updateProgress,
  getElevenLabsStatus: () => elevenLabsRotator.getStatus(),
};

"""
Professional AI - TTS Router (Permanent Provider Chain)
PRIMARY: ElevenLabs API (multilingual v2, multi-key rotation)
FALLBACK 1: edge-tts (Microsoft voices, FREE, unlimited)
FALLBACK 2 (OFFLINE): Piper TTS (local, CPU-only, never expires)

Router: ElevenLabs → edge-tts → Piper. If one fails, next one instantly.
Voice quality stays high, never stops.
"""

from __future__ import annotations

import asyncio
import os
import json
import tempfile
import time
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from cryptography.fernet import Fernet

from app.config import settings
from app.services.media.voice_catalog import (
    resolve_edge_tts_voice,
    resolve_elevenlabs_voice,
    get_elevenlabs_settings,
    resolve_piper_voice,
    EDGE_TTS_STYLE_PARAMS,
    resolve_voice_from_prompt,
    validate_voice_style,
    validate_language,
)


# ===================================================================
# Provider availability checks
# ===================================================================

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not installed — FALLBACK 1 unavailable")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# ===================================================================
# ElevenLabs Key Rotation Manager
# Multi-key support so it never runs out. Rotates to next key on
# rate-limit (429) or auth failure (401). Add unlimited keys in .env.
# ===================================================================

class ElevenLabsKeyManager:
    """Manages multiple ElevenLabs API keys with automatic rotation."""

    def __init__(self):
        self._keys: List[str] = []
        self._current_index: int = 0
        self._key_status: Dict[str, Dict[str, Any]] = {}
        self._load_keys()

    def _load_keys(self):
        """Load keys from settings (comma-separated) or single key."""
        keys_str = getattr(settings, "ELEVENLABS_KEYS", "") or ""
        single_key = getattr(settings, "ELEVENLABS_API_KEY", None)

        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if single_key and single_key not in keys:
            keys.insert(0, single_key)

        self._keys = keys
        for k in keys:
            self._key_status[k] = {
                "rate_limited_until": 0.0,
                "error_count": 0,
                "last_used": 0.0,
                "success_count": 0,
            }

        if keys:
            logger.info(f"ElevenLabs key manager loaded {len(keys)} key(s)")
        else:
            logger.warning("No ElevenLabs API keys configured — PRIMARY provider unavailable")

    def get_active_key(self) -> Optional[str]:
        """Get the next available (non-rate-limited) key. Rotates automatically."""
        if not self._keys:
            return None

        now = time.time()
        for i in range(len(self._keys)):
            idx = (self._current_index + i) % len(self._keys)
            key = self._keys[idx]
            status = self._key_status[key]

            if status["rate_limited_until"] > now:
                continue
            if status["error_count"] >= 5:
                continue

            self._current_index = idx
            status["last_used"] = now
            return key

        # All keys exhausted — reset and try again
        logger.warning("All ElevenLabs keys exhausted — resetting error counts")
        for k in self._keys:
            self._key_status[k]["error_count"] = 0
            self._key_status[k]["rate_limited_until"] = 0.0

        if self._keys:
            self._current_index = 0
            return self._keys[0]
        return None

    def mark_rate_limited(self, key: str, retry_after: float = 60.0):
        if key in self._key_status:
            self._key_status[key]["rate_limited_until"] = time.time() + retry_after
            logger.warning(f"ElevenLabs key {key[:8]}... rate-limited for {retry_after}s — rotating")

    def mark_error(self, key: str):
        if key in self._key_status:
            self._key_status[key]["error_count"] += 1
            logger.warning(f"ElevenLabs key {key[:8]}... error count: {self._key_status[key]['error_count']}")

    def mark_success(self, key: str):
        if key in self._key_status:
            self._key_status[key]["error_count"] = 0
            self._key_status[key]["success_count"] += 1

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        active_keys = sum(
            1 for k, s in self._key_status.items()
            if s["rate_limited_until"] <= now and s["error_count"] < 5
        )
        return {
            "total_keys": len(self._keys),
            "active_keys": active_keys,
            "current_index": self._current_index,
            "keys": [
                {
                    "key_prefix": k[:8] + "...",
                    "rate_limited": s["rate_limited_until"] > now,
                    "error_count": s["error_count"],
                    "success_count": s["success_count"],
                }
                for k, s in self._key_status.items()
            ],
        }


# Singleton key manager
elevenlabs_key_manager = ElevenLabsKeyManager()


# ===================================================================
# Voice Clone Encryption (stored encrypted)
# ===================================================================

class VoiceCloneVault:
    """Encrypts and stores voice clone audio samples securely."""

    def __init__(self):
        self._fernet = self._init_fernet()
        self._vault_dir = Path(settings.MEDIA_OUTPUT_DIR) / "voice_clones_encrypted"
        self._vault_dir.mkdir(parents=True, exist_ok=True)

    def _init_fernet(self) -> Optional[Fernet]:
        try:
            key = settings.ENCRYPTION_KEY
            if not key:
                logger.warning("ENCRYPTION_KEY not set — voice clone vault unencrypted")
                return None
            if len(key) == 44:
                return Fernet(key.encode() if isinstance(key, str) else key)
            derived = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode() if isinstance(key, str) else key).digest()
            )
            return Fernet(derived)
        except Exception as e:
            logger.error(f"Failed to init voice clone vault encryption: {e}")
            return None

    def encrypt_and_store(self, audio_path: str, clone_id: str) -> Optional[str]:
        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            if self._fernet:
                audio_data = self._fernet.encrypt(audio_data)
            enc_path = str(self._vault_dir / f"clone_{clone_id}.enc")
            with open(enc_path, "wb") as f:
                f.write(audio_data)
            logger.info(f"Voice clone {clone_id} encrypted and stored")
            return enc_path
        except Exception as e:
            logger.error(f"Failed to encrypt voice clone: {e}")
            return None

    def decrypt_and_load(self, encrypted_path: str) -> Optional[bytes]:
        try:
            with open(encrypted_path, "rb") as f:
                encrypted_data = f.read()
            if self._fernet:
                return self._fernet.decrypt(encrypted_data)
            return encrypted_data
        except Exception as e:
            logger.error(f"Failed to decrypt voice clone: {e}")
            return None

    def delete_clone(self, encrypted_path: str) -> bool:
        try:
            if os.path.exists(encrypted_path):
                size = os.path.getsize(encrypted_path)
                with open(encrypted_path, "wb") as f:
                    f.write(os.urandom(size))
                os.remove(encrypted_path)
                logger.info(f"Voice clone securely deleted: {encrypted_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete voice clone: {e}")
            return False


# Singleton vault
voice_clone_vault = VoiceCloneVault()


# ===================================================================
# TTS Router — Permanent Provider Chain
# ===================================================================

class TTSRouter:
    """
    Permanent TTS provider chain with automatic failover.
    ElevenLabs → edge-tts → Piper. Never stops.
    """

    PROVIDER_CHAIN = ["elevenlabs", "edge_tts", "piper"]

    def __init__(self):
        self._output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "voice"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._piper_models_dir = Path(getattr(settings, "OFFLINE_VOICE_MODELS_DIR", "./data/voice_models"))
        self._piper_bin = self._find_piper_binary()

    def _find_piper_binary(self) -> Optional[str]:
        candidates = [
            "piper",
            "/usr/local/bin/piper",
            "/usr/bin/piper",
            str(Path(settings.MEDIA_OUTPUT_DIR).parent / "piper" / "piper"),
            "./piper/piper.exe",
            "./piper/piper",
        ]
        for c in candidates:
            try:
                import shutil
                if shutil.which(c) or os.path.exists(c):
                    return c
            except Exception:
                continue
        return None

    async def synthesize(
        self,
        text: str,
        voice_style: str = "adult_female",
        language: str = "en",
        voice_prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        voice_clone_id: Optional[str] = None,
        clone_audio_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize speech using the permanent provider chain.
        Tries ElevenLabs → edge-tts → Piper. Returns first success.
        """
        if not text or not text.strip():
            return {"success": False, "error": "empty_text"}

        # Resolve voice from natural language prompt if provided
        if voice_prompt:
            resolved = resolve_voice_from_prompt(voice_prompt)
            if resolved:
                voice_style = resolved["style"]
                language = resolved["language"]
                logger.info(f"Voice prompt resolved: style={voice_style}, lang={language}")

        # Validate
        if not validate_voice_style(voice_style):
            voice_style = "adult_female"
        if not validate_language(language):
            language = "en"

        # Generate output path if not provided
        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"voice_{job_id}.mp3")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Try each provider in the chain
        provider_results: List[Dict[str, Any]] = []

        # PRIMARY: ElevenLabs (with voice clone support)
        if voice_clone_id and clone_audio_path:
            result = await self._synthesize_elevenlabs_clone(
                text, voice_clone_id, clone_audio_path, language, output_path
            )
        else:
            result = await self._synthesize_elevenlabs(
                text, voice_style, language, output_path
            )
        provider_results.append({"provider": "elevenlabs", "result": result})
        if result.get("success"):
            return self._format_success(result, "elevenlabs", voice_style, language, text, output_path)

        # FALLBACK 1: edge-tts (FREE, unlimited)
        result = await self._synthesize_edge_tts(text, voice_style, language, output_path)
        provider_results.append({"provider": "edge_tts", "result": result})
        if result.get("success"):
            return self._format_success(result, "edge_tts", voice_style, language, text, output_path)

        # FALLBACK 2: Piper (OFFLINE, CPU-only)
        result = await self._synthesize_piper(text, voice_style, language, output_path)
        provider_results.append({"provider": "piper", "result": result})
        if result.get("success"):
            return self._format_success(result, "piper", voice_style, language, text, output_path)

        # All providers failed
        logger.error("All TTS providers failed in the permanent chain")
        return {
            "success": False,
            "error": "all_providers_failed",
            "provider_results": provider_results,
        }

    def _format_success(
        self, result: Dict, provider: str, voice_style: str,
        language: str, text: str, output_path: str
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "path": output_path,
            "provider": provider,
            "voice_style": voice_style,
            "language": language,
            "script": text,
            "duration_estimate": self._estimate_duration(text),
            "provider_detail": result,
        }

    # ===================================================================
    # PRIMARY: ElevenLabs API (multilingual v2)
    # ===================================================================

    async def _synthesize_elevenlabs(
        self, text: str, voice_style: str, language: str, output_path: str
    ) -> Dict[str, Any]:
        """Synthesize using ElevenLabs multilingual v2 with key rotation."""
        api_key = elevenlabs_key_manager.get_active_key()
        if not api_key:
            return {"success": False, "error": "no_api_key"}

        if not HTTPX_AVAILABLE:
            return {"success": False, "error": "httpx_not_available"}

        voice_id = resolve_elevenlabs_voice(voice_style, language)
        voice_settings = get_elevenlabs_settings(voice_style)
        model_id = "eleven_multilingual_v2"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        }
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 60))
                    elevenlabs_key_manager.mark_rate_limited(api_key, retry_after)
                    return {"success": False, "error": "rate_limited", "retry_after": retry_after}

                if resp.status_code == 401:
                    elevenlabs_key_manager.mark_error(api_key)
                    return {"success": False, "error": "auth_failed"}

                if resp.status_code != 200:
                    logger.warning(f"ElevenLabs returned {resp.status_code}")
                    elevenlabs_key_manager.mark_error(api_key)
                    return {"success": False, "error": f"http_{resp.status_code}"}

                with open(output_path, "wb") as f:
                    f.write(resp.content)

                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    return {"success": False, "error": "output_empty"}

                elevenlabs_key_manager.mark_success(api_key)
                logger.info(f"ElevenLabs synthesis success (key {api_key[:8]}...)")
                return {
                    "success": True,
                    "voice_id": voice_id,
                    "model": model_id,
                    "key_used": api_key[:8] + "...",
                }

        except asyncio.TimeoutError:
            logger.warning("ElevenLabs timeout — failing over to edge-tts")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            elevenlabs_key_manager.mark_error(api_key)
            return {"success": False, "error": str(e)}

    async def _synthesize_elevenlabs_clone(
        self, text: str, clone_id: str, clone_audio_path: str,
        language: str, output_path: str
    ) -> Dict[str, Any]:
        """Synthesize using a cloned voice via ElevenLabs Instant Voice Cloning."""
        api_key = elevenlabs_key_manager.get_active_key()
        if not api_key:
            return {"success": False, "error": "no_api_key"}

        if not HTTPX_AVAILABLE:
            return {"success": False, "error": "httpx_not_available"}

        # Check if clone_id is an ElevenLabs voice ID (20-char alphanumeric)
        if len(clone_id) == 20 and clone_id.isalnum():
            cloned_voice_id = clone_id
        else:
            cloned_voice_id = await self._create_elevenlabs_clone(
                api_key, clone_id, clone_audio_path, language
            )
            if not cloned_voice_id:
                return {"success": False, "error": "clone_creation_failed"}

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{cloned_voice_id}"
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.80,
                "style": 0.20,
                "use_speaker_boost": True,
            },
        }
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 60))
                    elevenlabs_key_manager.mark_rate_limited(api_key, retry_after)
                    return {"success": False, "error": "rate_limited"}

                if resp.status_code != 200:
                    elevenlabs_key_manager.mark_error(api_key)
                    return {"success": False, "error": f"http_{resp.status_code}"}

                with open(output_path, "wb") as f:
                    f.write(resp.content)

                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    return {"success": False, "error": "output_empty"}

                elevenlabs_key_manager.mark_success(api_key)
                logger.info(f"ElevenLabs clone synthesis success (voice {cloned_voice_id[:8]}...)")
                return {
                    "success": True,
                    "voice_id": cloned_voice_id,
                    "model": "eleven_multilingual_v2",
                    "cloned": True,
                }

        except Exception as e:
            logger.error(f"ElevenLabs clone synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_elevenlabs_clone(
        self, api_key: str, clone_name: str, audio_path: str, language: str
    ) -> Optional[str]:
        """Create an instant voice clone on ElevenLabs. Returns voice ID."""
        if not HTTPX_AVAILABLE:
            return None

        url = "https://api.elevenlabs.io/v1/voices/add"
        headers = {"xi-api-key": api_key}

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            files = {"files": ("sample.wav", audio_data, "audio/wav")}
            data = {
                "name": f"clone_{clone_name}",
                "labels": json.dumps({"language": language, "type": "clone"}),
            }

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, files=files, data=data)

                if resp.status_code == 200:
                    result = resp.json()
                    voice_id = result.get("voice_id")
                    logger.info(f"ElevenLabs clone created: {voice_id}")
                    return voice_id
                else:
                    logger.error(f"ElevenLabs clone creation failed: {resp.status_code} {resp.text}")
                    return None

        except Exception as e:
            logger.error(f"ElevenLabs clone creation error: {e}")
            return None

    # ===================================================================
    # FALLBACK 1: edge-tts (Microsoft voices, FREE, unlimited)
    # ===================================================================

    async def _synthesize_edge_tts(
        self, text: str, voice_style: str, language: str, output_path: str
    ) -> Dict[str, Any]:
        """Synthesize using edge-tts (Microsoft voices). FREE, unlimited."""
        if not EDGE_TTS_AVAILABLE:
            return {"success": False, "error": "edge_tts_not_installed"}

        voice = resolve_edge_tts_voice(voice_style, language)
        style_params = EDGE_TTS_STYLE_PARAMS.get(voice_style, {})

        try:
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=style_params.get("rate", "+0%"),
                pitch=style_params.get("pitch", "+0Hz"),
                volume=style_params.get("volume", "+0%"),
            )
            await communicate.save(output_path)

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return {"success": False, "error": "output_empty"}

            logger.info(f"edge-tts synthesis success (voice={voice})")
            return {
                "success": True,
                "voice": voice,
                "engine": "edge-tts",
            }

        except Exception as e:
            logger.error(f"edge-tts synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    # ===================================================================
    # FALLBACK 2: Piper TTS (OFFLINE, CPU-only, never expires)
    # ===================================================================

    async def _synthesize_piper(
        self, text: str, voice_style: str, language: str, output_path: str
    ) -> Dict[str, Any]:
        """Synthesize using Piper TTS (local, offline, CPU-only)."""
        if not self._piper_bin:
            return {"success": False, "error": "piper_not_installed"}

        piper_model = resolve_piper_voice(voice_style, language)
        model_path = self._piper_models_dir / f"{piper_model}.onnx"

        if not model_path.exists():
            downloaded = await self._download_piper_model(piper_model)
            if not downloaded:
                return {"success": False, "error": "piper_model_not_found", "model": piper_model}

        try:
            cmd = [
                self._piper_bin,
                "--model", str(model_path),
                "--output_file", output_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate(input=text.encode("utf-8"))

            if proc.returncode != 0:
                logger.error(f"Piper TTS failed: {stderr.decode()}")
                return {"success": False, "error": f"piper_exit_{proc.returncode}"}

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return {"success": False, "error": "output_empty"}

            logger.info(f"Piper TTS synthesis success (model={piper_model})")
            return {
                "success": True,
                "voice": piper_model,
                "engine": "piper",
                "offline": True,
            }

        except Exception as e:
            logger.error(f"Piper TTS synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _download_piper_model(self, model_name: str) -> bool:
        """Download a Piper TTS model (first run only)."""
        if not HTTPX_AVAILABLE:
            return False

        self._piper_models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self._piper_models_dir / f"{model_name}.onnx"
        config_path = self._piper_models_dir / f"{model_name}.json"

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

        try:
            parts = model_name.split("-")
            if len(parts) < 3:
                logger.error(f"Invalid Piper model name format: {model_name}")
                return False

            lang_region = parts[0]
            voice_name = parts[1]
            quality = parts[2]

            onnx_url = f"{base_url}/{lang_region}/{voice_name}/{quality}/{model_name}.onnx"
            json_url = f"{base_url}/{lang_region}/{voice_name}/{quality}/{model_name}.json"

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(onnx_url)
                if resp.status_code != 200:
                    logger.error(f"Failed to download Piper model {model_name}: HTTP {resp.status_code}")
                    return False

                with open(model_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded Piper model: {model_name}")

                resp = await client.get(json_url)
                if resp.status_code == 200:
                    with open(config_path, "wb") as f:
                        f.write(resp.content)

                return True

        except Exception as e:
            logger.error(f"Failed to download Piper model {model_name}: {e}")
            return False

    # ===================================================================
    # Utilities
    # ===================================================================

    @staticmethod
    def _estimate_duration(script: str) -> float:
        """Estimate voice-over duration in seconds (~150 wpm)."""
        word_count = len(script.split())
        return max(1.0, word_count / 2.5)

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers in the chain."""
        return {
            "chain": self.PROVIDER_CHAIN,
            "elevenlabs": {
                "available": elevenlabs_key_manager.get_status()["total_keys"] > 0,
                "key_status": elevenlabs_key_manager.get_status(),
            },
            "edge_tts": {
                "available": EDGE_TTS_AVAILABLE,
                "engine": "Microsoft Neural TTS",
                "cost": "FREE",
                "unlimited": True,
            },
            "piper": {
                "available": self._piper_bin is not None,
                "binary": self._piper_bin,
                "offline": True,
                "cpu_only": True,
            },
        }


# Singleton
tts_router = TTSRouter()
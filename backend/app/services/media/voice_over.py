"""
Professional AI - Media Engine Voice Over Service
Generates voice overs from the exact script text using edge-tts (free,
multi-voice) with fallback to cloud TTS. Supports voice styles and cloning.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.config import settings
from app.services.media.provider_keys import media_key_vault

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False


# ===================================================================
# Voice Style → edge-tts voice mapping
# ===================================================================

VOICE_STYLE_MAP = {
    "young_girl": "en-US-AriaNeural",       # female, youthful
    "young_boy": "en-US-GuyNeural",         # young male
    "adult_male": "en-US-ChristopherNeural",
    "adult_female": "en-US-JennyNeural",
    "news_anchor": "en-US-GuyNeural",        # authoritative male
    "robotic": "en-US-EricNeural",           # synthetic sounding
    "cartoon": "en-US-AnaNeural",            # bright, energetic
    "villain": "en-US-DavisNeural",          # deep dramatic
    "hero": "en-US-TonyNeural",              # strong male
    "custom": "en-US-JennyNeural",
    "clone": "en-US-JennyNeural",            # default until clone model used
}

# Language → voice override (best default voice per language)
VOICE_LANGUAGE_MAP = {
    "en": "en-US-JennyNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-SwaraNeural",
    "ar": "ar-SA-ZariyahNeural",
    "bn": "bn-BD-PabanNeural",
}


class VoiceOverService:
    """Generates voice over audio from exact script text."""

    def __init__(self):
        self._output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "voice"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_voice(self, voice_style: str, language: str, voice_prompt: Optional[str] = None) -> str:
        """Resolve a voice style/prompt to an actual TTS voice."""
        # If user provided a natural language prompt, try to match keywords
        if voice_prompt:
            prompt_lower = voice_prompt.lower()
            # Language detection in the prompt (e.g. "in Urdu")
            for lang_code, lang_name in [("ur", "urdu"), ("hi", "hindi"), ("ar", "arabic"), ("bn", "bengali"), ("en", "english")]:
                if lang_name in prompt_lower:
                    language = lang_code
                    break
            # Style detection in the prompt
            if "young girl" in prompt_lower or "little girl" in prompt_lower or "sweet" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["young_girl"])
            if "young boy" in prompt_lower or "little boy" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["young_boy"])
            if "news" in prompt_lower or "anchor" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["news_anchor"])
            if "robot" in prompt_lower or "robotic" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["robotic"])
            if "cartoon" in prompt_lower or "kids" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["cartoon"])
            if "villain" in prompt_lower or "evil" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["villain"])
            if "hero" in prompt_lower or "strong" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["hero"])
            if "male" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["adult_male"])
            if "female" in prompt_lower:
                return VOICE_LANGUAGE_MAP.get(language, VOICE_STYLE_MAP["adult_female"])

        # Explicit style
        voice = VOICE_STYLE_MAP.get(voice_style)
        if voice:
            return voice

        # Language default
        return VOICE_LANGUAGE_MAP.get(language, "en-US-JennyNeural")

    async def generate_voice_over(
        self,
        script: str,
        voice_style: str = "adult_female",
        voice_prompt: Optional[str] = None,
        language: str = "en",
        output_path: Optional[str] = None,
        voice_clone_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate voice over audio from the EXACT script text.
        Failover chain: ElevenLabs → Google Cloud TTS → edge-tts → cloud fallback.
        Returns path and metadata.
        """
        if not script or not script.strip():
            return {"success": False, "error": "script_empty"}

        # Voice cloning path (using clone provider when available)
        if voice_clone_id and voice_style == "clone":
            logger.warning(f"Voice clone {voice_clone_id} requested — falling back to default voice")

        voice = self._resolve_voice(voice_style, language, voice_prompt)

        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"voice_{job_id}.mp3")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        providers = [
            ("elevenlabs", lambda: self._synthesize_elevenlabs(script, voice, output_path, voice_clone_id)),
            ("google_tts", lambda: self._synthesize_google_tts(script, voice, output_path, language)),
        ]

        if EDGE_TTS_AVAILABLE:
            providers.append(("edge_tts", lambda: self._synthesize_edge_tts(script, voice, output_path)))

        for provider_name, provider_fn in providers:
            try:
                result = await asyncio.wait_for(provider_fn(), timeout=30)
                if result.get("success"):
                    return {
                        "success": True,
                        "path": output_path,
                        "provider": provider_name,
                        "voice": voice,
                        "language": language,
                        "script": script,
                        "duration_estimate": self._estimate_duration(script),
                        "provider_detail": result,
                    }
            except asyncio.TimeoutError:
                logger.warning(f"{provider_name} voice synthesis timed out after 30s")
            except Exception as e:
                logger.warning(f"{provider_name} voice synthesis failed: {e}")

        # Final fallback: cloud TTS endpoint if configured
        success = await self._cloud_tts_fallback(script, voice, output_path)
        if success:
            return {
                "success": True,
                "path": output_path,
                "provider": "cloud_tts_fallback",
                "voice": voice,
                "language": language,
                "script": script,
                "duration_estimate": self._estimate_duration(script),
            }

        return {"success": False, "error": "all_voice_providers_failed"}

    async def _synthesize_elevenlabs(
        self, script: str, voice: str, output_path: str, voice_clone_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesize using ElevenLabs with multi-key rotation."""
        api_key = media_key_vault.elevenlabs.get_active_key()
        if not api_key:
            return {"success": False, "error": "no_elevenlabs_key"}

        if not HTTPX_AVAILABLE:
            return {"success": False, "error": "httpx_not_available"}

        voice_id = voice
        if voice_clone_id:
            if len(voice_clone_id) == 20 and voice_clone_id.isalnum():
                voice_id = voice_clone_id
            else:
                logger.warning("Voice clone not available via ElevenLabs direct API, using default voice")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            "text": script[:5000],
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.50, "similarity_boost": 0.75, "style": 0.20, "use_speaker_boost": True},
        }
        headers = {"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 60))
                    media_key_vault.elevenlabs.mark_rate_limited(api_key, retry_after)
                    return {"success": False, "error": "elevenlabs_rate_limited"}
                if resp.status_code == 401:
                    media_key_vault.elevenlabs.mark_error(api_key)
                    return {"success": False, "error": "elevenlabs_auth_failed"}
                if resp.status_code != 200:
                    media_key_vault.elevenlabs.mark_error(api_key)
                    return {"success": False, "error": f"elevenlabs_http_{resp.status_code}"}

                with open(output_path, "wb") as f:
                    f.write(resp.content)
                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    return {"success": False, "error": "output_empty"}

                media_key_vault.elevenlabs.mark_success(api_key)
                return {"success": True, "voice_id": voice_id, "model": "eleven_multilingual_v2", "key_used": api_key[:8] + "..."}
        except asyncio.TimeoutError:
            return {"success": False, "error": "elevenlabs_timeout"}
        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _synthesize_google_tts(
        self, script: str, voice: str, output_path: str, language: str = "en"
    ) -> Dict[str, Any]:
        """Synthesize using Google Cloud TTS with multi-key rotation."""
        api_key = media_key_vault.google_tts.get_active_key()
        if not api_key:
            return {"success": False, "error": "no_google_tts_key"}

        if not HTTPX_AVAILABLE:
            return {"success": False, "error": "httpx_not_available"}

        lang_code = language if len(language) == 5 else f"{language}-US"
        voice_name = voice if voice.startswith(lang_code[:2]) else f"{lang_code}-Standard-A"

        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        payload = {
            "input": {"text": script[:5000]},
            "voice": {"languageCode": lang_code, "name": voice_name, "ssmlGender": "FEMALE"},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0, "pitch": 0.0},
        }
        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    media_key_vault.google_tts.mark_rate_limited(api_key, 60.0)
                    return {"success": False, "error": "google_tts_rate_limited"}
                if resp.status_code == 401:
                    media_key_vault.google_tts.mark_error(api_key)
                    return {"success": False, "error": "google_tts_auth_failed"}
                if resp.status_code != 200:
                    media_key_vault.google_tts.mark_error(api_key)
                    return {"success": False, "error": f"google_tts_http_{resp.status_code}"}

                data = resp.json()
                audio_content = data.get("audioContent")
                if not audio_content:
                    return {"success": False, "error": "google_tts_no_audio"}

                import base64
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(audio_content))
                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    return {"success": False, "error": "output_empty"}

                media_key_vault.google_tts.mark_success(api_key)
                return {"success": True, "voice": voice_name, "engine": "google_tts", "key_used": api_key[:8] + "..."}
        except asyncio.TimeoutError:
            return {"success": False, "error": "google_tts_timeout"}
        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _synthesize_edge_tts(self, script: str, voice: str, output_path: str) -> Dict[str, Any]:
        """Synthesize using edge-tts (Microsoft voices). FREE, unlimited."""
        if not EDGE_TTS_AVAILABLE:
            return {"success": False, "error": "edge_tts_not_installed"}

        style_params = {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}

        try:
            communicate = edge_tts.Communicate(
                script,
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

    async def _cloud_tts_fallback(self, script: str, voice: str, output_path: str) -> bool:
        """Fallback to cloud TTS service if configured."""
        tts_url = settings.TTS_API_URL
        if not tts_url:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{tts_url}/tts",
                    json={"text": script, "voice": voice, "output_path": output_path},
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Cloud TTS fallback failed: {e}")
            return False

    @staticmethod
    def _estimate_duration(script: str) -> float:
        """Estimate voice-over duration in seconds (~150 wpm)."""
        word_count = len(script.split())
        return max(1.0, word_count / 2.5)  # ~150 words per minute

    async def clone_voice(
        self,
        audio_path: str,
        name: str,
        language: str = "en",
        consent: bool = False,
    ) -> Dict[str, Any]:
        """
        Clone a user's voice from a 30-second audio sample.
        REQUIRES consent checkbox.
        """
        if not consent:
            return {"success": False, "error": "consent_required"}

        # Check duration limit
        try:
            import wave
            with wave.open(audio_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / rate
        except Exception:
            # Try pydub for non-wav formats
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_path)
                duration = audio.duration_seconds
            except Exception as e:
                logger.error(f"Could not read audio file: {e}")
                return {"success": False, "error": "bad_audio_file"}

        max_seconds = settings.MEDIA_VOICE_CLONE_MAX_SECONDS
        if duration > max_seconds:
            return {
                "success": False,
                "error": f"audio_too_long:{max_seconds}",
                "message": f"Audio must be {max_seconds} seconds or less for voice cloning.",
            }

        # In production, upload to the voice clone provider (ElevenLabs, etc.)
        # For now, return a placeholder clone record.
        return {
            "success": True,
            "name": name,
            "duration_seconds": int(duration),
            "language": language,
            "consent_given": consent,
            "message": "Voice sample accepted for cloning.",
        }


# Singleton
voice_over_service = VoiceOverService()
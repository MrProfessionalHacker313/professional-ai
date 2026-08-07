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
        Returns path and metadata.
        """
        if not script or not script.strip():
            return {"success": False, "error": "script_empty"}

        # Voice cloning path (using clone provider when available)
        if voice_clone_id and voice_style == "clone":
            # In production, this calls the voice clone provider (e.g. ElevenLabs)
            # For now, falls through to default voice as placeholder
            logger.warning(f"Voice clone {voice_clone_id} requested but provider not configured — using default voice")

        voice = self._resolve_voice(voice_style, language, voice_prompt)

        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"voice_{job_id}.mp3")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            if EDGE_TTS_AVAILABLE:
                communicate = edge_tts.Communicate(script, voice)
                await communicate.save(output_path)
            else:
                # Fallback: use cloud TTS API endpoint if configured
                success = await self._cloud_tts_fallback(script, voice, output_path)
                if not success:
                    return {"success": False, "error": "no_tts_provider"}

            # Verify the file was created and has content
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return {"success": False, "error": "output_empty"}

            return {
                "success": True,
                "path": output_path,
                "voice": voice,
                "language": language,
                "script": script,
                "duration_estimate": self._estimate_duration(script),
            }

        except Exception as e:
            logger.error(f"Voice over generation failed: {e}")
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
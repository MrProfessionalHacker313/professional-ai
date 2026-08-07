"""
Professional AI - Offline Voice Service (Vosk)
Provides speech recognition that works WITHOUT internet.
Supports Urdu, Hindi, English and 20+ other languages.
"""

import os
import json
import asyncio
import tempfile
import shutil
import wave
import io
import time
from typing import Optional, Dict, Any, List, BinaryIO
from pathlib import Path
from dataclasses import dataclass
from loguru import logger
from fastapi import HTTPException
import httpx

from app.config import settings


@dataclass
class VoiceModel:
    language: str
    language_code: str
    model_name: str
    model_path: str
    size_mb: int
    supported: bool = True


OFFLINE_VOICE_MODELS = [
    VoiceModel("English", "en", "vosk-model-small-en-us-0.15", "en-us", 40),
    VoiceModel("Urdu", "ur", "vosk-model-small-ur-0.1", "ur", 35),
    VoiceModel("Hindi", "hi", "vosk-model-small-hi-0.22", "hi", 45),
    VoiceModel("Arabic", "ar", "vosk-model-small-ar-0.1", "ar", 35),
    VoiceModel("Spanish", "es", "vosk-model-small-es-0.42", "es", 40),
    VoiceModel("French", "fr", "vosk-model-small-fr-0.42", "fr", 40),
    VoiceModel("German", "de", "vosk-model-small-de-0.15", "de", 40),
    VoiceModel("Russian", "ru", "vosk-model-small-ru-0.42", "ru", 40),
    VoiceModel("Chinese (Mandarin)", "zh", "vosk-model-small-cn-0.22", "cn", 45),
    VoiceModel("Portuguese", "pt", "vosk-model-small-pt-0.3", "pt", 40),
    VoiceModel("Japanese", "ja", "vosk-model-small-ja-0.22", "ja", 40),
    VoiceModel("Korean", "ko", "vosk-model-small-ko-0.22", "ko", 40),
    VoiceModel("Turkish", "tr", "vosk-model-small-tr-0.3", "tr", 35),
    VoiceModel("Vietnamese", "vi", "vosk-model-small-vi-0.4", "vi", 40),
    VoiceModel("Italian", "it", "vosk-model-small-it-0.22", "it", 40),
    VoiceModel("Dutch", "nl", "vosk-model-small-nl-0.22", "nl", 35),
    VoiceModel("Polish", "pl", "vosk-model-small-pl-0.22", "pl", 40),
    VoiceModel("Swedish", "sv", "vosk-model-small-sv-0.21", "sv", 35),
    VoiceModel("Ukrainian", "uk", "vosk-model-small-uk-0.22", "uk", 40),
    VoiceModel("Czech", "cs", "vosk-model-small-cs-0.4", "cs", 35),
]


class OfflineVoiceService:
    """
    Offline speech recognition using Vosk.
    Works completely without internet after model download.
    """

    def __init__(self, models_dir: Optional[str] = None):
        self._models_dir = Path(models_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "voice_models",
        ))
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_models: Dict[str, Any] = {}
        self._model_semaphore = asyncio.Semaphore(2)

    async def _load_model(self, language_code: str) -> Optional[Any]:
        """Load Vosk model for a language (lazy loading)."""
        if language_code in self._loaded_models:
            return self._loaded_models[language_code]

        model_info = next(
            (m for m in OFFLINE_VOICE_MODELS if m.language_code == language_code),
            OFFLINE_VOICE_MODELS[0],
        )

        model_path = self._models_dir / model_info.model_name
        if not model_path.exists():
            logger.warning(f"Vosk model not found: {model_path}")
            return None

        async with self._model_semaphore:
            try:
                from vosk import Model, KaldiRecognizer
                import wave as wave_module

                model = Model(str(model_path))
                self._loaded_models[language_code] = {
                    "model": model,
                    "info": model_info,
                }
                logger.info(f"Loaded Vosk model: {model_info.display_name}")
                return self._loaded_models[language_code]
            except ImportError:
                logger.error("Vosk not installed. Install with: pip install vosk")
                return None
            except Exception as e:
                logger.error(f"Failed to load Vosk model {language_code}: {e}")
                return None

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        sample_rate: int = 16000,
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using offline Vosk.
        Returns transcription with confidence scores.
        """
        start_time = time.time()

        # Validate language
        language_code = language.split("-")[0].lower()
        model_entry = await self._load_model(language_code)
        if not model_entry:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{language}' not supported offline. Available: {[m.language_code for m in OFFLINE_VOICE_MODELS]}",
            )

        try:
            import vosk
            import io
            import struct

            # Convert audio to WAV format if needed
            wav_data = await self._ensure_wav(audio_data, sample_rate)

            model = model_entry["model"]
            rec = vosk.KaldiRecognizer(model, sample_rate)
            rec.SetWords(True)
            rec.SetPartialWords(True)

            # Process audio
            rec.AcceptWaveform(wav_data)
            result_json = rec.FinalResult()
            result = json.loads(result_json)

            # Also get partial results for confidence
            partial_results = []
            if "result" in result:
                for word_info in result["result"]:
                    partial_results.append({
                        "word": word_info.get("word", ""),
                        "confidence": word_info.get("conf", 0.0),
                        "start": word_info.get("start", 0),
                        "end": word_info.get("end", 0),
                    })

            text = result.get("text", "").strip()
            confidence = result.get("text", "")
            avg_confidence = (
                sum(w.get("conf", 0) for w in partial_results) / len(partial_results)
                if partial_results else 0.0
            )

            execution_time = int((time.time() - start_time) * 1000)

            return {
                "text": text,
                "language": language_code,
                "confidence": round(avg_confidence, 3),
                "words": partial_results,
                "model": model_entry["info"].model_name,
                "provider": "vosk-offline",
                "offline": True,
                "execution_time_ms": execution_time,
            }

        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Vosk not installed. Run: pip install vosk soundfile numpy",
            )
        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    async def _ensure_wav(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Ensure audio is in WAV format (16kHz mono 16-bit)."""
        try:
            import numpy as np
            import soundfile as sf

            # Try to read as audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_data)
                tmp.flush()
                data, sr = sf.read(tmp.name, dtype="float32")

                # Resample if needed
                if sr != sample_rate:
                    try:
                        import resampy
                        data = resampy.resample(data, sr, sample_rate)
                    except ImportError:
                        logger.warning("resampy not installed, using original sample rate")

                # Convert to 16-bit PCM
                data_int16 = (data * 32767).astype(np.int16)

                # Write to WAV buffer
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(data_int16.tobytes())

                return wav_buffer.getvalue()

        except Exception:
            # If not audio data, return as-is
            return audio_data

    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages for offline transcription."""
        return [
            {
                "language": m.language,
                "code": m.language_code,
                "model": m.model_name,
                "size_mb": m.size_mb,
                "available": (self._models_dir / m.model_name).exists(),
            }
            for m in OFFLINE_VOICE_MODELS
        ]

    async def download_model(self, language_code: str) -> Dict[str, Any]:
        """Download a Vosk model for offline use."""
        model_info = next(
            (m for m in OFFLINE_VOICE_MODELS if m.language_code == language_code),
            None,
        )
        if not model_info:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{language_code}' not supported",
            )

        model_path = self._models_dir / model_info.model_name
        if model_path.exists():
            return {
                "success": True,
                "language": model_info.language,
                "status": "already_downloaded",
                "path": str(model_path),
            }

        # Download from Vosk model repository
        url = f"https://alphacephei.com/vosk/models/{model_info.model_name}.zip"
        logger.info(f"Downloading Vosk model: {url}")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                zip_path = self._models_dir / f"{model_info.model_name}.zip"
                with open(zip_path, "wb") as f:
                    f.write(response.content)

                # Extract
                import zipfile
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(self._models_dir)

                # Cleanup zip
                zip_path.unlink()

                return {
                    "success": True,
                    "language": model_info.language,
                    "status": "downloaded",
                    "path": str(model_path),
                    "size_mb": model_info.size_mb,
                }

        except Exception as e:
            logger.error(f"Failed to download Vosk model: {e}")
            return {
                "success": False,
                "language": model_info.language,
                "error": str(e),
            }

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of downloaded voice models."""
        downloaded = []
        for m in OFFLINE_VOICE_MODELS:
            model_path = self._models_dir / m.model_name
            downloaded.append({
                "language": m.language,
                "code": m.language_code,
                "available": model_path.exists(),
                "size_mb": m.size_mb,
            })

        return {
            "models_dir": str(self._models_dir),
            "total_supported": len(OFFLINE_VOICE_MODELS),
            "downloaded": sum(1 for d in downloaded if d["available"]),
            "models": downloaded,
        }


offline_voice_service = OfflineVoiceService()

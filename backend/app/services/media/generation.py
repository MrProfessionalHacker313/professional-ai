"""
Professional AI - Media Engine Generation Service
Engines: fal.ai (Stable Diffusion XL + Flux for images), Kling/Runway (video),
AnimateDiff via cloud GPU (animations). All heavy GPU work happens on the
cloud server — user devices never jam.

Multi-key rotation: every provider rotates through comma-separated keys
on rate-limit. Owner adds keys in .env — no code change needed.
"""

from __future__ import annotations

import asyncio
import os
import json
import time
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.config import settings
from app.services.media.provider_keys import media_key_vault


DEFAULT_TIMEOUT = 10.0  # 10 seconds max per external call


class MediaGenerationService:
    """
    Routes generation requests to the appropriate engine:
    - Images/Posters: fal.ai (SDXL + Flux)
    - Videos: Kling / Runway
    - Animations: AnimateDiff via cloud GPU
    """

    def __init__(self):
        self._output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "generated"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ===================================================================
    # Image Generation (fal.ai - SDXL + Flux)
    # ===================================================================

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        model: str = "flux",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an image using multi-key rotation with automatic failover.
        Provider chain: fal.ai → Replicate.
        10-second timeout per call. Falls back to placeholder if all fail.
        """
        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"img_{job_id}.png")

        # Try fal.ai with key rotation
        fal_keys = getattr(settings, "FAL_KEYS", "") or ""
        if fal_keys or settings.FAL_AI_API_KEY:
            providers = [
                ("fal_ai", lambda k: self._fal_generate_image(prompt, negative_prompt, width, height, model, output_path, k)),
                ("replicate", lambda k: self._replicate_generate_image(prompt, negative_prompt, width, height, model, output_path, k)),
            ]
            for provider_name, provider_fn in providers:
                keys = media_key_vault.fal._keys if provider_name == "fal_ai" else media_key_vault.replicate._keys
                rotator = media_key_vault.fal if provider_name == "fal_ai" else media_key_vault.replicate
                for _ in keys:
                    key = rotator.get_active_key()
                    if not key:
                        break
                    try:
                        result = await asyncio.wait_for(provider_fn(key), timeout=DEFAULT_TIMEOUT)
                        if result.get("success"):
                            return result
                    except asyncio.TimeoutError:
                        logger.warning(f"{provider_name} image generation timed out after {DEFAULT_TIMEOUT}s")
                        rotator.mark_error(key)
                    except Exception as e:
                        logger.warning(f"{provider_name} image generation failed: {e}")
                        rotator.mark_error(key)

        # Fallback: generate a placeholder image with Pillow
        return await self._placeholder_image(prompt, width, height, output_path)

    async def _fal_generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
        model: str,
        output_path: str,
        api_key: str,
    ) -> Dict[str, Any]:
        """Call fal.ai API for image generation with provided key."""
        model_endpoint = "fal-ai/flux/dev" if model == "flux" else "fal-ai/stable-diffusion-xl"

        payload = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.FAL_AI_API_URL}/{model_endpoint}",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 429:
                media_key_vault.fal.mark_rate_limited(api_key, float(resp.headers.get("retry-after", 60)))
                return {"success": False, "error": f"fal_rate_limited_{resp.status_code}"}
            if resp.status_code == 401:
                media_key_vault.fal.mark_error(api_key)
                return {"success": False, "error": "fal_auth_failed"}
            if resp.status_code != 200:
                media_key_vault.fal.mark_error(api_key)
                return {"success": False, "error": f"fal_http_{resp.status_code}"}

            data = resp.json()
            image_url = data.get("images", [{}])[0].get("url") or data.get("url")
            if not image_url:
                return {"success": False, "error": "no_image_url"}

            img_resp = await client.get(image_url)
            if img_resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(img_resp.content)
                media_key_vault.fal.mark_success(api_key)
                return {
                    "success": True,
                    "path": output_path,
                    "engine": "fal_ai",
                    "model": model,
                    "width": width,
                    "height": height,
                }

        return {"success": False, "error": "download_failed"}

    async def _replicate_generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
        model: str,
        output_path: str,
        api_key: str,
    ) -> Dict[str, Any]:
        """Call Replicate API for image generation with provided key."""
        version = "black-forest-labs/flux-dev" if model == "flux" else "stability-ai/sdxl"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            start_resp = await client.post(
                f"{settings.REPLICATE_API_URL}/predictions",
                json={"version": version, "input": {"prompt": prompt, "width": width, "height": height, "num_inference_steps": 30}},
                headers=headers,
            )
            if start_resp.status_code == 429:
                media_key_vault.replicate.mark_rate_limited(api_key, float(start_resp.headers.get("retry-after", 60)))
                return {"success": False, "error": "replicate_rate_limited"}
            if start_resp.status_code != 201 and start_resp.status_code != 200:
                media_key_vault.replicate.mark_error(api_key)
                return {"success": False, "error": f"replicate_http_{start_resp.status_code}"}

            prediction = start_resp.json()
            for _ in range(60):
                await asyncio.sleep(2)
                poll_resp = await client.get(
                    f"{settings.REPLICATE_API_URL}/predictions/{prediction['id']}",
                    headers=headers,
                )
                if poll_resp.status_code == 429:
                    media_key_vault.replicate.mark_rate_limited(api_key)
                    return {"success": False, "error": "replicate_rate_limited"}
                data = poll_resp.json()
                if data.get("status") == "succeeded":
                    output_url = data.get("output")
                    if isinstance(output_url, list):
                        output_url = output_url[0]
                    if output_url:
                        img_resp = await client.get(output_url)
                        if img_resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(img_resp.content)
                            media_key_vault.replicate.mark_success(api_key)
                            return {"success": True, "path": output_path, "engine": "replicate", "model": model}
                elif data.get("status") == "failed":
                    media_key_vault.replicate.mark_error(api_key)
                    return {"success": False, "error": "replicate_failed"}

        return {"success": False, "error": "replicate_timeout"}

    async def _placeholder_image(
        self,
        prompt: str,
        width: int,
        height: int,
        output_path: str,
    ) -> Dict[str, Any]:
        """Generate a placeholder image when no API key is configured."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            def _create():
                img = Image.new("RGB", (width, height), (15, 23, 42))
                draw = ImageDraw.Draw(img)
                # Draw a simple gradient-like background
                for y in range(height):
                    color = (
                        int(15 + (y / height) * 40),
                        int(23 + (y / height) * 30),
                        int(42 + (y / height) * 60),
                    )
                    draw.line([(0, y), (width, y)], fill=color)

                # Draw prompt text
                text = prompt[:100] + ("..." if len(prompt) > 100 else "")
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except Exception:
                    font = ImageFont.load_default()

                # Center text
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                x = (width - text_w) // 2
                y = (height - text_h) // 2
                draw.text((x, y), text, fill=(255, 255, 255), font=font)

                img.save(output_path, "PNG")

            await asyncio.to_thread(_create)
            return {
                "success": True,
                "path": output_path,
                "engine": "placeholder",
                "width": width,
                "height": height,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ===================================================================
    # Video Generation (Kling / Runway)
    # ===================================================================

    async def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 5,
        width: int = 1920,
        height: int = 1080,
        engine: str = "kling",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a video clip using multi-key rotation with automatic failover.
        Provider chain: Kling → Runway → fal.ai video.
        10-second timeout per call. Falls back to placeholder if all fail.
        """
        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"vid_{job_id}.mp4")

        providers = [
            ("kling", lambda: self._kling_generate_video(prompt, duration_seconds, width, height, output_path)),
            ("runway", lambda: self._runway_generate_video(prompt, duration_seconds, width, height, output_path)),
            ("fal_video", lambda: self._fal_generate_video(prompt, duration_seconds, width, height, output_path)),
        ]

        if engine == "runway":
            providers = [
                ("runway", lambda: self._runway_generate_video(prompt, duration_seconds, width, height, output_path)),
                ("kling", lambda: self._kling_generate_video(prompt, duration_seconds, width, height, output_path)),
                ("fal_video", lambda: self._fal_generate_video(prompt, duration_seconds, width, height, output_path)),
            ]

        for provider_name, provider_fn in providers:
            rotator = (
                media_key_vault.kling if provider_name == "kling"
                else media_key_vault.runway if provider_name == "runway"
                else media_key_vault.fal
            )
            for _ in range(rotator.total_keys or 1):
                key = rotator.get_active_key()
                if not key and provider_name != "kling":  # kling/runway always have at least one key attempt
                    break
                try:
                    result = await asyncio.wait_for(provider_fn(key) if key else provider_fn(), timeout=DEFAULT_TIMEOUT)
                    if result.get("success"):
                        result["provider"] = provider_name
                        return result
                except asyncio.TimeoutError:
                    logger.warning(f"{provider_name} video timed out after {DEFAULT_TIMEOUT}s")
                    if key:
                        rotator.mark_error(key)
                except Exception as e:
                    logger.warning(f"{provider_name} video generation failed: {e}")
                    if key:
                        rotator.mark_error(key)

        return await self._placeholder_video(prompt, duration_seconds, width, height, output_path)

    async def _kling_generate_video(
        self,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        output_path: str,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Call Kling AI API for video generation with multi-key support."""
        api_key = api_key or settings.KLING_API_KEY
        if not api_key:
            return {"success": False, "error": "no_kling_key"}

        payload = {
            "model_name": "kling-v1",
            "prompt": prompt,
            "duration": str(duration_seconds),
            "width": width,
            "height": height,
            "cfg_scale": 0.5,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.KLING_API_URL}/v1/videos/text2video",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("retry-after", 60))
                media_key_vault.kling.mark_rate_limited(api_key, retry_after)
                return {"success": False, "error": f"kling_rate_limited_{resp.status_code}"}
            if resp.status_code == 401:
                media_key_vault.kling.mark_error(api_key)
                return {"success": False, "error": "kling_auth_failed"}
            if resp.status_code != 200:
                media_key_vault.kling.mark_error(api_key)
                return {"success": False, "error": f"kling_http_{resp.status_code}"}

            data = resp.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return {"success": False, "error": "no_task_id"}

            for attempt in range(60):
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"{settings.KLING_API_URL}/v1/videos/text2video/{task_id}",
                    headers=headers,
                )
                if status_resp.status_code == 429:
                    media_key_vault.kling.mark_rate_limited(api_key)
                    return {"success": False, "error": "kling_rate_limited"}
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    task_status = status_data.get("data", {}).get("task_status")
                    if task_status == "succeed":
                        video_url = status_data.get("data", {}).get("task_result", {}).get("videos", [{}])[0].get("url")
                        if video_url:
                            video_resp = await client.get(video_url, timeout=DEFAULT_TIMEOUT)
                            if video_resp.status_code == 200:
                                with open(output_path, "wb") as f:
                                    f.write(video_resp.content)
                                media_key_vault.kling.mark_success(api_key)
                                return {"success": True, "path": output_path, "engine": "kling", "duration": duration_seconds}
                    elif task_status == "failed":
                        media_key_vault.kling.mark_error(api_key)
                        return {"success": False, "error": "kling_task_failed"}

        return {"success": False, "error": "kling_timeout"}

    async def _runway_generate_video(
        self,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        output_path: str,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Call Runway API for video generation with multi-key support."""
        api_key = api_key or settings.RUNWAY_API_KEY
        if not api_key:
            return {"success": False, "error": "no_runway_key"}

        payload = {"prompt": prompt, "duration": duration_seconds, "ratio": f"{width}:{height}"}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.RUNWAY_API_URL}/text_to_video",
                json=payload,
                headers=headers,
            )
            if resp.status_code == 429:
                media_key_vault.runway.mark_rate_limited(api_key, float(resp.headers.get("retry-after", 60)))
                return {"success": False, "error": f"runway_rate_limited_{resp.status_code}"}
            if resp.status_code == 401:
                media_key_vault.runway.mark_error(api_key)
                return {"success": False, "error": "runway_auth_failed"}
            if resp.status_code != 200:
                media_key_vault.runway.mark_error(api_key)
                return {"success": False, "error": f"runway_http_{resp.status_code}"}

            data = resp.json()
            task_id = data.get("id")
            if not task_id:
                return {"success": False, "error": "no_task_id"}

            for attempt in range(60):
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"{settings.RUNWAY_API_URL}/tasks/{task_id}",
                    headers=headers,
                )
                if status_resp.status_code == 429:
                    media_key_vault.runway.mark_rate_limited(api_key)
                    return {"success": False, "error": "runway_rate_limited"}
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if status_data.get("status") == "SUCCEEDED":
                        video_url = status_data.get("output", [""])[0]
                        if video_url:
                            video_resp = await client.get(video_url, timeout=DEFAULT_TIMEOUT)
                            if video_resp.status_code == 200:
                                with open(output_path, "wb") as f:
                                    f.write(video_resp.content)
                                media_key_vault.runway.mark_success(api_key)
                                return {"success": True, "path": output_path, "engine": "runway", "duration": duration_seconds}
                    elif status_data.get("status") == "FAILED":
                        media_key_vault.runway.mark_error(api_key)
                        return {"success": False, "error": "runway_task_failed"}

        return {"success": False, "error": "runway_timeout"}

    async def _fal_generate_video(
        self,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        output_path: str,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Call fal.ai video endpoint as last-resort video provider."""
        api_key = api_key or getattr(settings, "FAL_AI_API_KEY", None)
        if not api_key:
            return {"success": False, "error": "no_fal_key"}

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            headers = {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}
            resp = await client.post(
                f"{settings.FAL_AI_API_URL}/fal-ai/veo2",
                json={"prompt": prompt, "duration": duration_seconds, "resolution": f"{width}x{height}"},
                headers=headers,
            )
            if resp.status_code == 429:
                media_key_vault.fal.mark_rate_limited(api_key, float(resp.headers.get("retry-after", 60)))
                return {"success": False, "error": f"fal_video_rate_limited_{resp.status_code}"}
            if resp.status_code != 200:
                media_key_vault.fal.mark_error(api_key)
                return {"success": False, "error": f"fal_video_http_{resp.status_code}"}

            data = resp.json()
            video_url = data.get("video_url") or data.get("url")
            if not video_url:
                return {"success": False, "error": "fal_no_video_url"}

            video_resp = await client.get(video_url, timeout=DEFAULT_TIMEOUT)
            if video_resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(video_resp.content)
                media_key_vault.fal.mark_success(api_key)
                return {"success": True, "path": output_path, "engine": "fal_video", "duration": duration_seconds}

        return {"success": False, "error": "fal_video_download_failed"}

    async def _placeholder_video(
        self,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        output_path: str,
    ) -> Dict[str, Any]:
        """Generate a placeholder video when no API key is configured."""
        try:
            # Use ffmpeg if available to create a simple video
            import subprocess

            # Create a simple color video with text using ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x0f172a:s={width}x{height}:d={duration_seconds}",
                "-vf", f"drawtext=text='{prompt[:50]}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                return {
                    "success": True,
                    "path": output_path,
                    "engine": "placeholder_ffmpeg",
                    "duration": duration_seconds,
                }
        except Exception as e:
            logger.warning(f"ffmpeg placeholder failed: {e}")

        return {"success": False, "error": "no_video_engine"}

    # ===================================================================
    # Animation Generation (AnimateDiff via cloud GPU)
    # ===================================================================

    async def generate_animation(
        self,
        prompt: str,
        duration_seconds: int = 5,
        width: int = 1024,
        height: int = 1024,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an animation using multi-key rotation with automatic failover.
        Provider chain: ComfyUI (owner's GPU server, zero cost) → Replicate AnimateDiff.
        10-second timeout per call. ComfyUI is primary (permanent, self-owned).
        """
        if output_path is None:
            job_id = os.urandom(8).hex()
            output_path = str(self._output_dir / f"anim_{job_id}.gif")

        # PRIMARY: ComfyUI on owner's GPU server (zero per-use cost, permanent)
        comfyui_url = getattr(settings, "COMFYUI_URL", None)
        if comfyui_url:
            try:
                result = await asyncio.wait_for(
                    self._comfyui_generate_animation(prompt, duration_seconds, width, height, output_path),
                    timeout=DEFAULT_TIMEOUT * 12  # Allow longer for ComfyUI generation
                )
                if result.get("success"):
                    return result
            except asyncio.TimeoutError:
                logger.warning(f"ComfyUI animation timed out after {DEFAULT_TIMEOUT * 12}s")
            except Exception as e:
                logger.warning(f"ComfyUI animation failed: {e}")

        # BACKUP: Replicate AnimateDiff
        replicate_keys = getattr(settings, "REPLICATE_KEYS", "") or getattr(settings, "ANIMATEDIFF_API_KEY", None)
        if replicate_keys:
            rotator = media_key_vault.replicate
            for _ in range(rotator.total_keys or 1):
                key = rotator.get_active_key()
                if not key:
                    break
                try:
                    result = await asyncio.wait_for(
                        self._replicate_generate_animation(prompt, duration_seconds, width, height, output_path, key),
                        timeout=DEFAULT_TIMEOUT
                    )
                    if result.get("success"):
                        result["provider"] = "replicate"
                        return result
                except asyncio.TimeoutError:
                    logger.warning("Replicate AnimateDiff timed out")
                    rotator.mark_error(key)
                except Exception as e:
                    logger.warning(f"Replicate AnimateDiff failed: {e}")
                    rotator.mark_error(key)

        # Fallback: simple animated GIF
        return await self._placeholder_animation(prompt, duration_seconds, width, height, output_path)

    async def _comfyui_generate_animation(
        self, prompt: str, duration_seconds: int, width: int, height: int, output_path: str
    ) -> Dict[str, Any]:
        """Call ComfyUI API on owner's GPU server for AnimateDiff generation."""
        comfyui_url = getattr(settings, "COMFYUI_URL", "")
        if not comfyui_url:
            return {"success": False, "error": "comfyui_not_configured"}

        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int(time.time() * 1000) % 2147483647,
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "animatediff_lightning"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "VHS_VideoCombine", "inputs": {"frame_rate": 8, "images": ["8", 0]}},
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            submit_resp = await client.post(
                f"{comfyui_url}/prompt", json={"prompt": workflow}, timeout=DEFAULT_TIMEOUT
            )
            if submit_resp.status_code != 200:
                return {"success": False, "error": f"comfyui_http_{submit_resp.status_code}"}

            prompt_id = submit_resp.json().get("prompt_id")
            if not prompt_id:
                return {"success": False, "error": "comfyui_no_prompt_id"}

            for _ in range(120):
                await asyncio.sleep(2)
                history_resp = await client.get(
                    f"{comfyui_url}/history/{prompt_id}", timeout=DEFAULT_TIMEOUT
                )
                if history_resp.status_code != 200:
                    continue
                history = history_resp.json().get(prompt_id)
                if not history:
                    continue
                status = history.get("status", {})
                if status.get("completed"):
                    outputs = history.get("outputs", {})
                    video_node = outputs.get("9", {})
                    gifs = video_node.get("gifs", [])
                    if gifs:
                        filename = gifs[0].get("filename")
                        video_resp = await client.get(
                            f"{comfyui_url}/view?filename={filename}&type=output",
                            timeout=DEFAULT_TIMEOUT,
                        )
                        if video_resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(video_resp.content)
                            return {"success": True, "path": output_path, "engine": "comfyui_animatediff"}
                elif status.get("status_str") == "error":
                    return {"success": False, "error": "comfyui_generation_failed"}

        return {"success": False, "error": "comfyui_timeout"}

    async def _replicate_generate_animation(
        self, prompt: str, duration_seconds: int, width: int, height: int,
        output_path: str, api_key: str,
    ) -> Dict[str, Any]:
        """Call Replicate AnimateDiff with provided key."""
        num_frames = min(duration_seconds * 8, 64)
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            start_resp = await client.post(
                f"{settings.REPLICATE_API_URL}/predictions",
                json={
                    "version": settings.ANIMATEDIFF_MODEL,
                    "input": {"prompt": prompt, "num_frames": num_frames, "width": width, "height": height},
                },
                headers=headers,
            )
            if start_resp.status_code == 429:
                media_key_vault.replicate.mark_rate_limited(api_key, float(start_resp.headers.get("retry-after", 60)))
                return {"success": False, "error": "replicate_rate_limited"}
            if start_resp.status_code != 201 and start_resp.status_code != 200:
                media_key_vault.replicate.mark_error(api_key)
                return {"success": False, "error": f"replicate_http_{start_resp.status_code}"}

            prediction = start_resp.json()
            for _ in range(60):
                await asyncio.sleep(2)
                poll_resp = await client.get(
                    f"{settings.REPLICATE_API_URL}/predictions/{prediction['id']}",
                    headers=headers,
                )
                if poll_resp.status_code == 429:
                    media_key_vault.replicate.mark_rate_limited(api_key)
                    return {"success": False, "error": "replicate_rate_limited"}
                data = poll_resp.json()
                if data.get("status") == "succeeded":
                    output_url = data.get("output")
                    if isinstance(output_url, list):
                        output_url = output_url[0]
                    if output_url:
                        anim_resp = await client.get(output_url, timeout=DEFAULT_TIMEOUT)
                        if anim_resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(anim_resp.content)
                            media_key_vault.replicate.mark_success(api_key)
                            return {"success": True, "path": output_path, "engine": "replicate_animatediff"}
                elif data.get("status") == "failed":
                    media_key_vault.replicate.mark_error(api_key)
                    return {"success": False, "error": "replicate_animatediff_failed"}

        return {"success": False, "error": "replicate_timeout"}

    async def _placeholder_animation(
        self,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        output_path: str,
    ) -> Dict[str, Any]:
        """Generate a simple animated GIF placeholder."""
        try:
            from PIL import Image, ImageDraw

            def _create():
                frames = []
                num_frames = min(duration_seconds * 8, 32)
                for i in range(num_frames):
                    img = Image.new("RGB", (width, height), (15, 23, 42))
                    draw = ImageDraw.Draw(img)
                    # Animated circle
                    x = int((i / num_frames) * width)
                    y = height // 2
                    r = 50
                    draw.ellipse([x - r, y - r, x + r, y + r], fill=(59, 130, 246))
                    # Text
                    text = prompt[:30]
                    draw.text((10, 10), text, fill=(255, 255, 255))
                    frames.append(img)
                # Save as GIF
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=100,
                    loop=0,
                )

            await asyncio.to_thread(_create)
            return {
                "success": True,
                "path": output_path,
                "engine": "placeholder_gif",
                "duration": duration_seconds,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
media_generation_service = MediaGenerationService()
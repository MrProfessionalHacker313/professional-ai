"""
Professional AI - Media Engine Upscaler Service
8K QUALITY: Generation at high res + upscale pipeline (Real-ESRGAN x4 /
Topaz-style upscaler on the server) → output 8K (7680x4320) for videos,
8K for pictures/animations. Quality = top of the world.
"""

from __future__ import annotations

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from app.config import settings

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Resolution targets (width x height)
RESOLUTION_TARGETS = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
    "8k": (7680, 4320),
}


class UpscalerService:
    """Upscales generated media to the requested resolution (up to 8K)."""

    def __init__(self):
        self._enabled = settings.MEDIA_UPSCALER_ENABLED
        self._output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "upscaled"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def upscale_image(
        self,
        input_path: str,
        target_resolution: str = "8k",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upscale an image to the target resolution.
        Uses Real-ESRGAN API if configured, otherwise Pillow fallback.
        """
        if not self._enabled:
            return {"success": True, "skipped": True, "path": input_path}

        if not os.path.exists(input_path):
            return {"success": False, "error": "input_not_found"}

        if output_path is None:
            stem = Path(input_path).stem
            output_path = str(self._output_dir / f"{stem}_{target_resolution}.png")

        # Try Real-ESRGAN API first
        if settings.REAL_ESRGAN_API_URL:
            try:
                result = await self._real_esrgan_upscale(input_path, output_path, target_resolution)
                if result.get("success"):
                    return result
            except Exception as e:
                logger.warning(f"Real-ESRGAN upscale failed, falling back to Pillow: {e}")

        # Pillow fallback (bicubic upscale)
        if PIL_AVAILABLE:
            return await self._pillow_upscale(input_path, output_path, target_resolution)

        return {"success": False, "error": "no_upscaler_available"}

    async def _real_esrgan_upscale(
        self,
        input_path: str,
        output_path: str,
        target_resolution: str,
    ) -> Dict[str, Any]:
        """Call Real-ESRGAN API for high-quality upscaling."""
        import httpx

        target = RESOLUTION_TARGETS.get(target_resolution, RESOLUTION_TARGETS["8k"])

        async with httpx.AsyncClient(timeout=120) as client:
            with open(input_path, "rb") as f:
                files = {"file": (Path(input_path).name, f, "image/png")}
                data = {
                    "scale": str(settings.REAL_ESRGAN_SCALE),
                    "target_width": str(target[0]),
                    "target_height": str(target[1]),
                }
                resp = await client.post(
                    f"{settings.REAL_ESRGAN_API_URL}/upscale",
                    files=files,
                    data=data,
                )

            if resp.status_code == 200:
                with open(output_path, "wb") as out:
                    out.write(resp.content)
                return {
                    "success": True,
                    "path": output_path,
                    "resolution": target_resolution,
                    "width": target[0],
                    "height": target[1],
                    "method": "real_esrgan",
                }

        return {"success": False, "error": f"real_esrgan_http_{resp.status_code}"}

    async def _pillow_upscale(
        self,
        input_path: str,
        output_path: str,
        target_resolution: str,
    ) -> Dict[str, Any]:
        """Pillow-based upscale (bicubic) as fallback."""
        target = RESOLUTION_TARGETS.get(target_resolution, RESOLUTION_TARGETS["8k"])

        # Run in thread pool to avoid blocking event loop
        def _do_upscale():
            img = Image.open(input_path)
            img = img.convert("RGB")
            img = img.resize(target, Image.LANCZOS)
            img.save(output_path, "PNG")
            return img.size

        size = await asyncio.to_thread(_do_upscale)

        return {
            "success": True,
            "path": output_path,
            "resolution": target_resolution,
            "width": size[0],
            "height": size[1],
            "method": "pillow_lanczos",
        }

    async def upscale_video_frames(
        self,
        frames_dir: str,
        target_resolution: str = "8k",
    ) -> Dict[str, Any]:
        """
        Upscale all frames in a directory (for video upscaling).
        Returns count of upscaled frames.
        """
        if not os.path.isdir(frames_dir):
            return {"success": False, "error": "frames_dir_not_found"}

        frame_files = sorted([
            f for f in os.listdir(frames_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])

        if not frame_files:
            return {"success": False, "error": "no_frames_found"}

        upscaled_count = 0
        for frame_file in frame_files:
            frame_path = os.path.join(frames_dir, frame_file)
            result = await self.upscale_image(frame_path, target_resolution)
            if result.get("success"):
                upscaled_count += 1

        return {
            "success": True,
            "total_frames": len(frame_files),
            "upscaled_frames": upscaled_count,
            "resolution": target_resolution,
        }


# Singleton
upscaler_service = UpscalerService()
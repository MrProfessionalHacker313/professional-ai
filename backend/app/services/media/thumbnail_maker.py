"""
Professional AI - AI Thumbnail Maker Service
Auto-generates 5 clickable thumbnails for videos with bold text and eagle branding.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.models.media_extras import MediaThumbnail, ThumbnailStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class ThumbnailMakerService:
    """Service for generating AI-powered thumbnails for videos."""
    
    def __init__(self):
        self.output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "thumbnails"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Eagle logo path (semi-transparent watermark)
        self.eagle_logo_path = Path("./data/media_assets/eagle_logo.png")
        
        # Font paths for different languages
        self.font_dir = Path("./data/media_assets/fonts")
        self.font_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_thumbnails(
        self,
        db: AsyncSession,
        job_id: str,
        user_id: str,
        video_topic: str,
        language: str = "en",
        count: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate 5 clickable thumbnails for a video.
        
        Args:
            db: Database session
            job_id: Media job ID
            user_id: User ID
            video_topic: Video topic/description for context
            language: User's language for text overlay
            count: Number of thumbnails to generate (default 5)
        
        Returns:
            Dict with thumbnail URLs and metadata
        """
        try:
            # Create thumbnail records in DB
            thumbnails = []
            for i in range(count):
                thumbnail = MediaThumbnail(
                    job_id=uuid.UUID(job_id),
                    user_id=uuid.UUID(user_id),
                    status=ThumbnailStatus.GENERATING,
                )
                db.add(thumbnail)
                thumbnails.append(thumbnail)
            
            await db.flush()
            
            # Generate thumbnails in parallel
            tasks = []
            for i, thumbnail in enumerate(thumbnails):
                task = self._generate_single_thumbnail(
                    thumbnail_id=str(thumbnail.id),
                    job_id=job_id,
                    video_topic=video_topic,
                    language=language,
                    variant=i,
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update DB with results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    thumbnails[i].status = ThumbnailStatus.FAILED
                    thumbnails[i].error_message = str(result)
                else:
                    thumbnails[i].status = ThumbnailStatus.COMPLETED
                    thumbnails[i].thumbnail_url = result.get("url")
                    thumbnails[i].thumbnail_path = result.get("path")
                    thumbnails[i].thumbnail_text = result.get("text")
                    thumbnails[i].generation_prompt = result.get("prompt")
                    thumbnails[i].ai_model_used = result.get("model")
                    thumbnails[i].width = 1280
                    thumbnails[i].height = 720
                    thumbnails[i].file_size_bytes = result.get("size_bytes")
            
            await db.commit()
            
            # Return successful thumbnails
            successful = [t for t in thumbnails if t.status == ThumbnailStatus.COMPLETED]
            return {
                "success": True,
                "thumbnails": [
                    {
                        "id": str(t.id),
                        "url": t.thumbnail_url,
                        "text": t.thumbnail_text,
                        "model": t.ai_model_used,
                    }
                    for t in successful
                ],
                "count": len(successful),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "thumbnails": [],
            }
    
    async def _generate_single_thumbnail(
        self,
        thumbnail_id: str,
        job_id: str,
        video_topic: str,
        language: str,
        variant: int,
    ) -> Dict[str, Any]:
        """Generate a single thumbnail image."""
        try:
            # Generate AI image using fal.ai FLUX or Replicate SDXL
            image_path = await self._generate_ai_image(
                topic=video_topic,
                language=language,
                variant=variant,
            )
            
            # Add bold text overlay in user's language
            text_overlay = self._generate_text_overlay(video_topic, language)
            
            # Add eagle logo watermark
            final_image = self._add_watermark_and_text(
                image_path=image_path,
                text=text_overlay,
                language=language,
            )
            
            # Save final thumbnail
            output_path = self.output_dir / f"thumb_{thumbnail_id}.png"
            final_image.save(output_path, "PNG", optimize=True)
            
            # Get file size
            size_bytes = output_path.stat().st_size
            
            # In production, upload to GCS/S3 and return public URL
            # For now, return local path
            return {
                "url": f"/media/thumbnails/{thumbnail_id}.png",
                "path": str(output_path),
                "text": text_overlay,
                "prompt": f"Thumbnail for: {video_topic}",
                "model": "flux-schnell",
                "size_bytes": size_bytes,
            }
            
        except Exception as e:
            raise Exception(f"Thumbnail generation failed: {str(e)}")
    
    async def _generate_ai_image(self, topic: str, language: str, variant: int) -> Path:
        """
        Generate AI image using fal.ai FLUX (preferred) or Replicate SDXL.
        Creates visually striking thumbnail backgrounds.
        """
        # Different prompts for 5 variants
        prompts = [
            f"Professional thumbnail, bold, eye-catching, {topic}, cinematic lighting, 16:9 aspect ratio, high contrast, vibrant colors",
            f"Dynamic thumbnail design, {topic}, dramatic lighting, professional, YouTube thumbnail style, 16:9",
            f"Bold graphic design, {topic}, modern, clean, high impact, 16:9 thumbnail, professional photography style",
            f"Eye-catching thumbnail, {topic}, vibrant colors, professional, marketing style, 16:9 aspect ratio",
            f"Stunning visual, {topic}, cinematic, professional, high quality, YouTube thumbnail, 16:9",
        ]
        
        prompt = prompts[variant % len(prompts)]
        
        # Try fal.ai FLUX first (faster, better quality)
        if hasattr(settings, 'FAL_AI_API_KEY') and settings.FAL_AI_API_KEY:
            return await self._generate_with_fal_flux(prompt)
        
        # Fallback to Replicate SDXL
        elif hasattr(settings, 'REPLICATE_API_KEY') and settings.REPLICATE_API_KEY:
            return await self._generate_with_replicate_sdxl(prompt)
        
        # Fallback: Generate gradient placeholder
        else:
            return self._generate_placeholder_thumbnail(topic, variant)
    
    async def _generate_with_fal_flux(self, prompt: str) -> Path:
        """Generate image using fal.ai FLUX Schnell (fast, free tier available)."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Submit job
                response = await client.post(
                    "https://queue.fal.run/fal-ai/flux-schnell/submit",
                    headers={"Authorization": f"Key {settings.FAL_AI_API_KEY}"},
                    json={
                        "prompt": prompt,
                        "image_size": "landscape_16_9",
                        "num_inference_steps": 4,  # Fast generation
                        "guidance_scale": 3.5,
                    },
                )
                response.raise_for_status()
                job_data = response.json()
                request_id = job_data["request_id"]
                
                # Poll for completion
                for _ in range(30):  # 30 second timeout
                    await asyncio.sleep(1)
                    status_response = await client.get(
                        f"https://queue.fal.run/fal-ai/flux-schnell/status/{request_id}",
                        headers={"Authorization": f"Key {settings.FAL_AI_API_KEY}"},
                    )
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "COMPLETED":
                        image_url = status_data["response"]["image"]["url"]
                        # Download image
                        img_response = await client.get(image_url)
                        img_path = self.output_dir / f"flux_{uuid.uuid4().hex[:8]}.png"
                        with open(img_path, "wb") as f:
                            f.write(img_response.content)
                        return img_path
                
                raise Exception("FLUX generation timeout")
                
        except Exception as e:
            raise Exception(f"fal.ai FLUX failed: {str(e)}")
    
    async def _generate_with_replicate_sdxl(self, prompt: str) -> Path:
        """Generate image using Replicate SDXL."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Start prediction
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {settings.REPLICATE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "version": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                        "input": {
                            "prompt": prompt,
                            "width": 1280,
                            "height": 720,
                            "num_inference_steps": 20,
                        },
                    },
                )
                response.raise_for_status()
                prediction = response.json()
                
                # Poll for completion
                for _ in range(60):  # 60 second timeout
                    await asyncio.sleep(1)
                    status_response = await client.get(
                        f"https://api.replicate.com/v1/predictions/{prediction['id']}",
                        headers={"Authorization": f"Token {settings.REPLICATE_API_KEY}"},
                    )
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "succeeded":
                        image_url = status_data["output"][0]
                        # Download image
                        img_response = await client.get(image_url)
                        img_path = self.output_dir / f"sdxl_{uuid.uuid4().hex[:8]}.png"
                        with open(img_path, "wb") as f:
                            f.write(img_response.content)
                        return img_path
                
                raise Exception("SDXL generation timeout")
                
        except Exception as e:
            raise Exception(f"Replicate SDXL failed: {str(e)}")
    
    def _generate_placeholder_thumbnail(self, topic: str, variant: int) -> Path:
        """Generate a gradient placeholder thumbnail when AI APIs are unavailable."""
        # Create gradient background
        colors = [
            ((65, 105, 225), (30, 144, 255)),  # Royal Blue to Dodger Blue
            ((255, 69, 0), (255, 140, 0)),     # Red-Orange to Orange
            ((50, 205, 50), (0, 255, 127)),    # Lime Green to Spring Green
            ((138, 43, 226), (75, 0, 130)),    # Blue Violet to Indigo
            ((255, 20, 147), (255, 105, 180)), # Deep Pink to Hot Pink
        ]
        
        color1, color2 = colors[variant % len(colors)]
        
        img = Image.new('RGB', (1280, 720), color1)
        draw = ImageDraw.Draw(img)
        
        # Create gradient
        for y in range(720):
            r = int(color1[0] + (color2[0] - color1[0]) * y / 720)
            g = int(color1[1] + (color2[1] - color1[1]) * y / 720)
            b = int(color1[2] + (color2[2] - color1[2]) * y / 720)
            draw.line([(0, y), (1280, y)], fill=(r, g, b))
        
        # Save placeholder
        output_path = self.output_dir / f"placeholder_{uuid.uuid4().hex[:8]}.png"
        img.save(output_path, "PNG")
        return output_path
    
    def _generate_text_overlay(self, topic: str, language: str) -> str:
        """
        Generate bold text overlay for thumbnail.
        Keeps it short and punchy (3-5 words max).
        """
        # Truncate topic to 5 words
        words = topic.split()[:5]
        text = " ".join(words)
        
        # Capitalize first letter of each word
        text = text.title()
        
        # Add emoji based on language/country
        emojis = {
            "en": "🔥",
            "ur": "⭐",
            "hi": "🌟",
            "ar": "✨",
            "bn": "💫",
        }
        emoji = emojis.get(language, "🔥")
        
        return f"{emoji} {text}"
    
    def _add_watermark_and_text(
        self,
        image_path: Path,
        text: str,
        language: str,
    ) -> Image.Image:
        """
        Add bold text overlay and eagle logo watermark to thumbnail.
        """
        # Load image
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Load font (use default if custom font not available)
        try:
            # Try to load language-specific font
            font_large = ImageFont.truetype(
                str(self.font_dir / "Roboto-Bold.ttf"),
                80
            )
            font_small = ImageFont.truetype(
                str(self.font_dir / "Roboto-Bold.ttf"),
                40
            )
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Add bold text overlay (centered, with outline for readability)
        text_bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (1280 - text_width) // 2
        y = (720 - text_height) // 2
        
        # Draw text outline (black)
        for offset_x in [-3, -2, -1, 0, 1, 2, 3]:
            for offset_y in [-3, -2, -1, 0, 1, 2, 3]:
                draw.text(
                    (x + offset_x, y + offset_y),
                    text,
                    font=font_large,
                    fill=(0, 0, 0),
                )
        
        # Draw main text (white)
        draw.text((x, y), text, font=font_large, fill=(255, 255, 255))
        
        # Add eagle logo watermark (bottom-right, semi-transparent)
        if self.eagle_logo_path.exists():
            try:
                logo = Image.open(self.eagle_logo_path).convert("RGBA")
                logo = logo.resize((150, 150))
                
                # Create transparent overlay
                img_rgba = img.convert("RGBA")
                overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
                overlay.paste(logo, (1280 - 160, 720 - 160), logo)
                
                # Blend with 70% opacity
                img_rgba = Image.alpha_composite(img_rgba, overlay)
                img = img_rgba.convert("RGB")
            except Exception as e:
                print(f"Warning: Could not add eagle logo: {e}")
        
        return img
    
    async def select_thumbnail(
        self,
        db: AsyncSession,
        thumbnail_id: str,
        user_id: str,
        job_id: str,
    ) -> Dict[str, Any]:
        """
        User selects their preferred thumbnail for a video.
        Updates the media_jobs.selected_thumbnail_url field.
        """
        try:
            # Get thumbnail
            result = await db.execute(
                select(MediaThumbnail).where(
                    MediaThumbnail.id == uuid.UUID(thumbnail_id),
                    MediaThumbnail.user_id == uuid.UUID(user_id),
                    MediaThumbnail.job_id == uuid.UUID(job_id),
                )
            )
            thumbnail = result.scalar_one_or_none()
            
            if not thumbnail:
                return {"success": False, "error": "Thumbnail not found"}
            
            if thumbnail.status != ThumbnailStatus.COMPLETED:
                return {"success": False, "error": "Thumbnail not ready"}
            
            # Mark as selected
            thumbnail.is_selected = True
            thumbnail.selected_at = datetime.now(timezone.utc)
            
            # Update media job
            from app.models.media_engine import MediaJob
            job_result = await db.execute(
                select(MediaJob).where(MediaJob.id == uuid.UUID(job_id))
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.selected_thumbnail_url = thumbnail.thumbnail_url
            
            await db.commit()
            
            return {
                "success": True,
                "thumbnail_id": str(thumbnail.id),
                "thumbnail_url": thumbnail.thumbnail_url,
                "message": "Thumbnail selected successfully",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_thumbnails(
        self,
        db: AsyncSession,
        job_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get all thumbnails for a video job."""
        try:
            result = await db.execute(
                select(MediaThumbnail).where(
                    MediaThumbnail.job_id == uuid.UUID(job_id),
                    MediaThumbnail.user_id == uuid.UUID(user_id),
                ).order_by(MediaThumbnail.created_at.asc())
            )
            thumbnails = result.scalars().all()
            
            return {
                "success": True,
                "thumbnails": [
                    {
                        "id": str(t.id),
                        "url": t.thumbnail_url,
                        "text": t.thumbnail_text,
                        "is_selected": t.is_selected,
                        "status": t.status.value,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                    }
                    for t in thumbnails
                ],
                "count": len(thumbnails),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Import missing modules
from datetime import datetime, timezone

# Singleton instance
thumbnail_maker_service = ThumbnailMakerService()
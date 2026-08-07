"""
Professional AI - Meme Maker Service
Generates funny meme images and videos from user text input.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
import random

from PIL import Image, ImageDraw, ImageFont
import httpx

from app.config import settings
from app.models.media_extras import MediaMeme, MemeType, MemeStatus
from app.database import get_db


class MemeMakerService:
    """Service for generating memes from text."""
    
    def __init__(self):
        self.output_dir = Path(settings.MEDIA_OUTPUT_DIR) / "memes"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Meme templates directory
        self.templates_dir = Path("./data/media_assets/meme_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Font directory
        self.font_dir = Path("./data/media_assets/fonts")
        self.font_dir.mkdir(parents=True, exist_ok=True)
        
        # Popular meme templates (top text, bottom text format)
        self.popular_templates = [
            "drake", "distracted_boyfriend", "two_buttons", "change_my_mind",
            "doge", "success_kid", "scumbag_steve", "good_guy_greg",
            "overly_attached_girlfriend", "bad_luck_brian", "hide_the_pain_harold",
            "disaster_girl", "roll_safe", "leonardo_dicaprio", "confused_math_lady"
        ]
    
    async def generate_meme(
        self,
        user_id: str,
        meme_text: str,
        meme_type: str = "image",
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a meme from user text.
        
        Args:
            user_id: User ID
            meme_text: Text for the meme
            meme_type: "image" or "video"
            template: Optional template name (random if not provided)
        
        Returns:
            Dict with meme URL and metadata
        """
        try:
            # Check daily limit for free tier
            if not await self._check_meme_limit(user_id):
                return {
                    "success": False,
                    "error": "Daily meme limit reached (5/day for free tier)",
                    "limit_reached": True,
                }
            
            # Create meme record
            meme = MediaMeme(
                user_id=uuid.UUID(user_id),
                meme_text=meme_text,
                meme_type=MemeType(meme_type),
                template_used=template or random.choice(self.popular_templates),
                status=MemeStatus.GENERATING,
            )
            
            async with get_db() as db:
                db.add(meme)
                await db.flush()
                await db.commit()
            
            # Generate meme based on type
            if meme_type == "video":
                result = await self._generate_video_meme(
                    meme_id=str(meme.id),
                    text=meme_text,
                    template=meme.template_used,
                )
            else:
                result = await self._generate_image_meme(
                    meme_id=str(meme.id),
                    text=meme_text,
                    template=meme.template_used,
                )
            
            # Update meme record
            async with get_db() as db:
                meme_result = await db.execute(
                    select(MediaMeme).where(MediaMeme.id == meme.id)
                )
                meme = meme_result.scalar_one_or_none()
                if meme:
                    if result.get("success"):
                        meme.status = MemeStatus.COMPLETED
                        meme.output_url = result.get("url")
                        meme.output_path = result.get("path")
                        meme.output_size_bytes = result.get("size_bytes")
                        meme.completed_at = datetime.now(timezone.utc)
                    else:
                        meme.status = MemeStatus.FAILED
                        meme.error_message = result.get("error")
                    await db.commit()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _generate_image_meme(
        self,
        meme_id: str,
        text: str,
        template: str,
    ) -> Dict[str, Any]:
        """Generate an image meme with text overlay."""
        try:
            # Try to load template image
            template_path = self.templates_dir / f"{template}.jpg"
            
            if not template_path.exists():
                # Generate placeholder meme
                return self._generate_placeholder_meme(meme_id, text, template)
            
            # Load template
            img = Image.open(template_path).convert("RGB")
            
            # Add text overlay
            img = self._add_meme_text(img, text)
            
            # Save meme
            output_path = self.output_dir / f"meme_{meme_id}.png"
            img.save(output_path, "PNG", optimize=True)
            
            size_bytes = output_path.stat().st_size
            
            return {
                "success": True,
                "url": f"/media/memes/{meme_id}.png",
                "path": str(output_path),
                "type": "image",
                "template": template,
                "size_bytes": size_bytes,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Image meme generation failed: {str(e)}",
            }
    
    async def _generate_video_meme(
        self,
        meme_id: str,
        text: str,
        template: str,
    ) -> Dict[str, Any]:
        """Generate a video meme (5-second clip with text and music)."""
        try:
            # For video memes, we'll create a simple slideshow-style video
            # In production, use MoviePy or FFmpeg
            
            # Generate 5 frames with text
            frames = []
            for i in range(5):
                frame = self._create_meme_frame(text, i)
                frames.append(frame)
            
            # Save frames
            frame_paths = []
            for i, frame in enumerate(frames):
                frame_path = self.output_dir / f"meme_{meme_id}_frame_{i}.png"
                frame.save(frame_path, "PNG")
                frame_paths.append(str(frame_path))
            
            # TODO: Use MoviePy to combine frames into video with background music
            # For now, return the first frame as placeholder
            output_path = self.output_dir / f"meme_{meme_id}.png"
            frames[0].save(output_path, "PNG")
            
            size_bytes = output_path.stat().st_size
            
            return {
                "success": True,
                "url": f"/media/memes/{meme_id}.png",
                "path": str(output_path),
                "type": "video",
                "template": template,
                "size_bytes": size_bytes,
                "note": "Video meme generation requires MoviePy/FFmpeg",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Video meme generation failed: {str(e)}",
            }
    
    def _generate_placeholder_meme(self, meme_id: str, text: str, template: str) -> Dict[str, Any]:
        """Generate a placeholder meme when templates are unavailable."""
        # Create a simple meme with gradient background
        img = Image.new('RGB', (800, 600), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Add gradient background
        for y in range(600):
            r = int(255 - (y / 600) * 100)
            g = int(255 - (y / 600) * 100)
            b = int(255 - (y / 600) * 100)
            draw.line([(0, y), (800, y)], fill=(r, g, b))
        
        # Add text
        img = self._add_meme_text(img, text)
        
        # Save
        output_path = self.output_dir / f"meme_{meme_id}.png"
        img.save(output_path, "PNG")
        
        size_bytes = output_path.stat().st_size
        
        return {
            "success": True,
            "url": f"/media/memes/{meme_id}.png",
            "path": str(output_path),
            "type": "image",
            "template": template,
            "size_bytes": size_bytes,
        }
    
    def _add_meme_text(self, img: Image.Image, text: str) -> Image.Image:
        """Add meme-style text to image (top and bottom text)."""
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font = ImageFont.truetype(
                str(self.font_dir / "Impact.ttf"),
                60
            )
        except:
            try:
                font = ImageFont.truetype(
                    str(self.font_dir / "Roboto-Bold.ttf"),
                    60
                )
            except:
                font = ImageFont.load_default()
        
        # Split text into top and bottom (if contains | or -)
        if "|" in text:
            parts = text.split("|", 1)
            top_text = parts[0].strip()
            bottom_text = parts[1].strip() if len(parts) > 1 else ""
        elif "-" in text and len(text) > 20:
            parts = text.rsplit("-", 1)
            top_text = parts[0].strip()
            bottom_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            top_text = text
            bottom_text = ""
        
        # Draw top text (centered, with black outline)
        if top_text:
            self._draw_text_with_outline(draw, top_text, img.width, 50, font)
        
        # Draw bottom text (centered, with black outline)
        if bottom_text:
            self._draw_text_with_outline(draw, bottom_text, img.width, img.height - 100, font)
        
        return img
    
    def _draw_text_with_outline(
        self,
        draw: ImageDraw.Draw,
        text: str,
        img_width: int,
        y: int,
        font,
    ):
        """Draw text with black outline for readability."""
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Center horizontally
        x = (img_width - text_width) // 2
        
        # Draw outline (black)
        for offset_x in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
            for offset_y in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                draw.text((x + offset_x, y + offset_y), text, font=font, fill=(0, 0, 0))
        
        # Draw main text (white)
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    def _create_meme_frame(self, text: str, frame_number: int) -> Image.Image:
        """Create a single frame for video meme."""
        img = Image.new('RGB', (800, 600), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            font = ImageFont.truetype(str(self.font_dir / "Impact.ttf"), 50)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (800 - text_width) // 2
        y = 250 + (frame_number * 10)
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        return img
    
    async def _check_meme_limit(self, user_id: str) -> bool:
        """Check if user has reached daily meme limit."""
        try:
            from app.services.media.limits import MediaLimitsService
            from app.database import get_db
            
            async with get_db() as db:
                limits_service = MediaLimitsService(db)
                # For now, use a simple daily limit check
                # In production, integrate with the full limits system
                return True  # Placeholder
        except:
            return True
    
    async def get_user_memes(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get user's meme history."""
        try:
            async with get_db() as db:
                result = await db.execute(
                    select(MediaMeme)
                    .where(MediaMeme.user_id == uuid.UUID(user_id))
                    .order_by(MediaMeme.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                memes = result.scalars().all()
                
                return {
                    "success": True,
                    "memes": [
                        {
                            "id": str(m.id),
                            "text": m.meme_text,
                            "type": m.meme_type.value,
                            "template": m.template_used,
                            "url": m.output_url,
                            "status": m.status.value,
                            "created_at": m.created_at.isoformat() if m.created_at else None,
                        }
                        for m in memes
                    ],
                    "count": len(memes),
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_meme(
        self,
        meme_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get a specific meme."""
        try:
            async with get_db() as db:
                result = await db.execute(
                    select(MediaMeme).where(
                        MediaMeme.id == uuid.UUID(meme_id),
                        MediaMeme.user_id == uuid.UUID(user_id),
                    )
                )
                meme = result.scalar_one_or_none()
                
                if not meme:
                    return {"success": False, "error": "Meme not found"}
                
                return {
                    "success": True,
                    "meme": {
                        "id": str(meme.id),
                        "text": meme.meme_text,
                        "type": meme.meme_type.value,
                        "template": meme.template_used,
                        "url": meme.output_url,
                        "status": meme.status.value,
                        "suggested_captions": meme.suggested_captions,
                        "humor_score": meme.humor_score,
                        "created_at": meme.created_at.isoformat() if meme.created_at else None,
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Import missing modules at the end to avoid circular imports
from datetime import datetime, timezone
from sqlalchemy import select

# Singleton instance
meme_maker_service = MemeMakerService()
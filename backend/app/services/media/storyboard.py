"""
Professional AI - Media Engine Storyboard Builder
Parses user scene descriptions into a structured storyboard with per-scene
generation prompts. No scene is ever skipped.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from loguru import logger

from app.config import settings


# ===================================================================
# Scene Parsing
# ===================================================================

SCENE_PATTERNS = [
    # "Scene 1: description", "Scene 2: description"
    re.compile(r"scene\s*(\d+)\s*[:.\-]?\s*(.+?)(?=scene\s*\d+\s*[:.\-]?|$)", re.IGNORECASE | re.DOTALL),
    # "1. description", "2. description"
    re.compile(r"(?:^|\n)\s*(\d+)[.)]\s*(.+?)(?=(?:\n\s*\d+[.)]\s*)|$)", re.DOTALL),
    # "First, description", "Next, description", "Then, description"
    re.compile(r"(?:^|\n)\s*(first|second|third|fourth|fifth|next|then|finally)[,:]\s*(.+?)(?=(?:\n\s*(?:first|second|third|fourth|fifth|next|then|finally)[,:]\s*)|$)", re.IGNORECASE | re.DOTALL),
]

# Default scene duration when not specified
DEFAULT_SCENE_DURATION = 5.0


def parse_scenes(scenes_text: str) -> List[Dict[str, Any]]:
    """
    Parse raw scene text into structured scene objects.
    Handles: "Scene 1: ...", "1. ...", "First: ...", plain paragraphs.
    """
    if not scenes_text or not scenes_text.strip():
        return []

    scenes: List[Dict[str, Any]] = []
    text = scenes_text.strip()

    # Try each pattern until we get at least 2 scenes
    for pattern in SCENE_PATTERNS:
        matches = list(pattern.finditer(text))
        if len(matches) >= 2:
            for match in matches:
                num = int(match.group(1)) if match.group(1).isdigit() else len(scenes) + 1
                description = match.group(2).strip()
                # Clean trailing punctuation
                description = re.sub(r"[.;,]+$", "", description).strip()
                if description:
                    scenes.append({
                        "scene_number": num,
                        "description": description,
                        "prompt": _build_scene_prompt(description),
                        "duration_seconds": DEFAULT_SCENE_DURATION,
                        "status": "pending",
                    })
            if len(scenes) >= 2:
                # Normalize scene numbers
                for i, scene in enumerate(scenes):
                    scene["scene_number"] = i + 1
                break

    # Fallback: split into paragraphs / sentences
    if not scenes:
        # Split on double newlines first, then single newlines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
        if len(paragraphs) >= 2:
            for i, para in enumerate(paragraphs):
                scenes.append({
                    "scene_number": i + 1,
                    "description": para,
                    "prompt": _build_scene_prompt(para),
                    "duration_seconds": DEFAULT_SCENE_DURATION,
                    "status": "pending",
                })
        else:
            # Single scene
            scenes = [{
                "scene_number": 1,
                "description": text,
                "prompt": _build_scene_prompt(text),
                "duration_seconds": DEFAULT_SCENE_DURATION,
                "status": "pending",
            }]

    # Cap scene count
    max_scenes = settings.MEDIA_MAX_SCENES
    if len(scenes) > max_scenes:
        logger.warning(f"Scene count {len(scenes)} exceeds max {max_scenes} — truncating")
        scenes = scenes[:max_scenes]

    return scenes


def _build_scene_prompt(description: str) -> str:
    """
    Build a full generation prompt from a scene description.
    Includes quality keywords for top-tier output.
    """
    # Add high-quality suffixes for image/video generation
    quality_tags = (
        "ultra high definition, 8k resolution, cinematic lighting, "
        "professional composition, photorealistic, highly detailed, "
        "award winning, 35mm film look"
    )
    description_clean = description.strip().rstrip(".,;")
    return f"{description_clean}. {quality_tags}"


# ===================================================================
# Auto Storyboard from a Topic (when no explicit scenes provided)
# ===================================================================

AUTO_SCENE_TEMPLATES = {
    "hacking": [
        "Hacker silhouette typing in a dark room lit only by screen glow",
        "Glowing green code streams flow across multiple monitor screens",
        "A digital shield fractures and breaks apart with blue particles",
        "The hacker leans back with a satisfied smile as a firewall falls",
    ],
    "coding": [
        "Developer coding in a modern workspace with dual monitors",
        "Code streams rapidly across the screen with syntax highlighting",
        "A bug glows red then transforms into a green checkmark",
        "The developer celebrates as the application launches successfully",
    ],
    "cartoon": [
        "Colorful cartoon character waving hello in a bright animated world",
        "The character goes on a fun adventure through a whimsical landscape",
        "A comedic moment as the character bumps into a funny obstacle",
        "Happy ending with confetti and a big cartoon smile",
    ],
    "game": [
        "Epic video game hero standing in a fantasy landscape",
        "Intense action sequence with dynamic lighting and effects",
        "The hero defeats a massive boss with powerful abilities",
        "Victory screen with glowing trophy and celebration",
    ],
    "explainer": [
        "Clean 3D animated explainer scene with floating icons",
        "Infographic style animation showing key concepts with arrows",
        "Charts and diagrams animate into place with smooth transitions",
        "Summary scene with key takeaways and call to action",
    ],
    "story": [
        "Beautiful establishing shot with warm storytelling lighting",
        "Character moments that advance the narrative with emotion",
        "A turning point with dramatic tension and visual contrast",
        "Emotional resolution with satisfying narrative conclusion",
    ],
    "trending": [
        "Dynamic fast-paced opening with bold trending news graphics",
        "Key highlights displayed with eye-catching motion graphics",
        "Viral clip montage with energetic transitions",
        "Closing with trending hashtags and social statistics",
    ],
    "default": [
        "Cinematic establishing shot with dramatic lighting",
        "Main subject surrounded by rich detailed environment",
        "Action moment with dynamic composition and motion",
        "Resolution shot with beautiful closing visual",
    ],
}


def auto_storyboard(topic: str, script: Optional[str] = None, duration_seconds: int = 15) -> List[Dict[str, Any]]:
    """
    Generate a storyboard from just a topic when the user didn't provide scenes.
    Uses template scenes adapted to the topic.
    """
    topic_lower = topic.lower()
    template_key = "default"

    # Topic keyword matching
    topic_keywords = {
        "hacking": ["hack", "cyber", "security", "exploit", "strike", "breach"],
        "coding": ["code", "program", "develop", "software", "app", "python", "javascript"],
        "cartoon": ["cartoon", "animation", "kids", "funny", "toon"],
        "game": ["game", "gaming", "play", "esports", "gamer"],
        "explainer": ["explain", "learn", "tutorial", "how to", "guide", "education"],
        "story": ["story", "tale", "narrative", "once upon"],
        "trending": ["trend", "viral", "news", "popular", "top"],
    }

    for key, keywords in topic_keywords.items():
        if any(kw in topic_lower for kw in keywords):
            template_key = key
            break

    template = AUTO_SCENE_TEMPLATES.get(template_key, AUTO_SCENE_TEMPLATES["default"])

    # Distribute duration across scenes
    scenes = []
    num_scenes = len(template)
    scene_duration = max(3.0, duration_seconds / num_scenes)

    for i, desc in enumerate(template):
        # Inject the topic into the scene for personalization
        personalized = f"{desc} related to {topic}"
        scenes.append({
            "scene_number": i + 1,
            "description": personalized,
            "prompt": _build_scene_prompt(personalized),
            "duration_seconds": scene_duration,
            "status": "pending",
        })

    return scenes


# ===================================================================
# Storyboard Service
# ===================================================================

class StoryboardService:
    """Builds and manages storyboards for media generation jobs."""

    async def build_storyboard(
        self,
        topic: str,
        script: Optional[str] = None,
        scenes_text: Optional[str] = None,
        duration_seconds: int = 15,
    ) -> Dict[str, Any]:
        """
        Build a storyboard from user input.
        - If scenes_text is provided, parse it (no scene skipped).
        - Otherwise auto-generate from topic + script.
        """
        scenes: List[Dict[str, Any]] = []

        if scenes_text and scenes_text.strip():
            scenes = parse_scenes(scenes_text)
            logger.info(f"Parsed {len(scenes)} scenes from user input")

        if not scenes:
            scenes = auto_storyboard(topic, script, duration_seconds)
            logger.info(f"Auto-generated {len(scenes)} scenes from topic")

        # If we have an explicit script, split it across scenes for voice/subs
        script_lines = []
        if script and script.strip():
            script_lines = _split_script_for_scenes(script, len(scenes))

        # Assign script segments to scenes
        for i, scene in enumerate(scenes):
            if i < len(script_lines):
                scene["script"] = script_lines[i]
            else:
                scene["script"] = ""

        return {
            "scenes": scenes,
            "total_scenes": len(scenes),
            "generated_at": None,  # set by caller
        }


def _split_script_for_scenes(script: str, num_scenes: int) -> List[str]:
    """Split a script into chunks, one per scene."""
    lines = [line.strip() for line in script.split("\n") if line.strip()]

    # If we have enough lines, one per scene
    if len(lines) >= num_scenes:
        # Distribute evenly
        chunk_size = max(1, len(lines) // num_scenes)
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk = " ".join(lines[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
            if len(chunks) >= num_scenes:
                break
        # If still short, pad
        while len(chunks) < num_scenes:
            chunks.append(chunks[-1] if chunks else "")
        return chunks[:num_scenes]

    # Otherwise split by sentence
    sentences = re.split(r"(?<=[.!?])\s+", script)
    if len(sentences) >= num_scenes:
        chunk_size = max(1, len(sentences) // num_scenes)
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
            if len(chunks) >= num_scenes:
                break
        while len(chunks) < num_scenes:
            chunks.append(chunks[-1] if chunks else "")
        return chunks[:num_scenes]

    # Very short script - duplicate roughly
    chunks = []
    for i in range(num_scenes):
        start = (i * len(sentences)) // num_scenes
        end = ((i + 1) * len(sentences)) // num_scenes
        chunk = " ".join(sentences[start:end]) if sentences else script
        chunks.append(chunk)
    return chunks


# Singleton
storyboard_service = StoryboardService()
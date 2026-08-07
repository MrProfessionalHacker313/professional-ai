"""
Professional AI - Auto Video Editor Service
============================================
Professional automatic video editing pipeline:
- Upload raw clips → AI analyzes, cuts, transitions, captions, color-grades, exports
- Platform presets: TikTok (9:16), YouTube (16:9), Reels (9:16), Instagram (1:1), Story (9:16)
- All CPU/GPU work on the cloud server — user device never lags.

Stages:
  1. UPLOADING  → raw files stored
  2. ANALYZING  → scene detection + AI scoring (keep best moments)
  3. EDITING    → cuts, transitions, color grade, stabilize, Ken Burns, speed, intro/outro
  4. RENDERING  → FFmpeg assembly, caption burn, music sync, platform preset
  5. COMPLETED  → output ready for download
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from app.config import settings


# ===================================================================
# DATA CLASSES
# ===================================================================

@dataclass
class SceneSegment:
    """A detected scene segment with quality score."""
    start: float
    end: float
    score: float
    keep: bool
    reason: str
    thumbnail_path: Optional[str] = None


@dataclass
class CaptionSegment:
    """A single caption segment with timing."""
    start: float
    end: float
    text: str
    words: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TransitionConfig:
    """Transition configuration."""
    type: str = "fade"  # fade, crossfade, wipe, slide
    duration_ms: int = 500
    enabled: bool = True


@dataclass
class PlatformPreset:
    """Platform-specific export settings."""
    name: str
    aspect_ratio: str  # "9:16", "16:9", "1:1"
    width: int
    height: int
    max_duration: int  # seconds
    recommended_bitrate: str
    caption_style: str = "modern"


# ===================================================================
# PLATFORM PRESETS
# ===================================================================

PLATFORM_PRESETS: Dict[str, PlatformPreset] = {
    "tiktok": PlatformPreset(
        name="TikTok", aspect_ratio="9:16", width=1080, height=1920,
        max_duration=180, recommended_bitrate="8M",
    ),
    "youtube": PlatformPreset(
        name="YouTube", aspect_ratio="16:9", width=1920, height=1080,
        max_duration=600, recommended_bitrate="20M",
    ),
    "reels": PlatformPreset(
        name="Reels/Shorts", aspect_ratio="9:16", width=1080, height=1920,
        max_duration=90, recommended_bitrate="8M",
    ),
    "instagram": PlatformPreset(
        name="Instagram Feed", aspect_ratio="1:1", width=1080, height=1080,
        max_duration=60, recommended_bitrate="8M",
    ),
    "story": PlatformPreset(
        name="Story", aspect_ratio="9:16", width=1080, height=1920,
        max_duration=60, recommended_bitrate="8M",
    ),
    "custom": PlatformPreset(
        name="Custom", aspect_ratio="16:9", width=1920, height=1080,
        max_duration=600, recommended_bitrate="20M",
    ),
}


# ===================================================================
# AUTO EDITOR SERVICE
# ===================================================================

class AutoEditorService:
    """
    Professional automatic video editing pipeline.
    All heavy processing on the server — FFmpeg + Whisper + AI scoring.
    """

    def __init__(self):
        self._temp_dir = Path(settings.AUTO_EDITOR_TEMP_DIR)
        self._output_dir = Path(settings.AUTO_EDITOR_OUTPUT_DIR)
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._intro_outro_path = Path(settings.AUTO_EDITOR_INTRO_OUTRO_PATH)
        self._bg_music_dir = Path(settings.AUTO_EDITOR_BG_MUSIC_DIR)

    # ===================================================================
    # STAGE 1: UPLOAD
    # ===================================================================

    def save_uploaded_file(self, user_id: str, file_bytes: bytes, filename: str) -> str:
        """Save uploaded raw clip to temp storage."""
        ext = Path(filename).suffix or ".mp4"
        safe_name = f"raw_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        dest = self._temp_dir / safe_name
        with open(dest, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Saved uploaded file: {dest} ({len(file_bytes) / 1024 / 1024:.1f} MB)")
        return str(dest)

    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Remove temporary files."""
        for path in file_paths:
            try:
                p = Path(path)
                if p.exists():
                    p.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")

    # ===================================================================
    # STAGE 2: SCENE ANALYSIS + SCORING
    # ===================================================================

    async def analyze_scenes(self, input_path: str) -> List[SceneSegment]:
        """
        Analyze video: detect scene changes and score each segment.
        Uses FFmpeg scene detection + heuristics for quality scoring.
        """
        segments: List[SceneSegment] = []
        try:
            # Get video duration
            duration = await self._get_video_duration(input_path)
            if duration <= 0:
                return segments

            # Detect scene changes with FFmpeg
            scene_timestamps = await self._detect_scene_changes(input_path, duration)

            # Build segments from scene boundaries
            timestamps = [0.0] + scene_timestamps + [duration]
            threshold = settings.AUTO_EDITOR_SCENE_SCORE_THRESHOLD

            for i in range(len(timestamps) - 1):
                start = timestamps[i]
                end = timestamps[i + 1]
                seg_duration = end - start

                # Skip very short segments (< 0.5s)
                if seg_duration < 0.5:
                    continue

                # Score this segment (heuristic quality)
                score, reason = await self._score_segment(input_path, start, end, duration)

                segments.append(SceneSegment(
                    start=start,
                    end=end,
                    score=score,
                    keep=score >= threshold,
                    reason=reason,
                ))

            logger.info(f"Scene analysis: {len(segments)} segments, {sum(1 for s in segments if s.keep)} kept")
        except Exception as e:
            logger.error(f"Scene analysis failed: {e}")

        return segments

    async def _detect_scene_changes(self, input_path: str, duration: float) -> List[float]:
        """Detect scene change timestamps using FFmpeg."""
        timestamps: List[float] = []
        try:
            cmd = [
                "ffmpeg", "-i", input_path,
                "-vf", "select='gt(scene,0.3)',showinfo",
                "-an", "-f", "null", "-",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            for line in result.stderr.split("\n"):
                if "pts_time:" in line:
                    try:
                        parts = line.split("pts_time:")
                        if len(parts) > 1:
                            ts = float(parts[1].split()[0].strip())
                            if 0 < ts < duration:
                                timestamps.append(ts)
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            logger.warning(f"Scene change detection failed: {e}")

        # Deduplicate and sort
        timestamps = sorted(set(round(t, 2) for t in timestamps))
        return timestamps

    async def _score_segment(
        self, input_path: str, start: float, end: float, total_duration: float
    ) -> Tuple[float, str]:
        """
        Score a video segment for quality.
        Returns (score 0-1, reason).
        """
        reasons: List[str] = []
        score = 0.5  # Base score

        # Factor 1: Motion variance (more motion = more interesting)
        motion_score = await self._estimate_motion(input_path, start, end)
        score += motion_score * 0.3
        if motion_score > 0.5:
            reasons.append("high_motion")

        # Factor 2: Audio level (louder = more engaging)
        audio_score = await self._estimate_audio_level(input_path, start, end)
        score += audio_score * 0.2
        if audio_score > 0.5:
            reasons.append("clear_audio")

        # Factor 3: Segment length (medium-length segments score higher)
        seg_len = end - start
        if 2.0 <= seg_len <= 10.0:
            score += 0.1
            reasons.append("good_pace")
        elif seg_len > 15.0:
            score -= 0.1
            reasons.append("too_long")

        # Factor 4: Position in video (start/end slightly penalized — intro/outro handled separately)
        mid = total_duration / 2
        seg_mid = (start + end) / 2
        if abs(seg_mid - mid) / max(mid, 1) > 0.7:
            score -= 0.05
            reasons.append("edge_position")

        # Clamp score
        score = max(0.0, min(1.0, score))
        return score, ", ".join(reasons) if reasons else "standard"

    async def _estimate_motion(self, input_path: str, start: float, end: float) -> float:
        """Estimate motion intensity in a segment using FFmpeg."""
        try:
            seg_dur = end - start
            if seg_dur < 0.5:
                return 0.3
            sample_dur = min(seg_dur, 3.0)
            cmd = [
                "ffmpeg", "-ss", str(start), "-t", str(sample_dur),
                "-i", input_path,
                "-vf", "mpdecimate,metadata=print",
                "-an", "-f", "null", "-",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            frame_diffs = result.stderr.count("frame:")
            frames_removed = result.stderr.count("dup")
            if frame_diffs > 0:
                return min(1.0, frames_removed / max(frame_diffs, 1) * 3)
            return 0.5
        except Exception:
            return 0.5

    async def _estimate_audio_level(self, input_path: str, start: float, end: float) -> float:
        """Estimate average audio level in a segment."""
        try:
            seg_dur = end - start
            sample_dur = min(seg_dur, 3.0)
            cmd = [
                "ffmpeg", "-ss", str(start), "-t", str(sample_dur),
                "-i", input_path,
                "-af", "volumedetect",
                "-f", "null", "-",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            for line in result.stderr.split("\n"):
                if "mean_volume:" in line:
                    db_str = line.split("mean_volume:")[1].strip().split()[0]
                    db = float(db_str.replace("dB", ""))
                    # Map -60dB..-10dB to 0..1
                    return max(0.0, min(1.0, (db + 60) / 50))
        except Exception:
            pass
        return 0.5

    async def _get_video_duration(self, input_path: str) -> float:
        """Get video duration in seconds."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    # ===================================================================
    # STAGE 3: EDITING PIPELINE
    # ===================================================================

    async def run_edit_pipeline(
        self,
        job_id: str,
        raw_files: List[str],
        segments: List[SceneSegment],
        preset: str,
        editing_options: Dict[str, Any],
        manual_overrides: Dict[str, Any],
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Run the full editing pipeline:
        1. Cut unwanted segments
        2. Add transitions
        3. Color grade
        4. Stabilize
        5. Ken Burns zoom
        6. Speed adjustment
        7. Add intro/outro
        8. Background music
        9. Platform preset formatting
        """
        work_dir = self._temp_dir / f"edit_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        output_dir = self._output_dir
        output_path = str(output_dir / f"edited_{job_id}.mp4")

        try:
            # Step 3a: Concatenate kept segments
            if progress_callback:
                progress_callback(15, "Cutting unwanted segments")
            concat_file = await self._cut_and_concat(
                raw_files, segments, work_dir, editing_options, manual_overrides
            )

            # Step 3b: Add transitions
            if editing_options.get("add_transitions", True):
                if progress_callback:
                    progress_callback(25, "Adding transitions")
                concat_file = await self._add_transitions(concat_file, work_dir, segments)

            # Step 3c: Color grade
            if editing_options.get("color_grade", True):
                if progress_callback:
                    progress_callback(35, "Color grading")
                concat_file = await self._apply_color_grade(
                    concat_file, work_dir, settings.AUTO_EDITOR_COLOR_GRADE_PRESET
                )

            # Step 3d: Stabilize shaky footage
            if editing_options.get("stabilize", True) and settings.AUTO_EDITOR_STABILIZE_ENABLED:
                if progress_callback:
                    progress_callback(45, "Stabilizing footage")
                concat_file = await self._stabilize_video(concat_file, work_dir)

            # Step 3e: Ken Burns zoom effect
            if editing_options.get("ken_burns", True):
                if progress_callback:
                    progress_callback(50, "Adding zoom effects")
                concat_file = await self._apply_ken_burns(concat_file, work_dir)

            # Step 3f: Speed adjustment
            if editing_options.get("adjust_speed", True) and manual_overrides.get("speed_factor"):
                if progress_callback:
                    progress_callback(55, "Adjusting speed")
                concat_file = await self._adjust_speed(
                    concat_file, work_dir, manual_overrides["speed_factor"]
                )

            # Step 3g: Add intro/outro
            if editing_options.get("add_intro_outro", True):
                if progress_callback:
                    progress_callback(60, "Adding intro & outro")
                concat_file = await self._add_intro_outro(concat_file, work_dir)

            # Step 3h: Background music
            if editing_options.get("background_music", True):
                if progress_callback:
                    progress_callback(70, "Mixing background music")
                concat_file = await self._add_background_music(concat_file, work_dir)

            # STAGE 4: RENDERING
            if progress_callback:
                progress_callback(75, "Rendering final video")

            platform_cfg = PLATFORM_PRESETS.get(preset, PLATFORM_PRESETS["custom"])

            # If user overrides aspect ratio, use that instead
            aspect_ratio = manual_overrides.get("aspect_ratio") or platform_cfg.aspect_ratio
            width, height = self._resolve_dimensions(
                platform_cfg.width, platform_cfg.height, aspect_ratio
            )

            # Final render with platform preset
            final_path = await self._render_final(
                concat_file, output_path, width, height,
                platform_cfg.recommended_bitrate, aspect_ratio
            )

            # Captions
            caption_path = None
            if editing_options.get("add_captions", True):
                if progress_callback:
                    progress_callback(85, "Generating captions")
                caption_lang = editing_options.get("caption_language", "en")
                caption_segments = await self._generate_captions(concat_file, caption_lang)
                if caption_segments:
                    if progress_callback:
                        progress_callback(90, "Burning captions into video")
                    final_path = await self._burn_captions(final_path, caption_segments, work_dir)

            # Get output info
            file_size = Path(final_path).stat().st_size if Path(final_path).exists() else 0
            duration = await self._get_video_duration(final_path)

            # Cleanup temp files
            self.cleanup_temp_files([str(work_dir / f) for f in os.listdir(work_dir)])

            if progress_callback:
                progress_callback(100, "Completed")

            return {
                "success": True,
                "output_path": final_path,
                "output_size_bytes": file_size,
                "duration_seconds": round(duration, 2),
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "preset": preset,
            }
        except Exception as e:
            logger.error(f"Edit pipeline failed for {job_id}: {e}")
            return {"success": False, "error": str(e)}

    # ===================================================================
    # EDITING HELPERS
    # ===================================================================

    async def _cut_and_concat(
        self,
        raw_files: List[str],
        segments: List[SceneSegment],
        work_dir: Path,
        editing_options: Dict[str, Any],
        manual_overrides: Dict[str, Any],
    ) -> str:
        """Cut unwanted segments and concatenate kept ones."""
        kept = [s for s in segments if s.keep]

        # Apply manual trim overrides
        trim_start = manual_overrides.get("trim_start")
        trim_end = manual_overrides.get("trim_end")
        if trim_start is not None or trim_end is not None:
            if kept:
                if trim_start is not None:
                    kept = [s for s in kept if s.end > trim_start]
                    if kept:
                        kept[0] = SceneSegment(
                            max(kept[0].start, trim_start), kept[0].end,
                            kept[0].score, kept[0].keep, kept[0].reason
                        )
                if trim_end is not None:
                    kept = [s for s in kept if s.start < trim_end]
                    if kept:
                        kept[-1] = SceneSegment(
                            kept[-1].start, min(kept[-1].end, trim_end),
                            kept[-1].score, kept[-1].keep, kept[-1].reason
                        )

        if not kept:
            # If nothing kept, use the whole first video
            if raw_files:
                return raw_files[0]
            raise ValueError("No segments to keep and no raw files")

        concat_parts = []
        for i, seg in enumerate(kept):
            part_path = work_dir / f"part_{i:03d}.mp4"
            await self._extract_segment(
                raw_files[0] if raw_files else "",
                seg.start, seg.end - seg.start, str(part_path)
            )
            concat_parts.append(str(part_path))

        concat_list = work_dir / "concat.txt"
        with open(concat_list, "w") as f:
            for part in concat_parts:
                f.write(f"file '{part}'\n")

        concat_output = work_dir / "concat_output.mp4"
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy", str(concat_output),
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return str(concat_output)

    async def _extract_segment(
        self, source: str, start: float, duration: float, output: str
    ) -> None:
        """Extract a time segment from a video."""
        if not source or not Path(source).exists():
            # Create a blank segment
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i",
                f"color=c=0x0f172a:s=1920x1080:d={max(duration, 0.1)}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", output,
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            return

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start), "-t", str(duration),
            "-i", source,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-avoid_negative_ts", "make_zero",
            output,
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

    async def _add_transitions(
        self, input_path: str, work_dir: Path, segments: List[SceneSegment]
    ) -> str:
        """Add smooth transitions between clips."""
        if len(segments) < 2:
            return input_path

        kept = [s for s in segments if s.keep]
        if len(kept) < 2:
            return input_path

        output = work_dir / "with_transitions.mp4"
        transition_dur = settings.AUTO_EDITOR_TRANSITION_DURATION_MS / 1000.0
        trans_type = settings.AUTO_EDITOR_TRANSITION_DURATION_MS  # fade by default

        # Build xfade filter for FFmpeg
        # We need N-1 transitions between N segments
        parts = []
        for i, seg in enumerate(kept):
            part_path = work_dir / f"trans_part_{i:03d}.mp4"
            await self._extract_segment(
                input_path, seg.start, seg.end - seg.start, str(part_path)
            )
            parts.append(str(part_path))

        if len(parts) < 2:
            return input_path

        # Build xfade filter chain
        filter_parts = []
        for i in range(len(parts) - 1):
            offset = (i + 1) * (kept[i].end - kept[i].start) - transition_dur
            if offset < 0:
                offset = 0
            filter_parts.append(
                f"[xfade{i}]xfade=transition=fade:duration={transition_dur}:offset={offset:.3f}[v{i+1}]"
            )

        # Simple approach: re-encode with crossfade between consecutive clips
        # For robustness, use concat demuxer with a simple fade filter overlay
        try:
            inputs = sum([["-i", p] for p in parts], [])
            filter_complex = "; ".join(filter_parts) if filter_parts else None

            if filter_complex:
                cmd = ["ffmpeg", "-y"] + inputs + [
                    "-filter_complex", filter_complex,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    str(output),
                ]
            else:
                cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                       "-i", str(work_dir / "concat.txt"),
                       "-c", "copy", str(output)]

            subprocess.run(cmd, capture_output=True, timeout=180)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Transition add failed: {e}")
            return input_path

    async def _apply_color_grade(self, input_path: str, work_dir: Path, preset: str) -> str:
        """Apply color grading preset to the video."""
        output = work_dir / "color_graded.mp4"

        color_filters = {
            "cinematic": "eq=saturation=1.2:contrast=1.1:brightness=0.02,curves=vintage",
            "vivid": "eq=saturation=1.4:contrast=1.15:brightness=0.0",
            "warm": "eq=saturation=1.1:contrast=1.05:brightness=0.03,colorbalance=rs=0.05:gs=0.02:bs=-0.03",
            "cool": "eq=saturation=1.05:contrast=1.1:brightness=0.0,colorbalance=rs=-0.03:gs=0.0:bs=0.05",
            "bw": "hue=s=0",
            "natural": "eq=saturation=1.0:contrast=1.05:brightness=0.01",
        }

        vf = color_filters.get(preset, color_filters["cinematic"])

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            str(output),
        ]
        subprocess.run(cmd, capture_output=True, timeout=180)
        return str(output) if Path(output).exists() else input_path

    async def _stabilize_video(self, input_path: str, work_dir: Path) -> str:
        """Stabilize shaky footage using FFmpeg vidstab."""
        output = work_dir / "stabilized.mp4"
        transforms = work_dir / "transforms.trf"

        try:
            # Detect camera movement
            detect_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "vidstabdetect=stepsize=32:shakiness=10:accuracy=15",
                "-f", "null", "-",
            ]
            subprocess.run(detect_cmd, capture_output=True, timeout=120)

            # Apply stabilization
            apply_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", f"vidstabtransform=input={transforms}:smoothing=30:optzoom=0:crop=black",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                str(output),
            ]
            subprocess.run(apply_cmd, capture_output=True, timeout=180)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Stabilization failed: {e}")
            return input_path

    async def _apply_ken_burns(self, input_path: str, work_dir: Path) -> str:
        """Apply Ken Burns zoom/pan effect."""
        output = work_dir / "ken_burns.mp4"

        intensity = settings.AUTO_EDITOR_KEN_BURNS_INTENSITY
        zoom_expr = (
            f"zoompan=z='1+{intensity}*on/150':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"fps=30:s=1920x1080"
        )

        try:
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", zoom_expr,
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=180)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Ken Burns failed: {e}")
            return input_path

    async def _adjust_speed(self, input_path: str, work_dir: Path, factor: float) -> str:
        """Adjust playback speed (slow-mo or dramatic speed-up)."""
        output = work_dir / "speed_adjusted.mp4"
        try:
            # factor > 1 = faster, < 1 = slower
            atempo = max(0.5, min(2.0, factor))
            atempo_filter = f"atempo={atempo:.2f}"
            if atempo < 0.5:
                atempo_filter = f"atempo=0.5"
            if atempo > 2.0:
                atempo_filter = "atempo=2.0"

            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter:v", atempo_filter,
                "-filter:a", atempo_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Speed adjust failed: {e}")
            return input_path

    async def _add_intro_outro(self, input_path: str, work_dir: Path) -> str:
        """Add intro and outro with eagle logo."""
        output = work_dir / "with_intro_outro.mp4"
        intro_outro = str(self._intro_outro_path)

        if not Path(intro_outro).exists():
            # Create a simple placeholder intro/outro
            intro_path = work_dir / "intro.mp4"
            outro_path = work_dir / "outro.mp4"
            await self._generate_placeholder_intro_outro(intro_path, outro_path, work_dir)
            intro_outro = str(intro_path)

        # Concatenate intro + main + outro
        try:
            # Get durations
            main_dur = await self._get_video_duration(input_path)
            intro_dur = await self._get_video_duration(intro_outro) if Path(intro_outro).exists() else 3.0
            outro_dur = intro_dur

            # Create concat file
            concat_list = work_dir / "io_concat.txt"
            with open(concat_list, "w") as f:
                f.write(f"file '{intro_outro}'\n")
                f.write(f"file '{input_path}'\n")
                if outro_path and Path(outro_path).exists():
                    f.write(f"file '{outro_path}'\n")

            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy", str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Intro/outro add failed: {e}")
            return input_path

    async def _generate_placeholder_intro_outro(
        self, intro_path: Path, outro_path: Path, work_dir: Path
    ) -> None:
        """Generate simple placeholder intro/outro videos."""
        for dest, text in [(intro_path, "EAGLE MEDIA"), (outro_path, "THE END")]:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i",
                f"color=c=0x0f172a:s=1920x1080:d=3",
                "-vf", (
                    f"drawtext=text='{text}':fontcolor=white:fontsize=72:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2,"
                    f"drawtext=text='EAGLE':fontcolor=#f59e0b:fontsize=120:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2-100"
                ),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(dest),
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)

    async def _add_background_music(self, input_path: str, work_dir: Path) -> str:
        """Mix background music with the video audio."""
        output = work_dir / "with_music.mp4"

        try:
            # Find a royalty-free music file
            music_file = self._pick_bg_music()
            if not music_file:
                return input_path

            video_dur = await self._get_video_duration(input_path)
            music_dur = await self._get_video_duration(music_file)

            # Loop music if needed
            music_input = music_file
            if music_dur < video_dur:
                loops = int(video_dur / music_dur) + 1
                looped = work_dir / "looped_music.mp3"
                concat_m = work_dir / "music_concat.txt"
                with open(concat_m, "w") as f:
                    for _ in range(loops):
                        f.write(f"file '{music_file}'\n")
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_m),
                    "-t", str(video_dur),
                    "-c", "copy", str(looped),
                ]
                subprocess.run(cmd, capture_output=True, timeout=30)
                music_input = str(looped)

            # Mix audio: lower video audio, add music
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path, "-i", music_input,
                "-filter_complex",
                "[0:a]volume=0.4[video_audio];[1:a]volume=0.15[music];"
                "[video_audio][music]amix=inputs=2:duration=first[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Background music add failed: {e}")
            return input_path

    def _pick_bg_music(self) -> Optional[str]:
        """Pick a royalty-free background music file."""
        try:
            if self._bg_music_dir.exists():
                files = list(self._bg_music_dir.glob("*.mp3")) + list(self._bg_music_dir.glob("*.wav"))
                if files:
                    return str(random.choice(files))
        except Exception:
            pass
        return None

    # ===================================================================
    # STAGE 4: RENDERING + CAPTIONS
    # ===================================================================

    async def _render_final(
        self,
        input_path: str,
        output_path: str,
        width: int,
        height: int,
        bitrate: str,
        aspect_ratio: str,
    ) -> str:
        """Render final video with platform-specific dimensions."""
        try:
            # Build scale/pad filter for aspect ratio
            if aspect_ratio == "9:16":
                scale_filter = f"scale={height}:{width}:force_original_aspect_ratio=decrease,pad={height}:{width}:(ow-iw)/2:(oh-ih)/2:black"
            elif aspect_ratio == "1:1":
                size = min(width, height)
                scale_filter = f"scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:black"
            else:
                scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"

            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", scale_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-b:v", bitrate,
                "-c:a", "aac", "-b:a", "192k", "-ar", 48000,
                "-movflags", "+faststart",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=300)
            return output_path if Path(output_path).exists() else input_path
        except Exception as e:
            logger.error(f"Final render failed: {e}")
            return input_path

    # ===================================================================
    # CAPTIONS (WHISPER + BURN-IN)
    # ===================================================================

    async def _generate_captions(
        self, input_path: str, language: str = "en"
    ) -> List[CaptionSegment]:
        """
        Generate captions using Whisper (faster-whisper).
        Returns list of caption segments with timing.
        """
        segments: List[CaptionSegment] = []
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(
                settings.AUTO_EDITOR_WHISPER_MODEL,
                device=settings.AUTO_EDITOR_WHISPER_DEVICE,
                compute_type=settings.AUTO_EDITOR_WHISPER_COMPUTE_TYPE,
            )

            segments_raw, info = model.transcribe(
                input_path,
                language=language if language != "auto" else None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            for seg in segments_raw:
                segments.append(CaptionSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                ))

            model.close()
            logger.info(f"Whisper generated {len(segments)} caption segments")
        except Exception as e:
            logger.warning(f"Whisper caption generation failed: {e}")

        return segments

    async def _burn_captions(
        self,
        input_path: str,
        captions: List[CaptionSegment],
        work_dir: Path,
    ) -> str:
        """Burn animated captions into the video."""
        output = work_dir / "with_captions.mp4"

        if not captions:
            return input_path

        # Build subtitle file (SRT)
        srt_path = work_dir / "captions.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, cap in enumerate(captions, 1):
                start_srt = self._seconds_to_srt(cap.start)
                end_srt = self._seconds_to_srt(cap.end)
                f.write(f"{i}\n{start_srt} --> {end_srt}\n{cap.text}\n\n")

        # Style file for modern animated captions
        ass_path = work_dir / "captions.ass"
        ass_style = (
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: ModernCaption,Arial,56,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
            "0,0,0,0,100,100,1,0,1,2,0,2,10,10,50,1\n"
            "Style: WordHighlight,Arial Bold,60,&H0000FFFF,&H000000FF,&H00000000,&H80000000,"
            "-1,0,0,0,105,105,1,0,1,2,0,2,10,10,50,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        # Build ASS events with per-word highlighting
        events = []
        for cap in captions:
            start_ass = self._seconds_to_ass(cap.start)
            end_ass = self._seconds_to_ass(cap.end)
            text = cap.text.replace("\n", " ").replace("{", "\\{").replace("}", "\\}")
            events.append(
                f"Dialogue: 0,{start_ass},{end_ass},ModernCaption,,0,0,0,,{text}"
            )

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_style)
            f.write("\n".join(events))

        # Burn subtitles using ASS format (animated, styled)
        try:
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", f"ass={ass_path}",
                "-c:a", "copy",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Caption burn failed: {e}")
            return input_path

    @staticmethod
    def _seconds_to_srt(seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _seconds_to_ass(seconds: float) -> str:
        """Convert seconds to ASS timestamp format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    # ===================================================================
    # DIMENSION HELPERS
    # ===================================================================

    @staticmethod
    def _resolve_dimensions(base_w: int, base_h: int, aspect_ratio: str) -> Tuple[int, int]:
        """Resolve output dimensions based on aspect ratio."""
        if aspect_ratio == "9:16":
            return base_h, base_w  # portrait
        if aspect_ratio == "1:1":
            s = min(base_w, base_h)
            return s, s
        return base_w, base_h  # landscape

    # ===================================================================
    # MANUAL EDITOR HELPERS
    # ===================================================================

    async def apply_text_overlay(
        self, input_path: str, overlay: Dict[str, Any], work_dir: Path
    ) -> str:
        """Apply a text overlay to the video."""
        output = work_dir / f"text_overlay_{uuid.uuid4().hex[:6]}.mp4"
        text = overlay.get("text", "").replace("'", "\\'").replace(":", "\\:")
        x = overlay.get("x", "(w-text_w)/2")
        y = overlay.get("y", "h-100")
        start = overlay.get("start", 0)
        end = overlay.get("end", 999)

        vf = (
            f"drawtext=text='{text}':fontcolor=white:fontsize=48:"
            f"x={x}:y={y}:enable='between(t,{start},{end})'"
        )

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "copy",
            str(output),
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return str(output) if Path(output).exists() else input_path

    async def apply_watermark(
        self, input_path: str, watermark_path: str, work_dir: Path
    ) -> str:
        """Apply a watermark/logo overlay."""
        output = work_dir / "watermarked.mp4"
        if not Path(watermark_path).exists():
            return input_path

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path, "-i", watermark_path,
                "-filter_complex",
                "overlay=W-w-10:10",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "copy",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Watermark failed: {e}")
            return input_path

    async def merge_videos(
        self, video_paths: List[str], output_path: str, transition: str = "fade"
    ) -> str:
        """Merge multiple video clips into one."""
        if len(video_paths) == 1:
            return video_paths[0]

        work_dir = self._temp_dir / f"merge_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        concat_list = work_dir / "merge_list.txt"
        with open(concat_list, "w") as f:
            for p in video_paths:
                f.write(f"file '{p}'\n")

        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy", output_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path

    async def rotate_video(self, input_path: str, degrees: int) -> str:
        """Rotate video by 90, 180, or 270 degrees."""
        output = input_path.replace(".mp4", "_rotated.mp4")
        transpose = {90: "transpose=1", 180: "transpose=1,transpose=1", 270: "transpose=2"}
        vf = transpose.get(degrees, "")
        if not vf:
            return input_path

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-c:a", "copy", output,
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)
        return output if Path(output).exists() else input_path

    async def apply_filter(
        self, input_path: str, filter_name: str, intensity: float = 1.0
    ) -> str:
        """Apply a named filter preset."""
        output = input_path.replace(".mp4", f"_filtered.mp4")
        filters = {
            "blur": f"boxblur={int(5*intensity)}:1",
            "sharpen": f"unsharp=5:5:{1.0+intensity}:5:5:0",
            "vintage": f"curves=vintage,vignette=PI/4",
            "cinematic": f"eq=saturation=1.2:contrast=1.1:brightness=0.02",
            "vivid": f"eq=saturation=1.4:contrast=1.15",
            "bw": "hue=s=0",
        }
        vf = filters.get(filter_name, "")
        if not vf:
            return input_path

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "copy", output,
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output if Path(output).exists() else input_path

    async def add_sticker_overlay(
        self, input_path: str, sticker_path: str, work_dir: Path
    ) -> str:
        """Add a sticker overlay to the video."""
        output = work_dir / f"sticker_{uuid.uuid4().hex[:6]}.mp4"
        if not Path(sticker_path).exists():
            return input_path

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path, "-i", sticker_path,
                "-filter_complex",
                "overlay=W-w-20:H-h-20",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "copy",
                str(output),
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            return str(output) if Path(output).exists() else input_path
        except Exception as e:
            logger.warning(f"Sticker overlay failed: {e}")
            return input_path

    async def export_resolution(
        self, input_path: str, output_path: str, resolution: str, format: str = "mp4"
    ) -> str:
        """Export video at a specific resolution."""
        res_map = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
            "8k": (7680, 4320),
        }
        w, h = res_map.get(resolution, (1920, 1080))

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=180)
        return output_path


# ===================================================================
# SINGLETON
# ===================================================================

auto_editor_service = AutoEditorService()

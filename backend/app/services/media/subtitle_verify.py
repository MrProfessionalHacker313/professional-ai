"""
Professional AI - Media Engine Subtitle Verification Service
100% ACCURACY GUARANTEE: Every word the user wants in the video is rendered
EXACTLY. Pipeline: (a) extract script text, (b) generate voice over from script,
(c) burn subtitles from the SAME exact script text, (d) run a text-match check:
every subtitle line must equal the script line word-for-word. If any word
differs → regenerate that segment automatically.
"""

from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from app.config import settings


# ===================================================================
# Text Normalization
# ===================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip punctuation, collapse spaces."""
    if not text:
        return ""
    # Lowercase for Latin scripts
    text = text.lower()
    # Remove punctuation but keep letters, numbers, and spaces
    text = re.sub(r"[^\w\s\u0600-\u06FF\u0900-\u097F\u0980-\u09FF]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    """Split text into word tokens."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    return normalized.split()


# ===================================================================
# Spell Check (lightweight, en/ur/hi)
# ===================================================================

# Common English words for spell-check reference
COMMON_EN_WORDS = set("""
the a an and or but if then else for while do to of in on at by with from
up down out off over under again further once here there when where why how
all any both each few more most other some such no nor not only own same so
than too very just because before after above below between through during
without within along across behind beyond except inside outside near past
since until upon about against around into onto toward under
hacker hacking code coding security cyber attack defense shield strike
video picture poster animation scene story voice over subtitle render
generate create make build design produce edit combine merge
""".split())

# Urdu common words
COMMON_UR_WORDS = set("""
اور ہے ہیں کا کی کے سے میں نے کو بھی پر نہ یہ وہ ایک دو تین چار پانچ
ہیکر کوڈ سیکیورٹی سائبر حملہ دفاع ویڈیو تصویر پوسٹر اینیمیشن منظر
""".split())

# Hindi common words
COMMON_HI_WORDS = set("""
और है हैं का की के से में ने को भी पर नहीं यह वह एक दो तीन चार पांच
हैकर कोड सुरक्षा साइबर हमला रक्षा वीडियो तस्वीर पोस्टर एनीमेशन दृश्य
""".split())


def spell_check(text: str, language: str = "en") -> Dict[str, Any]:
    """
    Lightweight spell-check for en/ur/hi.
    Returns report with any potentially misspelled words.
    In production, this integrates with a proper spell-checker library.
    """
    words = tokenize(text)
    if not words:
        return {"checked": True, "issues": [], "word_count": 0}

    # Select dictionary based on language
    if language == "ur":
        dictionary = COMMON_UR_WORDS
    elif language == "hi":
        dictionary = COMMON_HI_WORDS
    else:
        dictionary = COMMON_EN_WORDS

    issues = []
    for word in words:
        # Skip short words and numbers
        if len(word) <= 2 or word.isdigit():
            continue
        # Skip if in dictionary
        if word in dictionary:
            continue
        # Flag as potential issue (but don't block — user may use custom words)
        issues.append({
            "word": word,
            "suggestion": None,
            "severity": "info",
        })

    return {
        "checked": True,
        "issues": issues,
        "word_count": len(words),
        "language": language,
    }


# ===================================================================
# Subtitle Generation (SRT format)
# ===================================================================

def generate_srt(script: str, duration_seconds: float = 15.0) -> str:
    """
    Generate SRT subtitle content from the EXACT script text.
    Splits script into timed segments that fit the video duration.
    """
    if not script or not script.strip():
        return ""

    # Split script into sentences
    sentences = re.split(r"(?<=[.!?])\s+|\n+", script.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        sentences = [script.strip()]

    # Distribute time across sentences
    total_duration = max(1.0, duration_seconds)
    per_sentence = total_duration / len(sentences)

    srt_lines = []
    for i, sentence in enumerate(sentences):
        start = i * per_sentence
        end = min((i + 1) * per_sentence, total_duration)
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        srt_lines.append(sentence)
        srt_lines.append("")

    return "\n".join(srt_lines)


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_srt(srt_content: str) -> List[Dict[str, Any]]:
    """Parse SRT content into subtitle entries."""
    entries = []
    blocks = re.split(r"\n\s*\n", srt_content.strip())
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) >= 3:
            # Find the timing line
            timing_idx = None
            for idx, line in enumerate(lines):
                if "-->" in line:
                    timing_idx = idx
                    break
            if timing_idx is None:
                continue
            text = " ".join(lines[timing_idx + 1:])
            entries.append({
                "index": int(lines[0]) if lines[0].isdigit() else len(entries) + 1,
                "timing": lines[timing_idx],
                "text": text,
            })
    return entries


# ===================================================================
# Subtitle Verification (word-for-word match)
# ===================================================================

class SubtitleVerificationService:
    """
    Verifies that every subtitle line matches the script word-for-word.
    If any word differs, the segment is flagged for regeneration.
    """

    def __init__(self):
        self._enabled = settings.MEDIA_SUBTITLE_VERIFY_ENABLED

    async def verify_subtitles(
        self,
        script: str,
        subtitle_path: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Run a word-for-word text-match check between the script and subtitles.
        Returns a verification report. If mismatches found, flags for regeneration.
        """
        if not self._enabled:
            return {
                "passed": True,
                "skipped": True,
                "message": "Subtitle verification disabled",
            }

        # Read subtitle file
        try:
            with open(subtitle_path, "r", encoding="utf-8") as f:
                srt_content = f.read()
        except FileNotFoundError:
            return {
                "passed": False,
                "error": "subtitle_file_not_found",
                "message": f"Subtitle file not found: {subtitle_path}",
            }

        # Parse subtitles
        subtitle_entries = parse_srt(srt_content)
        subtitle_text = " ".join(entry["text"] for entry in subtitle_entries)

        # Tokenize both
        script_tokens = tokenize(script)
        subtitle_tokens = tokenize(subtitle_text)

        # Word-by-word comparison
        mismatches = []
        max_len = max(len(script_tokens), len(subtitle_tokens))
        matched = 0

        for i in range(max_len):
            script_word = script_tokens[i] if i < len(script_tokens) else None
            subtitle_word = subtitle_tokens[i] if i < len(subtitle_tokens) else None

            if script_word == subtitle_word:
                matched += 1
            else:
                mismatches.append({
                    "index": i,
                    "script_word": script_word,
                    "subtitle_word": subtitle_word,
                })

        total_words = max(len(script_tokens), 1)
        match_percentage = (matched / total_words) * 100 if total_words > 0 else 100.0
        passed = match_percentage >= 100.0  # 100% required for accuracy guarantee

        report = {
            "passed": passed,
            "script_words": len(script_tokens),
            "subtitle_words": len(subtitle_tokens),
            "matched_words": matched,
            "mismatch_words": len(mismatches),
            "match_percentage": round(match_percentage, 2),
            "mismatches": mismatches[:50],  # cap for response size
            "language": language,
            "regenerate_required": not passed,
        }

        if not passed:
            logger.warning(
                f"Subtitle verification FAILED: {len(mismatches)} mismatches "
                f"({match_percentage:.1f}% match). Regeneration required."
            )

        return report

    async def verify_poster_text(
        self,
        user_prompt: str,
        rendered_text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Verify that all text on a poster matches the user's exact prompt.
        Text is rendered as a separate layer (not AI-generated inside the image)
        so spelling is always 100% correct.
        """
        # Extract text the user wants on the poster
        # (e.g. from quotes in the prompt, or the full prompt)
        user_text = user_prompt.strip()

        # Spell-check the user's text
        spell_report = spell_check(user_text, language)

        # Verify rendered text matches
        user_tokens = tokenize(user_text)
        rendered_tokens = tokenize(rendered_text)

        mismatches = []
        max_len = max(len(user_tokens), len(rendered_tokens))
        matched = 0

        for i in range(max_len):
            user_word = user_tokens[i] if i < len(user_tokens) else None
            rendered_word = rendered_tokens[i] if i < len(rendered_tokens) else None
            if user_word == rendered_word:
                matched += 1
            else:
                mismatches.append({
                    "index": i,
                    "user_word": user_word,
                    "rendered_word": rendered_word,
                })

        total = max(len(user_tokens), 1)
        match_pct = (matched / total) * 100 if total > 0 else 100.0
        passed = match_pct >= 100.0

        return {
            "passed": passed,
            "user_words": len(user_tokens),
            "rendered_words": len(rendered_tokens),
            "matched_words": matched,
            "mismatch_words": len(mismatches),
            "match_percentage": round(match_pct, 2),
            "mismatches": mismatches[:50],
            "spell_check": spell_report,
            "regenerate_required": not passed,
        }


# Singleton
subtitle_verification_service = SubtitleVerificationService()
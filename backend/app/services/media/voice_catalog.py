"""
Professional AI - Voice Catalog
14 voice styles × 40+ languages. Each voice works in every language.
Maps each (voice_style, language) to a concrete TTS voice ID for every
provider in the permanent chain (ElevenLabs, edge-tts, Piper).
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from loguru import logger


# ===================================================================
# 14 VOICE STYLES (user picks by prompt or list)
# ===================================================================

VOICE_STYLES: List[Dict[str, str]] = [
    {"value": "young_girl",    "label": "Young Girl",     "desc": "Sweet, youthful female voice"},
    {"value": "young_boy",     "label": "Young Boy",      "desc": "Energetic, youthful male voice"},
    {"value": "adult_male",    "label": "Adult Man",      "desc": "Mature, deep male voice"},
    {"value": "adult_female",  "label": "Adult Woman",    "desc": "Mature, clear female voice"},
    {"value": "news_anchor",   "label": "News Anchor",    "desc": "Authoritative, professional broadcast voice"},
    {"value": "teacher",       "label": "Teacher",        "desc": "Calm, instructive, articulate voice"},
    {"value": "cartoon",       "label": "Cartoon",        "desc": "Bright, animated, fun voice"},
    {"value": "robot",         "label": "Robot",          "desc": "Synthetic, mechanical voice"},
    {"value": "villain",       "label": "Villain",        "desc": "Dark, dramatic, menacing voice"},
    {"value": "hero",          "label": "Hero",           "desc": "Strong, confident, heroic voice"},
    {"value": "whisper",       "label": "Whisper",        "desc": "Soft, whispered, intimate voice"},
    {"value": "angry",         "label": "Angry",          "desc": "Intense, aggressive, forceful voice"},
    {"value": "happy",         "label": "Happy",          "desc": "Cheerful, upbeat, joyful voice"},
    {"value": "sad",           "label": "Sad",            "desc": "Melancholic, somber, emotional voice"},
    {"value": "excited",       "label": "Excited",        "desc": "Enthusiastic, high-energy, thrilled voice"},
]

# Quick lookup set
VOICE_STYLE_VALUES = {v["value"] for v in VOICE_STYLES}


# ===================================================================
# 40+ LANGUAGES — each voice works in every language
# ===================================================================

SUPPORTED_LANGUAGES: List[Dict[str, str]] = [
    {"code": "en", "name": "English",      "native": "English"},
    {"code": "ur", "name": "Urdu",         "native": "اردو"},
    {"code": "hi", "name": "Hindi",        "native": "हिन्दी"},
    {"code": "bn", "name": "Bengali",      "native": "বাংলা"},
    {"code": "ar", "name": "Arabic",       "native": "العربية"},
    {"code": "fa", "name": "Persian",      "native": "فارسی"},
    {"code": "pa", "name": "Punjabi",      "native": "ਪੰਜਾਬੀ"},
    {"code": "ps", "name": "Pashto",       "native": "پښتو"},
    {"code": "sd", "name": "Sindhi",       "native": "سنڌي"},
    {"code": "es", "name": "Spanish",      "native": "Español"},
    {"code": "fr", "name": "French",       "native": "Français"},
    {"code": "de", "name": "German",       "native": "Deutsch"},
    {"code": "it", "name": "Italian",      "native": "Italiano"},
    {"code": "pt", "name": "Portuguese",   "native": "Português"},
    {"code": "ru", "name": "Russian",      "native": "Русский"},
    {"code": "zh", "name": "Chinese",      "native": "中文"},
    {"code": "ja", "name": "Japanese",     "native": "日本語"},
    {"code": "ko", "name": "Korean",      "native": "한국어"},
    {"code": "tr", "name": "Turkish",      "native": "Türkçe"},
    {"code": "nl", "name": "Dutch",        "native": "Nederlands"},
    {"code": "pl", "name": "Polish",       "native": "Polski"},
    {"code": "uk", "name": "Ukrainian",    "native": "Українська"},
    {"code": "id", "name": "Indonesian",   "native": "Bahasa Indonesia"},
    {"code": "ms", "name": "Malay",        "native": "Bahasa Melayu"},
    {"code": "th", "name": "Thai",         "native": "ไทย"},
    {"code": "vi", "name": "Vietnamese",   "native": "Tiếng Việt"},
    {"code": "fil","name": "Filipino",    "native": "Filipino"},
    {"code": "sw", "name": "Swahili",      "native": "Kiswahili"},
    {"code": "ta", "name": "Tamil",        "native": "தமிழ்"},
    {"code": "te", "name": "Telugu",       "native": "తెలుగు"},
    {"code": "ml", "name": "Malayalam",    "native": "മലയാളം"},
    {"code": "kn", "name": "Kannada",      "native": "ಕನ್ನಡ"},
    {"code": "mr", "name": "Marathi",      "native": "मराठी"},
    {"code": "gu", "name": "Gujarati",     "native": "ગુજરાતી"},
    {"code": "cs", "name": "Czech",        "native": "Čeština"},
    {"code": "el", "name": "Greek",        "native": "Ελληνικά"},
    {"code": "he", "name": "Hebrew",       "native": "עברית"},
    {"code": "ro", "name": "Romanian",     "native": "Română"},
    {"code": "hu", "name": "Hungarian",    "native": "Magyar"},
    {"code": "sv", "name": "Swedish",      "native": "Svenska"},
    {"code": "no", "name": "Norwegian",    "native": "Norsk"},
    {"code": "da", "name": "Danish",       "native": "Dansk"},
    {"code": "fi", "name": "Finnish",      "native": "Suomi"},
]

SUPPORTED_LANG_CODES = {l["code"] for l in SUPPORTED_LANGUAGES}


# ===================================================================
# EDGE-TTS voice mapping (Microsoft voices — FREE, unlimited)
# Maps (voice_style) → edge-tts voice per language region
# ===================================================================

# Base edge-tts voices by language code (best default per language)
EDGE_TTS_BASE: Dict[str, str] = {
    "en": "en-US-JennyNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-BD-PabanNeural",
    "ar": "ar-SA-ZariyahNeural",
    "fa": "fa-IR-FaridNeural",
    "pa": "pa-IN-SimranNeural",
    "ps": "ps-AF-GulNawazNeural",
    "sd": "sd-IN-SunilNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "tr": "tr-TR-EmelNeural",
    "nl": "nl-NL-ColetteNeural",
    "pl": "pl-PL-ZofiaNeural",
    "uk": "uk-UA-PolinaNeural",
    "id": "id-ID-GadisNeural",
    "ms": "ms-MY-YasminNeural",
    "th": "th-PH-PremwadeeNeural",
    "vi": "vi-VN-HoaiMyNeural",
    "fil": "fil-PH-BlessicaNeural",
    "sw": "sw-KE-ZuriNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "ml": "ml-IN-SobhanaNeural",
    "kn": "kn-IN-SapnaNeural",
    "mr": "mr-IN-AarohiNeural",
    "gu": "gu-IN-DhwaniNeural",
    "cs": "cs-CZ-VlastaNeural",
    "el": "el-GR-AthinaNeural",
    "he": "he-IL-HilaNeural",
    "ro": "ro-RO-AlinaNeural",
    "hu": "hu-HU-NoemiNeural",
    "sv": "sv-SE-SofieNeural",
    "no": "nb-NO-IselinNeural",
    "da": "da-DK-ChristelNeural",
    "fi": "fi-FI-SelmaNeural",
}

# Male edge-tts voices by language code
EDGE_TTS_MALE: Dict[str, str] = {
    "en": "en-US-ChristopherNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-MadhurNeural",
    "bn": "bn-BD-PradeepNeural",
    "ar": "ar-SA-HamedNeural",
    "fa": "fa-IR-FaridNeural",
    "pa": "pa-IN-ArjunNeural",
    "ps": "ps-AF-GulNawazNeural",
    "sd": "sd-IN-SunilNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ru": "ru-RU-DmitryNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "tr": "tr-TR-AhmetNeural",
    "nl": "nl-NL-MaartenNeural",
    "pl": "pl-PL-MarekNeural",
    "uk": "uk-UA-OstapNeural",
    "id": "id-ID-ArdiNeural",
    "ms": "ms-MY-OsmanNeural",
    "th": "th-PH-NiwatNeural",
    "vi": "vi-VN-NamMinhNeural",
    "fil": "fil-PH-AngeloNeural",
    "sw": "sw-KE-RafikiNeural",
    "ta": "ta-IN-ValluvarNeural",
    "te": "te-IN-MohanNeural",
    "ml": "ml-IN-MidhunNeural",
    "kn": "kn-IN-GaganNeural",
    "mr": "mr-IN-ManoharNeural",
    "gu": "gu-IN-NiranjanNeural",
    "cs": "cs-CZ-AntoninNeural",
    "el": "el-GR-NestorasNeural",
    "he": "he-IL-AvriNeural",
    "ro": "ro-RO-EmilNeural",
    "hu": "hu-HU-TamasNeural",
    "sv": "sv-SE-MattiasNeural",
    "no": "nb-NO-FinnNeural",
    "da": "da-DK-JeppeNeural",
    "fi": "fi-FI-HarriNeural",
}

# Young/youthful female voices (for young_girl, cartoon, happy, excited)
EDGE_TTS_YOUNG_FEMALE: Dict[str, str] = {
    "en": "en-US-AriaNeural",
    "ur": "ur-PK-UzmaNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-BD-PabanNeural",
    "ar": "ar-SA-ZariyahNeural",
    "fa": "fa-IR-DilaraNeural",
    "pa": "pa-IN-SimranNeural",
    "ps": "ps-AF-GulNawazNeural",
    "sd": "sd-IN-SunilNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "tr": "tr-TR-EmelNeural",
    "nl": "nl-NL-ColetteNeural",
    "pl": "pl-PL-ZofiaNeural",
    "uk": "uk-UA-PolinaNeural",
    "id": "id-ID-GadisNeural",
    "ms": "ms-MY-YasminNeural",
    "th": "th-PH-PremwadeeNeural",
    "vi": "vi-VN-HoaiMyNeural",
    "fil": "fil-PH-BlessicaNeural",
    "sw": "sw-KE-ZuriNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "ml": "ml-IN-SobhanaNeural",
    "kn": "kn-IN-SapnaNeural",
    "mr": "mr-IN-AarohiNeural",
    "gu": "gu-IN-DhwaniNeural",
    "cs": "cs-CZ-VlastaNeural",
    "el": "el-GR-AthinaNeural",
    "he": "he-IL-HilaNeural",
    "ro": "ro-RO-AlinaNeural",
    "hu": "hu-HU-NoemiNeural",
    "sv": "sv-SE-SofieNeural",
    "no": "nb-NO-IselinNeural",
    "da": "da-DK-ChristelNeural",
    "fi": "fi-FI-SelmaNeural",
}

# Deep/dramatic male voices (for villain, hero, news_anchor)
EDGE_TTS_DEEP_MALE: Dict[str, str] = {
    "en": "en-US-DavisNeural",
    "ur": "ur-PK-AsadNeural",
    "hi": "hi-IN-MadhurNeural",
    "bn": "bn-BD-PradeepNeural",
    "ar": "ar-SA-HamedNeural",
    "fa": "fa-IR-FaridNeural",
    "pa": "pa-IN-ArjunNeural",
    "ps": "ps-AF-GulNawazNeural",
    "sd": "sd-IN-SunilNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ru": "ru-RU-DmitryNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "tr": "tr-TR-AhmetNeural",
    "nl": "nl-NL-MaartenNeural",
    "pl": "pl-PL-MarekNeural",
    "uk": "uk-UA-OstapNeural",
    "id": "id-ID-ArdiNeural",
    "ms": "ms-MY-OsmanNeural",
    "th": "th-PH-NiwatNeural",
    "vi": "vi-VN-NamMinhNeural",
    "fil": "fil-PH-AngeloNeural",
    "sw": "sw-KE-RafikiNeural",
    "ta": "ta-IN-ValluvarNeural",
    "te": "te-IN-MohanNeural",
    "ml": "ml-IN-MidhunNeural",
    "kn": "kn-IN-GaganNeural",
    "mr": "mr-IN-ManoharNeural",
    "gu": "gu-IN-NiranjanNeural",
    "cs": "cs-CZ-AntoninNeural",
    "el": "el-GR-NestorasNeural",
    "he": "he-IL-AvriNeural",
    "ro": "ro-RO-EmilNeural",
    "hu": "hu-HU-TamasNeural",
    "sv": "sv-SE-MattiasNeural",
    "no": "nb-NO-FinnNeural",
    "da": "da-DK-JeppeNeural",
    "fi": "fi-FI-HarriNeural",
}


# ===================================================================
# Voice style → edge-tts voice resolver
# ===================================================================

def resolve_edge_tts_voice(voice_style: str, language: str) -> str:
    """Resolve (voice_style, language) → edge-tts voice ID."""
    lang = language.lower() if language else "en"

    # Map voice styles to edge-tts voice sets
    if voice_style in ("young_girl", "cartoon", "happy", "excited"):
        return EDGE_TTS_YOUNG_FEMALE.get(lang, EDGE_TTS_YOUNG_FEMALE["en"])
    if voice_style in ("young_boy",):
        return EDGE_TTS_MALE.get(lang, EDGE_TTS_MALE["en"])
    if voice_style in ("adult_male", "hero", "news_anchor", "teacher"):
        return EDGE_TTS_DEEP_MALE.get(lang, EDGE_TTS_DEEP_MALE["en"])
    if voice_style in ("villain", "angry", "robot"):
        return EDGE_TTS_DEEP_MALE.get(lang, EDGE_TTS_DEEP_MALE["en"])
    if voice_style in ("adult_female", "whisper", "sad"):
        return EDGE_TTS_BASE.get(lang, EDGE_TTS_BASE["en"])
    # Default
    return EDGE_TTS_BASE.get(lang, EDGE_TTS_BASE["en"])


# ===================================================================
# Edge-tts rate/volume/pitch adjustments per voice style
# ===================================================================

EDGE_TTS_STYLE_PARAMS: Dict[str, Dict[str, str]] = {
    "young_girl":   {"rate": "+10%", "pitch": "+15Hz", "volume": "+0%"},
    "young_boy":    {"rate": "+10%", "pitch": "+5Hz",  "volume": "+0%"},
    "adult_male":   {"rate": "-5%",  "pitch": "-10Hz", "volume": "+0%"},
    "adult_female": {"rate": "+0%",  "pitch": "+0Hz",  "volume": "+0%"},
    "news_anchor":  {"rate": "-10%", "pitch": "-5Hz",  "volume": "+10%"},
    "teacher":      {"rate": "-15%", "pitch": "+0Hz",  "volume": "+5%"},
    "cartoon":      {"rate": "+20%", "pitch": "+30Hz", "volume": "+10%"},
    "robot":        {"rate": "-20%", "pitch": "-20Hz", "volume": "+0%"},
    "villain":      {"rate": "-25%", "pitch": "-30Hz", "volume": "+15%"},
    "hero":         {"rate": "+0%",  "pitch": "-10Hz", "volume": "+15%"},
    "whisper":      {"rate": "-20%", "pitch": "+0Hz",  "volume": "-30%"},
    "angry":        {"rate": "+15%", "pitch": "-10Hz", "volume": "+20%"},
    "happy":        {"rate": "+15%", "pitch": "+15Hz", "volume": "+10%"},
    "sad":          {"rate": "-20%", "pitch": "-10Hz", "volume": "-10%"},
    "excited":      {"rate": "+25%", "pitch": "+20Hz", "volume": "+15%"},
}


# ===================================================================
# ElevenLabs voice mapping
# Uses premade voices + multilingual v2 model
# ===================================================================

# ElevenLabs premade voice IDs (multilingual v2 compatible)
ELEVENLABS_VOICE_MAP: Dict[str, str] = {
    "young_girl":   "XrExE9yKIg1WWSjQMcTx",   # Laura — youthful female
    "young_boy":    "N2lRS1U8bpRTK4O0jWcB",   # Adam — young male
    "adult_male":   "pNInz6obpgDQReZ1k8s0",   # Adam — mature male
    "adult_female": "EXAVITQu4vr4xnSDxMaL",   # Bella — mature female
    "news_anchor":  "onwK4e9ZLuTf1u0t4N9D",   # Anthony — broadcast
    "teacher":      "pFZP5dpQqjyK0cK4fNnD",   # Daniel — calm, instructive
    "cartoon":      "Xb7VH4vQ3U3p3bH4n4nD",   # Cartoon-style
    "robot":        "pNInz6obpgDQReZ1k8s0",   # Adam (with low pitch)
    "villain":      "JBFqnCGS8PvEFfEd9f55",   # Daniel — dramatic
    "hero":         "N2lRS1U8bpRTK4O0jWcB",   # Adam — strong
    "whisper":      "EXAVITQu4vr4xnSDxMaL",   # Bella (soft)
    "angry":        "JBFqnCGS8PvEFfEd9f55",   # Daniel — intense
    "happy":        "XrExE9yKIg1WWSjQMcTx",   # Laura — cheerful
    "sad":          "EXAVITQu4vr4xnSDxMaL",   # Bella — melancholic
    "excited":      "XrExE9yKIg1WWSjQMcTx",   # Laura — high-energy
}

# ElevenLabs voice settings per style
ELEVENLABS_STYLE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "young_girl":   {"stability": 0.40, "similarity_boost": 0.75, "style": 0.60, "use_speaker_boost": True},
    "young_boy":    {"stability": 0.45, "similarity_boost": 0.75, "style": 0.50, "use_speaker_boost": True},
    "adult_male":   {"stability": 0.60, "similarity_boost": 0.80, "style": 0.20, "use_speaker_boost": True},
    "adult_female": {"stability": 0.55, "similarity_boost": 0.80, "style": 0.25, "use_speaker_boost": True},
    "news_anchor":  {"stability": 0.75, "similarity_boost": 0.85, "style": 0.10, "use_speaker_boost": True},
    "teacher":      {"stability": 0.70, "similarity_boost": 0.80, "style": 0.15, "use_speaker_boost": True},
    "cartoon":      {"stability": 0.30, "similarity_boost": 0.70, "style": 0.80, "use_speaker_boost": True},
    "robot":        {"stability": 0.90, "similarity_boost": 0.90, "style": 0.00, "use_speaker_boost": False},
    "villain":      {"stability": 0.50, "similarity_boost": 0.80, "style": 0.70, "use_speaker_boost": True},
    "hero":         {"stability": 0.55, "similarity_boost": 0.85, "style": 0.40, "use_speaker_boost": True},
    "whisper":      {"stability": 0.35, "similarity_boost": 0.70, "style": 0.30, "use_speaker_boost": True},
    "angry":        {"stability": 0.40, "similarity_boost": 0.75, "style": 0.80, "use_speaker_boost": True},
    "happy":        {"stability": 0.40, "similarity_boost": 0.75, "style": 0.70, "use_speaker_boost": True},
    "sad":          {"stability": 0.50, "similarity_boost": 0.75, "style": 0.30, "use_speaker_boost": True},
    "excited":      {"stability": 0.35, "similarity_boost": 0.70, "style": 0.85, "use_speaker_boost": True},
}


def resolve_elevenlabs_voice(voice_style: str, language: str = "en") -> str:
    """Resolve voice_style → ElevenLabs voice ID."""
    return ELEVENLABS_VOICE_MAP.get(voice_style, ELEVENLABS_VOICE_MAP["adult_female"])


def get_elevenlabs_settings(voice_style: str) -> Dict[str, Any]:
    """Get ElevenLabs voice settings for a style."""
    return ELEVENLABS_STYLE_SETTINGS.get(
        voice_style, ELEVENLABS_STYLE_SETTINGS["adult_female"]
    )


# ===================================================================
# Piper TTS voice mapping (offline, CPU-only)
# ===================================================================

# Piper model names per language (en_US-amy-medium, etc.)
PIPER_VOICE_MAP: Dict[str, Dict[str, str]] = {
    "en": {"female": "en_US-amy-medium", "male": "en_US-ryan-medium"},
    "ur": {"female": "ur-PK-voice-medium", "male": "ur-PK-voice-medium"},
    "hi": {"female": "hi-IN-voice-medium", "male": "hi-IN-voice-medium"},
    "bn": {"female": "bn-BD-voice-medium", "male": "bn-BD-voice-medium"},
    "ar": {"female": "ar-voice-medium", "male": "ar-voice-medium"},
    "es": {"female": "es_ES-davefx-medium", "male": "es_ES-davefx-medium"},
    "fr": {"female": "fr_FR-siwis-medium", "male": "fr_FR-siwis-medium"},
    "de": {"female": "de_DE-thorsten-medium", "male": "de_DE-thorsten-medium"},
    "it": {"female": "it_IT-paola-medium", "male": "it_IT-paola-medium"},
    "pt": {"female": "pt_BR-faber-medium", "male": "pt_BR-faber-medium"},
    "ru": {"female": "ru_RU-denis-medium", "male": "ru_RU-denis-medium"},
    "zh": {"female": "zh_CN-huayan-medium", "male": "zh_CN-huayan-medium"},
    "ja": {"female": "ja-JP-voice-medium", "male": "ja-JP-voice-medium"},
    "ko": {"female": "ko_KR-voice-medium", "male": "ko_KR-voice-medium"},
    "tr": {"female": "tr_TR-dfki-medium", "male": "tr_TR-dfki-medium"},
    "nl": {"female": "nl-voice-medium", "male": "nl-voice-medium"},
    "pl": {"female": "pl_PL-voice-medium", "male": "pl_PL-voice-medium"},
    "uk": {"female": "uk_UK-voice-medium", "male": "uk_UK-voice-medium"},
    "id": {"female": "id_ID-voice-medium", "male": "id_ID-voice-medium"},
    "vi": {"female": "vi_VN-voice-medium", "male": "vi_VN-voice-medium"},
    "cs": {"female": "cs_CZ-voice-medium", "male": "cs_CZ-voice-medium"},
    "el": {"female": "el_GR-voice-medium", "male": "el_GR-voice-medium"},
    "ro": {"female": "ro_RO-voice-medium", "male": "ro_RO-voice-medium"},
    "hu": {"female": "hu_HU-voice-medium", "male": "hu_HU-voice-medium"},
    "sv": {"female": "sv_SE-voice-medium", "male": "sv_SE-voice-medium"},
    "no": {"female": "no-voice-medium", "male": "no-voice-medium"},
    "da": {"female": "da_DK-voice-medium", "male": "da_DK-voice-medium"},
    "fi": {"female": "fi_FI-voice-medium", "male": "fi_FI-voice-medium"},
}


def resolve_piper_voice(voice_style: str, language: str = "en") -> str:
    """Resolve (voice_style, language) → Piper model name."""
    lang = language.lower() if language else "en"
    voice_set = PIPER_VOICE_MAP.get(lang, PIPER_VOICE_MAP["en"])

    # Determine gender from style
    female_styles = {"young_girl", "adult_female", "cartoon", "happy", "excited", "whisper", "sad"}
    male_styles = {"young_boy", "adult_male", "news_anchor", "teacher", "villain", "hero", "robot", "angry"}

    if voice_style in female_styles:
        return voice_set.get("female", "en_US-amy-medium")
    if voice_style in male_styles:
        return voice_set.get("male", "en_US-ryan-medium")
    return voice_set.get("female", "en_US-amy-medium")


# ===================================================================
# Natural language prompt → voice style resolver
# ===================================================================

def resolve_voice_from_prompt(prompt: str) -> Optional[Dict[str, str]]:
    """
    Resolve a natural language voice prompt to a voice style.
    e.g. "young girl voice, sweet, Urdu" → {style: young_girl, language: ur}
    Returns None if no match found.
    """
    if not prompt:
        return None

    prompt_lower = prompt.lower().strip()

    # Language detection
    language = "en"  # default
    for lang in SUPPORTED_LANGUAGES:
        if lang["name"].lower() in prompt_lower or lang["native"] in prompt:
            language = lang["code"]
            break
        # Also check code
        if f" {lang['code']} " in f" {prompt_lower} ":
            language = lang["code"]
            break

    # Style detection
    style_map = {
        "young_girl":   ["young girl", "little girl", "sweet girl", "girl voice", "kid girl", "child girl"],
        "young_boy":     ["young boy", "little boy", "boy voice", "kid boy", "child boy"],
        "adult_male":    ["adult man", "man voice", "male voice", "deep male", "mature man"],
        "adult_female":  ["adult woman", "woman voice", "female voice", "mature woman", "lady voice"],
        "news_anchor":   ["news", "anchor", "broadcast", "reporter", "journalist"],
        "teacher":       ["teacher", "professor", "instructor", "educational", "lecture"],
        "cartoon":       ["cartoon", "animated", "kids", "funny", "playful"],
        "robot":         ["robot", "robotic", "mechanical", "synthetic", "android", "ai voice"],
        "villain":       ["villain", "evil", "dark", "menacing", "sinister", "antagonist"],
        "hero":          ["hero", "heroic", "strong", "brave", "warrior", "protagonist"],
        "whisper":       ["whisper", "soft", "quiet", "intimate", "low voice"],
        "angry":         ["angry", "mad", "furious", "rage", "aggressive"],
        "happy":         ["happy", "cheerful", "joyful", "upbeat", "merry"],
        "sad":           ["sad", "melancholic", "somber", "emotional", "depressed", "crying"],
        "excited":       ["excited", "enthusiastic", "thrilled", "energetic", "hyped"],
    }

    for style, keywords in style_map.items():
        for kw in keywords:
            if kw in prompt_lower:
                return {"style": style, "language": language}

    return None


# ===================================================================
# Catalog API
# ===================================================================

def get_voice_catalog() -> Dict[str, Any]:
    """Return the full voice catalog for the frontend."""
    return {
        "voices": VOICE_STYLES,
        "languages": SUPPORTED_LANGUAGES,
        "total_voices": len(VOICE_STYLES),
        "total_languages": len(SUPPORTED_LANGUAGES),
        "combinations": len(VOICE_STYLES) * len(SUPPORTED_LANGUAGES),
    }


def validate_voice_style(style: str) -> bool:
    """Check if a voice style is valid."""
    return style in VOICE_STYLE_VALUES


def validate_language(lang: str) -> bool:
    """Check if a language code is supported."""
    return lang.lower() in SUPPORTED_LANG_CODES
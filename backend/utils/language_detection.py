"""
Language Detection Utility — detects the language of document text.
Uses langdetect with fallback to English.
"""

import logging
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Mapping of langdetect codes to human-readable names and Tesseract language codes
LANGUAGE_MAP = {
    "en": {"name": "English", "tesseract": "eng"},
    "hi": {"name": "Hindi", "tesseract": "hin"},
    "es": {"name": "Spanish", "tesseract": "spa"},
    "fr": {"name": "French", "tesseract": "fra"},
    "de": {"name": "German", "tesseract": "deu"},
    "it": {"name": "Italian", "tesseract": "ita"},
    "pt": {"name": "Portuguese", "tesseract": "por"},
    "ru": {"name": "Russian", "tesseract": "rus"},
    "ja": {"name": "Japanese", "tesseract": "jpn"},
    "ko": {"name": "Korean", "tesseract": "kor"},
    "zh-cn": {"name": "Chinese (Simplified)", "tesseract": "chi_sim"},
    "zh-tw": {"name": "Chinese (Traditional)", "tesseract": "chi_tra"},
    "ar": {"name": "Arabic", "tesseract": "ara"},
    "nl": {"name": "Dutch", "tesseract": "nld"},
    "sv": {"name": "Swedish", "tesseract": "swe"},
    "pl": {"name": "Polish", "tesseract": "pol"},
    "tr": {"name": "Turkish", "tesseract": "tur"},
    "vi": {"name": "Vietnamese", "tesseract": "vie"},
    "th": {"name": "Thai", "tesseract": "tha"},
    "bn": {"name": "Bengali", "tesseract": "ben"},
    "ta": {"name": "Tamil", "tesseract": "tam"},
    "te": {"name": "Telugu", "tesseract": "tel"},
    "mr": {"name": "Marathi", "tesseract": "mar"},
    "gu": {"name": "Gujarati", "tesseract": "guj"},
}


def detect_language(text: str) -> dict:
    """
    Detect the language of the given text.

    Returns:
        {"code": "en", "name": "English", "tesseract": "eng"}
    """
    if not text or len(text.strip()) < 20:
        return {"code": "en", "name": "English", "tesseract": "eng"}

    try:
        # Use first 2000 chars for detection (faster, still accurate)
        sample = text[:2000]
        code = detect(sample)

        if code in LANGUAGE_MAP:
            return {"code": code, **LANGUAGE_MAP[code]}

        # Unknown language code — return code with English fallback for Tesseract
        return {"code": code, "name": code.upper(), "tesseract": "eng"}

    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}")
        return {"code": "en", "name": "English", "tesseract": "eng"}


def get_tesseract_lang(language_code: str) -> str:
    """Get the Tesseract language code for a given language."""
    if language_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[language_code]["tesseract"]
    return "eng"

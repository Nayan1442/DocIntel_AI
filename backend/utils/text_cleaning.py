"""
Text cleaning utilities for OCR output and raw text.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Full cleaning pipeline: normalize, strip control chars,
    fix whitespace, and remove extra blank lines.
    """
    text = normalize_unicode(text)
    text = remove_control_chars(text)
    text = normalize_whitespace(text)
    text = collapse_blank_lines(text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """Normalize unicode to NFC form."""
    return unicodedata.normalize("NFC", text)


def remove_control_chars(text: str) -> str:
    """Remove non-printable control characters (keep newlines)."""
    return "".join(
        ch for ch in text
        if ch in ("\n", "\r") or not unicodedata.category(ch).startswith("C")
    )


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs into single space per line."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        cleaned.append(re.sub(r"[ \t]+", " ", line).strip())
    return "\n".join(cleaned)


def collapse_blank_lines(text: str) -> str:
    """Collapse 3+ consecutive blank lines into 2."""
    return re.sub(r"\n{3,}", "\n\n", text)


def remove_special_chars(text: str, keep_punctuation: bool = True) -> str:
    """
    Remove special characters.
    If keep_punctuation=True, keeps common punctuation.
    """
    if keep_punctuation:
        return re.sub(r"[^\w\s.,;:!?'\"\-/()@#$%&*]", "", text)
    return re.sub(r"[^\w\s]", "", text)

from utils.text_cleaning import (
    clean_text,
    normalize_unicode,
    remove_control_chars,
    normalize_whitespace,
    collapse_blank_lines,
    remove_special_chars,
)


def test_normalize_unicode():
    """Verify that unicode characters are normalized to NFC."""
    # Angstrom symbol (U+212B) vs A + Ring (U+00C5)
    normalized = normalize_unicode("\u212b")
    assert normalized == "\u00c5"


def test_remove_control_chars():
    """Verify that non-printable control characters are removed but spaces/newlines are kept."""
    text = "Hello\x00world\x07!\nLine two."
    cleaned = remove_control_chars(text)
    assert cleaned == "Helloworld!\nLine two."


def test_normalize_whitespace():
    """Verify that extra spaces and tabs are collapsed per line."""
    text = "Hello    world!\tThis\tis   a test."
    cleaned = normalize_whitespace(text)
    assert cleaned == "Hello world! This is a test."


def test_collapse_blank_lines():
    """Verify that 3+ blank lines are collapsed into 2 newlines."""
    text = "Line one\n\n\n\nLine two\n\n\nLine three"
    cleaned = collapse_blank_lines(text)
    assert cleaned == "Line one\n\nLine two\n\nLine three"


def test_remove_special_chars():
    """Verify that special characters are removed depending on keep_punctuation."""
    text = "Hello, world! @2026 #test$"
    # Keeping punctuation
    assert remove_special_chars(text, keep_punctuation=True) == "Hello, world! @2026 #test$"
    # Stripping punctuation
    assert remove_special_chars(text, keep_punctuation=False) == "Hello world 2026 test"


def test_clean_text_pipeline():
    """Verify that the full clean_text pipeline correctly processes noisy text."""
    noisy_text = "   Hello \x00 world!   \n\n\n\tThis is   OCR output.   "
    assert clean_text(noisy_text) == "Hello world!\n\nThis is OCR output."

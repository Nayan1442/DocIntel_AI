"""
OCR Service — extracts text from PDFs and images.
Uses PyMuPDF for native PDF text and pytesseract for scanned/image documents.
Supports multi-language OCR.
"""

import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pathlib import Path
from utils.text_cleaning import clean_text
from utils.language_detection import detect_language

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}


def get_available_ocr_langs() -> list[str]:
    """Get the list of installed Tesseract languages safely."""
    try:
        return pytesseract.get_languages()
    except Exception as e:
        logger.warning(f"Could not retrieve Tesseract languages: {e}")
        return ["eng"]


def extract_text(file_path: str) -> str:
    """
    Detect file type and extract text accordingly.
    Returns cleaned text.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext in IMAGE_EXTENSIONS:
        return extract_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF.
    Falls back to OCR if native text extraction yields little content.
    Supports multi-language OCR based on native text language detection.
    """
    doc = fitz.open(file_path)
    
    # 1. First pass: extract all native text to detect the main language of the document
    native_text_by_page = []
    has_scanned_pages = False
    
    for page in doc:
        text = page.get_text("text")
        if text and len(text.strip()) > 30:
            native_text_by_page.append(text)
        else:
            native_text_by_page.append("")
            has_scanned_pages = True

    combined_native = "\n".join(native_text_by_page)
    detected = detect_language(combined_native)
    tess_lang = detected.get("tesseract", "eng")
    
    # Check if the detected language package is installed
    available_langs = get_available_ocr_langs()
    lang_param = "eng"
    if tess_lang in available_langs:
        lang_param = tess_lang
        # Combine with English if it's not English itself
        if tess_lang != "eng" and "eng" in available_langs:
            lang_param = f"eng+{tess_lang}"
            
    logger.info(f"PDF OCR: detected lang {detected['name']}, using Tesseract lang param: {lang_param}")

    # 2. Second pass: build final text (use native text where available, fall back to OCR)
    full_text = ""
    for page_num, page in enumerate(doc):
        native = native_text_by_page[page_num]
        if native:
            full_text += native + "\n"
        else:
            # Scanned page — perform OCR
            try:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img, lang=lang_param)
                full_text += ocr_text + "\n"
            except Exception as e:
                logger.warning(f"OCR failed for page {page_num} of {file_path}: {e}. Skipping page OCR.")
                
    doc.close()
    return clean_text(full_text)


def extract_from_image(file_path: str) -> str:
    """Extract text from an image using pytesseract OCR, with English fallback."""
    try:
        img = Image.open(file_path)
        # For a single image, we don't have native text beforehand.
        # We can try to OCR with English + Hindi/Spanish if they are installed, or just default to standard installed list.
        available_langs = get_available_ocr_langs()
        
        # Build standard lang string based on what is available
        langs_to_try = []
        for l in ["eng", "hin", "spa", "fra", "deu"]:
            if l in available_langs:
                langs_to_try.append(l)
        lang_param = "+".join(langs_to_try) if langs_to_try else "eng"
        
        logger.info(f"Image OCR: using lang param {lang_param}")
        raw_text = pytesseract.image_to_string(img, lang=lang_param)
        return clean_text(raw_text)
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        # If Tesseract is not installed/configured, raise a helpful message
        raise ValueError(
            "OCR service is not available on the server. "
            "Please ensure Tesseract is installed and added to the environment PATH."
        ) from e


def is_scanned_pdf(file_path: str) -> bool:
    """Check if a PDF is predominantly scanned (image-based)."""
    doc = fitz.open(file_path)
    total_pages = len(doc)
    scanned_pages = 0

    for page in doc:
        text = page.get_text("text")
        if not text or len(text.strip()) < 30:
            scanned_pages += 1

    doc.close()
    return scanned_pages > (total_pages / 2)

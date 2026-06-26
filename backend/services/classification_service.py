import logging
from services.llm_client import call_llm

logger = logging.getLogger(__name__)

CATEGORIES = [
    "invoice",
    "bank_statement",
    "contract",
    "resume",
    "report",
    "letter",
    "receipt",
    "other",
]


async def classify_document(text: str) -> str:
    """
    Classify a document based on its text content.
    Returns one of the predefined categories.
    """
    text_sample = text[:3000]  # Use first 3000 chars for classification

    prompt = f"""Classify the following document into exactly ONE of these categories:
{', '.join(CATEGORIES)}

Rules:
- Return ONLY the category name, nothing else.
- Use lowercase.
- If uncertain, return "other".

DOCUMENT TEXT:
{text_sample}

CATEGORY:"""

    try:
        result = await call_llm(prompt, temperature=0.0, max_tokens=20)
        result = result.strip().lower()

        # Validate result
        for cat in CATEGORIES:
            if cat in result:
                return cat
        return "other"

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        return "other"


import logging
from services.llm_client import call_llm
from database.db import get_db
from bson import ObjectId
from utils.llm_helpers import parse_llm_json

logger = logging.getLogger(__name__)


async def analyze_sentiment(document_id: str) -> dict:
    """
    Analyze the overall sentiment and tone of a document.

    Returns:
        {
            "document_id": str,
            "overall_sentiment": str,  ("positive", "negative", "neutral", "mixed")
            "confidence": float,       (0.0 - 1.0)
            "tone": str,               ("formal", "informal", "technical", "friendly", etc.)
            "key_emotions": list[str],
            "section_analysis": list[dict],
            "summary": str
        }
    """
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise ValueError(f"Document not found: {document_id}")

    text = doc.get("text_content", "")[:5000]
    if not text:
        raise ValueError("Document has no text content.")

    classification = doc.get("classification", "document")

    system_msg = """You are an expert sentiment and tone analyst. 
Analyze documents thoroughly and return precise, structured sentiment analysis.
Return ONLY valid JSON."""

    prompt = f"""Analyze the sentiment and tone of this {classification} document.
Return your response as valid JSON:

{{
    "overall_sentiment": "positive" or "negative" or "neutral" or "mixed",
    "confidence": 0.85,
    "tone": "formal/informal/technical/friendly/urgent/persuasive",
    "key_emotions": ["list of emotions detected, e.g. confidence, urgency, frustration"],
    "section_analysis": [
        {{"section": "opening", "sentiment": "positive", "note": "brief observation"}},
        {{"section": "body", "sentiment": "neutral", "note": "brief observation"}},
        {{"section": "closing", "sentiment": "positive", "note": "brief observation"}}
    ],
    "summary": "One paragraph summary of the overall emotional tone and intent of this document"
}}

DOCUMENT TEXT:
{text}

Return ONLY the JSON:"""

    response = await call_llm(prompt, system_msg=system_msg)

    # Parse JSON from response
    default_res = {
        "overall_sentiment": "neutral",
        "confidence": 0.5,
        "tone": "unknown",
        "key_emotions": [],
        "section_analysis": [],
        "summary": "Analysis unavailable."
    }
    result = parse_llm_json(response, default_factory=lambda: default_res)

    # Save to DB
    await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {"sentiment": result}}
    )

    result["document_id"] = document_id
    return result

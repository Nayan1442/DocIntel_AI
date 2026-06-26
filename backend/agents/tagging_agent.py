import logging
from services.llm_client import call_llm
from database.db import get_db
from bson import ObjectId
from utils.llm_helpers import parse_llm_json

logger = logging.getLogger(__name__)


async def auto_tag_document(document_id: str) -> dict:
    """
    Extract keywords, named entities, and auto-generate tags from document text.

    Returns:
        {
            "document_id": str,
            "keywords": list[str],
            "entities": { "people": [], "organizations": [], "dates": [], "amounts": [], "emails": [], "locations": [] },
            "tags": list[str]
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

    system_msg = """You are an expert document analyst specializing in information extraction.
Extract structured information precisely and return ONLY the requested JSON format.
Do not add any extra text or explanation outside the JSON."""

    prompt = f"""Analyze this {classification} document and extract the following information.
Return your response as valid JSON with these exact keys:

{{
    "keywords": ["top 8-12 most important keywords or phrases"],
    "entities": {{
        "people": ["list of person names found"],
        "organizations": ["list of company/org names"],
        "dates": ["list of dates mentioned"],
        "amounts": ["list of monetary amounts"],
        "emails": ["list of email addresses"],
        "locations": ["list of places/addresses"]
    }},
    "tags": ["5-8 concise category tags for this document"]
}}

DOCUMENT TEXT:
{text}

Return ONLY the JSON, no other text:"""

    response = await call_llm(prompt, system_msg=system_msg)

    # Parse JSON from response
    result = parse_llm_json(response, default_factory=lambda: {"keywords": [], "entities": {}, "tags": []})

    # Save tags to document in DB
    await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {
            "keywords": result.get("keywords", []),
            "entities": result.get("entities", {}),
            "auto_tags": result.get("tags", []),
        }}
    )

    return {
        "document_id": document_id,
        "keywords": result.get("keywords", []),
        "entities": result.get("entities", {}),
        "tags": result.get("tags", []),
    }

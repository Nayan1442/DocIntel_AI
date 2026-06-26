"""
Extraction Agent — retrieves document text, detects type,
and calls the extraction service with a type-specific schema.
"""

from services.extraction_service import extract_structured_data
from database.db import get_db
from bson import ObjectId
from datetime import datetime, timezone


async def extract_data(document_id: str, custom_fields: list[str] | None = None) -> dict:
    """
    Extract structured data from a document.

    Args:
        document_id:   MongoDB document ID.
        custom_fields: Optional user-specified fields to extract.

    Returns:
        {"document_id": str, "extracted_data": dict}
    """
    db = get_db()

    # Fetch document
    doc = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise ValueError(f"Document not found: {document_id}")

    # Return cached extraction if available and no custom fields requested
    if doc.get("extracted_data") and not custom_fields:
        return {
            "document_id": document_id,
            "extracted_data": doc["extracted_data"],
        }

    text = doc.get("text_content", "")
    if not text:
        raise ValueError("Document has no text content for extraction.")

    classification = doc.get("classification")

    # Extract
    extracted = await extract_structured_data(text, classification, custom_fields)

    # Cache in MongoDB (only if not custom fields)
    if not custom_fields:
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"extracted_data": extracted, "updated_at": datetime.now(timezone.utc)}},
        )

    return {
        "document_id": document_id,
        "extracted_data": extracted,
    }

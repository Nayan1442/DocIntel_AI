"""
Summarization Agent — retrieves document text and generates summaries.
Caches results in MongoDB to avoid re-processing.
"""

from services.summarization_service import summarize_document
from database.db import get_db
from bson import ObjectId
from datetime import datetime, timezone


async def get_summary(document_id: str, num_points: int = 5) -> dict:
    """
    Generate or retrieve a cached summary for a document.

    Args:
        document_id: MongoDB document ID.
        num_points:  Number of bullet points.

    Returns:
        {"document_id": str, "summary": str}
    """
    db = get_db()

    # Fetch document
    doc = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise ValueError(f"Document not found: {document_id}")

    # Return cached summary if available and same point count
    if doc.get("summary") and doc.get("summary_num_points") == num_points:
        return {
            "document_id": document_id,
            "summary": doc["summary"],
        }

    # Generate new summary
    text = doc.get("text_content", "")
    if not text:
        raise ValueError("Document has no text content for summarization.")

    summary = await summarize_document(text, num_points)

    # Cache in MongoDB (store num_points so we know when to invalidate)
    await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {
            "summary": summary,
            "summary_num_points": num_points,
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    return {
        "document_id": document_id,
        "summary": summary,
    }

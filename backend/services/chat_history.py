"""
Chat History Service — stores and retrieves conversation history in MongoDB.
Enables follow-up questions by providing LLM with prior context.
"""

from database.db import get_db
from bson import ObjectId
from datetime import datetime, timezone


async def create_conversation(user_id: str, document_id: str = None, title: str = "New Chat") -> str:
    """Create a new conversation and return its ID."""
    db = get_db()
    result = await db.conversations.insert_one({
        "user_id": user_id,
        "document_id": document_id,
        "title": title,
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    return str(result.inserted_id)


async def add_message(conversation_id: str, role: str, content: str, sources: list = None, confidence: float = None):
    """Add a message to an existing conversation."""
    db = get_db()
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    }
    if sources is not None:
        message["sources"] = sources
    if confidence is not None:
        message["confidence"] = confidence

    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        }
    )


async def get_conversation(conversation_id: str, user_id: str) -> dict:
    """Retrieve a conversation by ID."""
    db = get_db()
    conv = await db.conversations.find_one({"_id": ObjectId(conversation_id), "user_id": user_id})
    if not conv:
        return None
    conv["id"] = str(conv.pop("_id"))
    return conv


async def list_conversations(user_id: str, limit: int = 20) -> list:
    """List recent conversations."""
    db = get_db()
    cursor = db.conversations.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
    results = []
    async for conv in cursor:
        conv["id"] = str(conv.pop("_id"))
        conv["message_count"] = len(conv.get("messages", []))
        # Only include last 2 messages for preview
        msgs = conv.get("messages", [])
        conv["last_message"] = msgs[-1]["content"][:100] if msgs else ""
        del conv["messages"]
        results.append(conv)
    return results


async def get_conversation_context(conversation_id: str, max_messages: int = 6) -> list:
    """Get recent messages for LLM context (for follow-up questions)."""
    db = get_db()
    conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv:
        return []
    messages = conv.get("messages", [])
    # Return last N messages as chat history
    recent = messages[-max_messages:] if len(messages) > max_messages else messages
    return [{"role": m["role"], "content": m["content"]} for m in recent]


async def delete_conversation(conversation_id: str, user_id: str):
    """Delete a conversation."""
    db = get_db()
    await db.conversations.delete_one({"_id": ObjectId(conversation_id), "user_id": user_id})

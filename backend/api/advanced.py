"""
Advanced API Routes — Chat History, Auto-Tagging, Sentiment Analysis,
Document Statistics, and Batch Processing.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from agents.tagging_agent import auto_tag_document
from agents.sentiment_agent import analyze_sentiment
from services.chat_history import (
    create_conversation, add_message, get_conversation,
    list_conversations, get_conversation_context, delete_conversation,
)
from services.rag_service import ask_question, ask_question_stream
from services.auth_middleware import get_current_user
from database.db import get_db
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import asyncio
import os
import uuid
import json
import aiofiles
from config import settings

router = APIRouter(tags=["Advanced Features"])


# ─── Chat History ────────────────────────────────────────────

class ChatMessage(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    document_id: Optional[str] = None


@router.post("/chat")
async def chat_with_history(msg: ChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Send a message with conversation history.
    Creates a new conversation if conversation_id is not provided.
    LLM receives recent chat history for follow-up context.
    """
    try:
        # Create or use existing conversation
        conv_id = msg.conversation_id
        if not conv_id:
            conv_id = await create_conversation(
                user_id=current_user["id"],
                document_id=msg.document_id,
                title=msg.question[:60]
            )

        # Save user message
        await add_message(conv_id, "user", msg.question)

        # Get conversation context for follow-up
        history = await get_conversation_context(conv_id)

        # Build context-aware prompt
        if len(history) > 2:
            # Has prior conversation — add context
            history_text = "\n".join(
                [f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in history[:-1]]
            )
            enhanced_question = f"""Given this conversation history:
{history_text}

Current question: {msg.question}

Answer the current question, taking the conversation context into account."""
        else:
            enhanced_question = msg.question

        # Get RAG answer
        result = await ask_question(enhanced_question, msg.document_id)

        # Calculate confidence (scores are cosine similarity: higher = more similar)
        sources = result.get("sources", [])
        if sources:
            avg_score = sum(s.get("score", 0) for s in sources) / len(sources)
            similarity = max(0.0, min(avg_score, 1.0))  # clamp to [0, 1]
            confidence = min(round(similarity * 85 + min(len(sources) / 8, 1) * 15), 100)
        else:
            confidence = 0

        # Save assistant response
        await add_message(conv_id, "assistant", result["answer"], sources, confidence)

        return {
            "conversation_id": conv_id,
            "answer": result["answer"],
            "sources": sources,
            "confidence": confidence,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """List all recent conversations."""
    return await list_conversations(user_id=current_user["id"])


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get full conversation with all messages."""
    conv = await get_conversation(conversation_id, user_id=current_user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation."""
    await delete_conversation(conversation_id, user_id=current_user["id"])
    return {"status": "deleted"}


@router.post("/chat/stream")
async def chat_with_history_stream(msg: ChatMessage, current_user: dict = Depends(get_current_user)):
    """
    Stream chat messages with history using Server-Sent Events (SSE).
    """
    try:
        conv_id = msg.conversation_id
        if not conv_id:
            conv_id = await create_conversation(
                user_id=current_user["id"],
                document_id=msg.document_id,
                title=msg.question[:60]
            )

        # Save user message
        await add_message(conv_id, "user", msg.question)

        # Get conversation context for follow-up
        history = await get_conversation_context(conv_id)

        # Build context-aware prompt
        if len(history) > 2:
            history_text = "\n".join(
                [f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in history[:-1]]
            )
            enhanced_question = f"""Given this conversation history:
{history_text}

Current question: {msg.question}

Answer the current question, taking the conversation context into account."""
        else:
            enhanced_question = msg.question

        async def event_generator():
            # First send conversation_id
            yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conv_id})}\n\n"
            
            full_answer = ""
            sources = []
            
            async for chunk in ask_question_stream(enhanced_question, msg.document_id):
                if chunk["type"] == "token":
                    full_answer += chunk["content"]
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "sources":
                    sources = chunk["sources"]
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk["type"] == "follow_ups":
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            if sources:
                avg_score = sum(s.get("score", 0) for s in sources) / len(sources)
                similarity = max(0.0, min(avg_score, 1.0))
                confidence = min(round(similarity * 85 + min(len(sources) / 8, 1) * 15), 100)
            else:
                confidence = 0
                
            yield f"data: {json.dumps({'type': 'confidence', 'confidence': confidence})}\n\n"
            await add_message(conv_id, "assistant", full_answer, sources, confidence)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Auto-Tagging ───────────────────────────────────────────

@router.post("/auto-tag/{document_id}")
async def tag_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Extract keywords, entities, and auto-generate tags for a document."""
    try:
        return await auto_tag_document(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tagging failed: {str(e)}")


# ─── Sentiment Analysis ─────────────────────────────────────

@router.post("/sentiment/{document_id}")
async def sentiment_analysis(document_id: str, current_user: dict = Depends(get_current_user)):
    """Analyze the sentiment and tone of a document."""
    try:
        return await analyze_sentiment(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


# ─── Document Statistics ────────────────────────────────────

@router.get("/stats")
async def get_document_stats(current_user: dict = Depends(get_current_user)):
    """
    Global statistics: document counts, type distribution,
    chunk metrics, query activity, and storage usage.
    """
    db = get_db()

    # Total documents
    total_docs = await db.documents.count_documents({"user_id": current_user["id"]})

    # Type distribution
    pipeline_types = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {"_id": "$classification", "count": {"$sum": 1}}}
    ]
    type_dist = {}
    async for item in db.documents.aggregate(pipeline_types):
        type_dist[item["_id"] or "other"] = item["count"]

    # Chunk statistics
    pipeline_chunks = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": None,
            "total_chunks": {"$sum": "$chunk_count"},
            "avg_chunks": {"$avg": "$chunk_count"},
            "max_chunks": {"$max": "$chunk_count"},
        }}
    ]
    chunk_stats = {"total": 0, "average": 0, "max": 0}
    async for item in db.documents.aggregate(pipeline_chunks):
        chunk_stats = {
            "total": item.get("total_chunks", 0),
            "average": round(item.get("avg_chunks", 0), 1),
            "max": item.get("max_chunks", 0),
        }

    # File size stats
    pipeline_size = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": None,
            "total_size": {"$sum": "$file_size"},
            "avg_size": {"$avg": "$file_size"},
        }}
    ]
    size_stats = {"total_bytes": 0, "average_bytes": 0}
    async for item in db.documents.aggregate(pipeline_size):
        size_stats = {
            "total_bytes": item.get("total_size", 0),
            "average_bytes": round(item.get("avg_size", 0)),
        }

    # Recent uploads (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_uploads = await db.documents.count_documents({
        "user_id": current_user["id"],
        "created_at": {"$gte": week_ago}
    })

    # Conversation stats
    total_conversations = await db.conversations.count_documents({"user_id": current_user["id"]})
    pipeline_msgs = [
        {"$match": {"user_id": current_user["id"]}},
        {"$project": {"msg_count": {"$size": {"$ifNull": ["$messages", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$msg_count"}}}
    ]
    total_messages = 0
    async for item in db.conversations.aggregate(pipeline_msgs):
        total_messages = item.get("total", 0)

    # Most queried documents
    pipeline_popular = [
        {"$match": {"user_id": current_user["id"]}},
        {"$unwind": "$messages"},
        {"$match": {"messages.role": "user"}},
        {"$group": {"_id": "$document_id", "queries": {"$sum": 1}}},
        {"$sort": {"queries": -1}},
        {"$limit": 5},
    ]
    popular_docs = []
    try:
        async for item in db.conversations.aggregate(pipeline_popular):
            if item["_id"]:
                doc = await db.documents.find_one({"_id": ObjectId(item["_id"])})
                popular_docs.append({
                    "document_id": item["_id"],
                    "name": doc.get("original_name", "Unknown") if doc else "Deleted",
                    "query_count": item["queries"],
                })
    except Exception:
        pass

    return {
        "documents": {
            "total": total_docs,
            "recent_week": recent_uploads,
            "type_distribution": type_dist,
        },
        "chunks": chunk_stats,
        "storage": size_stats,
        "conversations": {
            "total": total_conversations,
            "total_messages": total_messages,
        },
        "popular_documents": popular_docs,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── Batch Processing ───────────────────────────────────────

@router.post("/batch-upload")
async def batch_upload(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and process multiple files simultaneously in the background.
    Returns immediate status for each file.
    """
    from database.models import DocumentModel
    from api.upload import bg_process_document

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")

    results = []
    db = get_db()
    for file in files:
        try:
            # Validate extension
            filename = os.path.basename(file.filename or "unknown")
            ext = os.path.splitext(filename)[1].lower()
            if ext not in settings.ALLOWED_EXTENSIONS:
                results.append({"filename": filename, "status": "error", "detail": f"Unsupported extension: {ext}"})
                continue

            # Stream files in chunks to compute size and validate
            unique_name = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

            file_size = 0
            max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

            try:
                async with aiofiles.open(file_path, "wb") as f:
                    while chunk := await file.read(1024 * 1024):  # 1MB chunks
                        file_size += len(chunk)
                        if file_size > max_bytes:
                            raise HTTPException(status_code=400, detail="File too large")
                        await f.write(chunk)
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                results.append({"filename": filename, "status": "error", "detail": f"Write failed: {str(e)}"})
                continue

            # Create document record with "processing" status
            file_type = "pdf" if ext == "pdf" else "image"
            doc_data = DocumentModel(
                user_id=current_user["id"],
                filename=unique_name,
                original_name=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status="processing",
                progress_pct=10,
                status_detail="Saved to disk. Starting AI pipeline...",
                chunk_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            insert_result = await db.documents.insert_one(doc_data.model_dump())
            doc_id = str(insert_result.inserted_id)

            # Queue background task
            background_tasks.add_task(
                bg_process_document,
                file_path=file_path,
                filename=unique_name,
                original_name=filename,
                file_size=file_size,
                user_id=current_user["id"],
                document_id=doc_id
            )

            results.append({
                "filename": filename,
                "status": "success",
                "document_id": doc_id,
                "message": "AI analysis queued in background."
            })

        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "detail": str(e)})

    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success

    return {
        "total": len(results),
        "success": success,
        "failed": failed,
        "results": results,
    }

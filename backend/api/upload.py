import os
import uuid
import aiofiles
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from config import settings
from agents.document_agent import process_document
from database.db import get_db
from database.models import UploadResponse, DocumentResponse, DocumentModel
from bson import ObjectId
from services.auth_middleware import get_current_user
from datetime import datetime, timezone

router = APIRouter(tags=["Documents"])
logger = logging.getLogger(__name__)


async def bg_process_document(
    file_path: str,
    filename: str,
    original_name: str,
    file_size: int,
    user_id: str,
    document_id: str
):
    """Background task to run the document intelligence pipeline."""
    try:
        await process_document(
            file_path=file_path,
            filename=filename,
            original_name=original_name,
            file_size=file_size,
            user_id=user_id,
            document_id=document_id
        )
    except Exception as e:
        logger.error(f"Background processing failed for {original_name}: {e}")
        db = get_db()
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "failed", "error_message": str(e)}}
        )
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document (PDF or image) for AI processing in the background.
    The document immediately returns a queue status and runs: OCR → chunking → embedding → classification.
    """
    # Sanitize filename to prevent path traversal
    filename = os.path.basename(file.filename or "unknown")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Save file in chunks to stream uploads and limit memory usage
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_size = 0
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # read in 1MB chunks
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
                    )
                await f.write(chunk)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create document record with "processing" status in MongoDB
    db = get_db()
    ext = file_path.rsplit(".", 1)[-1].lower()
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

    try:
        result = await db.documents.insert_one(doc_data.model_dump())
        doc_id = str(result.inserted_id)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Failed to save document record: {e}")
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    # Queue background task for full AI processing pipeline
    background_tasks.add_task(
        bg_process_document,
        file_path=file_path,
        filename=unique_name,
        original_name=filename,
        file_size=file_size,
        user_id=current_user["id"],
        document_id=doc_id
    )

    return UploadResponse(
        id=doc_id,
        filename=filename,
        status="processing",
        progress_pct=10,
        status_detail="Saved to disk. Starting AI pipeline...",
        message="Document uploaded. AI analysis is processing in the background."
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(current_user: dict = Depends(get_current_user)):
    """List all uploaded documents for the current user."""
    db = get_db()
    cursor = db.documents.find({"user_id": current_user["id"]}).sort("created_at", -1)
    documents = []

    async for doc in cursor:
        documents.append(
            DocumentResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                original_name=doc["original_name"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                status=doc.get("status", "completed"),
                progress_pct=doc.get("progress_pct", 0),
                status_detail=doc.get("status_detail", ""),
                classification=doc.get("classification"),
                chunk_count=doc.get("chunk_count", 0),
                detected_language=doc.get("detected_language"),
                created_at=doc["created_at"],
            )
        )

    return documents


@router.get("/documents/{document_id}")
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific document's details."""
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(document_id), "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "original_name": doc["original_name"],
        "file_type": doc["file_type"],
        "file_size": doc["file_size"],
        "status": doc.get("status", "completed"),
        "progress_pct": doc.get("progress_pct", 0),
        "status_detail": doc.get("status_detail", ""),
        "classification": doc.get("classification"),
        "text_content": (doc.get("text_content") or "")[:2000],  # truncate for preview
        "summary": doc.get("summary"),
        "extracted_data": doc.get("extracted_data"),
        "chunk_count": doc.get("chunk_count", 0),
        "created_at": doc["created_at"].isoformat(),
    }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document, its chunks, its embeddings, and its physical file on disk."""
    db = get_db()
    # 1. Fetch document metadata first
    doc = await db.documents.find_one({"_id": ObjectId(document_id), "user_id": current_user["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Delete database records
    await db.documents.delete_one({"_id": ObjectId(document_id)})
    await db.chunks.delete_many({"document_id": document_id})

    # 3. Clean up file on disk
    filename = doc.get("filename")
    if filename:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting physical file {file_path}: {e}")

    # 4. Remove vectors from FAISS index
    from services.embedding_service import remove_document_from_index
    try:
        remove_document_from_index(document_id)
    except Exception as e:
        logger.error(f"Error removing embeddings for document {document_id}: {e}")

    return {"message": "Document deleted successfully", "id": document_id}

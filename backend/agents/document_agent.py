import logging
import asyncio
from services.ocr_service import extract_text
from services.embedding_service import generate_embeddings, add_to_index
from services.classification_service import classify_document
from services.summarization_service import summarize_document
from utils.chunking import chunk_text
from utils.language_detection import detect_language
from database.db import get_db
from database.models import DocumentModel, ChunkModel
from datetime import datetime, timezone
from bson import ObjectId

logger = logging.getLogger(__name__)


async def process_document(file_path: str, filename: str, original_name: str, file_size: int, user_id: str = "", document_id: str = None) -> dict:
    """
    Full pipeline for processing an uploaded document.

    Steps:
        1. Extract text (OCR if needed)
        2. Chunk the text
        3. Classify & Summarize concurrently
        4. Store document in MongoDB
        5. Generate embeddings & add to FAISS
        6. Store chunks in MongoDB

    Returns:
        Document metadata dict with MongoDB ID.
    """
    db = get_db()

    async def update_progress(pct: int, detail: str):
        if document_id:
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"progress_pct": pct, "status_detail": detail}}
            )

    # ── Step 1: Extract text ────────────────────────────
    logger.info(f"Extracting text from: {original_name}")
    await update_progress(20, "Extracting text (OCR if needed)...")
    text_content = extract_text(file_path)

    if not text_content or len(text_content.strip()) < 10:
        raise ValueError("Could not extract meaningful text from the document.")

    # ── Step 2: Chunk ───────────────────────────────────
    logger.info(f"Chunking text ({len(text_content)} chars)")
    await update_progress(45, "Splitting document into semantic chunks...")
    chunks = chunk_text(text_content)

    if not chunks:
        raise ValueError("Text chunking produced no chunks.")

    # ── Step 3: Classify & Summarize concurrently ───────
    logger.info("Classifying and summarizing document concurrently...")
    await update_progress(65, "Summarizing and classifying document...")
    classification, summary = await asyncio.gather(
        classify_document(text_content),
        summarize_document(text_content, num_points=5)
    )

    # ── Step 4: Store document in MongoDB ───────────────
    ext = file_path.rsplit(".", 1)[-1].lower()
    file_type = "pdf" if ext == "pdf" else "image"

    # Detect language
    lang_info = detect_language(text_content)
    logger.info(f"Detected language: {lang_info['name']}")

    doc_data = DocumentModel(
        user_id=user_id,
        filename=filename,
        original_name=original_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        status="completed",
        progress_pct=100,
        status_detail="Processing completed successfully!",
        classification=classification,
        text_content=text_content,
        summary=summary,
        detected_language=lang_info["name"],
        chunk_count=len(chunks),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    if document_id:
        # Avoid overriding original created_at time
        update_data = doc_data.model_dump()
        update_data.pop("created_at", None)
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        doc_id = document_id
    else:
        result = await db.documents.insert_one(doc_data.model_dump())
        doc_id = str(result.inserted_id)

    # ── Step 5: Generate embeddings & add to FAISS ──────
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    await update_progress(85, "Generating embeddings & indexing vectors...")
    embeddings = generate_embeddings(chunks)
    faiss_ids = add_to_index(embeddings, doc_id, chunks)

    # ── Step 6: Store chunks in MongoDB ─────────────────
    chunk_docs = []
    for i, (chunk, fid) in enumerate(zip(chunks, faiss_ids)):
        chunk_doc = ChunkModel(
            document_id=doc_id,
            chunk_index=i,
            text=chunk,
            embedding_id=fid,
        )
        chunk_docs.append(chunk_doc.model_dump())

    if chunk_docs:
        await db.chunks.insert_many(chunk_docs)

    await update_progress(100, "Completed")
    logger.info(f"Document processed successfully: {original_name} → {doc_id} ({classification})")

    return {
        "id": doc_id,
        "filename": filename,
        "original_name": original_name,
        "classification": classification,
        "chunk_count": len(chunks),
        "text_length": len(text_content),
    }

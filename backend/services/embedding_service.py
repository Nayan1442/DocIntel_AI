import numpy as np
import faiss
import os
import json
import threading
from sentence_transformers import SentenceTransformer
from config import settings
from pathlib import Path

# ── Module-level state ──────────────────────────────────
_model: SentenceTransformer = None
_index: faiss.IndexFlatIP = None
_chunk_metadata: list[dict] = []  # maps FAISS ID → {document_id, chunk_index}
_metadata_path = str(Path(settings.FAISS_INDEX_PATH).parent / "chunk_metadata.json")
_index_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def _get_index() -> faiss.IndexFlatIP:
    """Lazy-load or create the FAISS index."""
    global _index
    if _index is None:
        index_file = settings.FAISS_INDEX_PATH + ".index"
        if os.path.exists(index_file):
            _index = faiss.read_index(index_file)
            load_metadata()
        else:
            _index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
    return _index


# ── Public API ──────────────────────────────────────────

def generate_embedding(text: str) -> np.ndarray:
    """Generate a single embedding vector for text."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.astype("float32")


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings for multiple texts (batched)."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.astype("float32")


def add_to_index(
    embeddings: np.ndarray,
    document_id: str,
    chunks: list[str],
) -> list[int]:
    """
    Add embeddings to the FAISS index and store chunk metadata.
    Returns the list of FAISS IDs assigned.
    """
    global _chunk_metadata, _index
    with _index_lock:
        index = _get_index()
        start_id = index.ntotal
        index.add(embeddings)

        ids = []
        for i in range(len(chunks)):
            fid = start_id + i
            _chunk_metadata.append({
                "faiss_id": fid,
                "document_id": document_id,
                "chunk_index": i,
            })
            ids.append(fid)

        save_index()
        save_metadata()
        return ids


def remove_document_from_index(document_id: str):
    """
    Remove all vectors associated with document_id from the FAISS index.
    Rebuilds the index and updates chunk_metadata.
    """
    global _index, _chunk_metadata
    with _index_lock:
        index = _get_index()
        if index.ntotal == 0:
            return

        # 1. Reconstruct all vectors from the index
        vectors = []
        for i in range(index.ntotal):
            vectors.append(index.reconstruct(i))
        vectors = np.array(vectors, dtype=np.float32)

        # 2. Filter out metadata and determine which vector indices to keep
        keep_indices = []
        new_metadata = []
        for i, meta in enumerate(_chunk_metadata):
            if meta["document_id"] != document_id:
                keep_indices.append(i)
                # Re-map faiss_id to the new sequential index
                new_meta = meta.copy()
                new_meta["faiss_id"] = len(new_metadata)
                new_metadata.append(new_meta)

        # 3. Create a brand new index
        _index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)

        # 4. If we have vectors to keep, rebuild index
        if keep_indices:
            keep_vectors = vectors[keep_indices]
            _index.add(keep_vectors)

        # 5. Update global metadata
        _chunk_metadata = new_metadata

        # 6. Save the new state to disk
        save_index()
        save_metadata()


async def search(query: str, top_k: int = None) -> list[dict]:
    """
    Perform semantic search: embed query → search FAISS → retrieve text from MongoDB → return top results.
    Returns list of {document_id, chunk_index, text, score}.
    """
    top_k = top_k or settings.RAG_TOP_K
    index = _get_index()

    if index.ntotal == 0:
        return []

    query_vec = generate_embedding(query).reshape(1, -1)
    scores, indices = index.search(query_vec, min(top_k, index.ntotal))

    results = []
    from database.db import get_db
    db = get_db()

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_chunk_metadata):
            continue
        meta = _chunk_metadata[idx]

        # Fetch chunk text from MongoDB using document_id and chunk_index
        chunk_text = ""
        if db is not None:
            chunk_doc = await db.chunks.find_one({
                "document_id": meta["document_id"],
                "chunk_index": meta["chunk_index"]
            })
            if chunk_doc:
                chunk_text = chunk_doc.get("text", "")

        results.append({
            "document_id": meta["document_id"],
            "chunk_index": meta["chunk_index"],
            "text": chunk_text,
            "score": float(score),
        })

    return results


async def search_by_document(query: str, document_id: str, top_k: int = None) -> list[dict]:
    """Search within a specific document only."""
    all_results = await search(query, top_k=top_k or settings.RAG_TOP_K * 3)
    return [r for r in all_results if r["document_id"] == document_id][:top_k or settings.RAG_TOP_K]


# ── Persistence ─────────────────────────────────────────

def save_index():
    """Save FAISS index to disk."""
    index = _get_index()
    os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)
    faiss.write_index(index, settings.FAISS_INDEX_PATH + ".index")


def save_metadata():
    """Save chunk metadata to JSON."""
    os.makedirs(os.path.dirname(_metadata_path) or ".", exist_ok=True)
    with open(_metadata_path, "w", encoding="utf-8") as f:
        json.dump(_chunk_metadata, f, ensure_ascii=False)


def load_metadata():
    """Load chunk metadata from JSON."""
    global _chunk_metadata
    if os.path.exists(_metadata_path):
        with open(_metadata_path, "r", encoding="utf-8") as f:
            _chunk_metadata = json.load(f)


def initialize():
    """Pre-load model and index at startup."""
    _get_model()
    _get_index()
    print(f"✅ Embedding service initialized — {_get_index().ntotal} vectors in index")

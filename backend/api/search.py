"""
Search API — semantic search across all documents.
"""

from fastapi import APIRouter, HTTPException, Depends
from database.models import SearchRequest, SearchResponse, SearchResultItem
from services.embedding_service import search
from database.db import get_db
from bson import ObjectId
from services.auth_middleware import get_current_user

router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, current_user: dict = Depends(get_current_user)):
    """
    Perform semantic search across all indexed documents.
    Returns the most relevant text chunks with similarity scores.
    """
    try:
        results = await search(request.query, top_k=request.top_k)
        db = get_db()

        items = []
        for r in results:
            # Fetch document name
            filename = None
            try:
                doc = await db.documents.find_one({"_id": ObjectId(r["document_id"])})
                if doc:
                    filename = doc.get("original_name")
            except Exception:
                pass

            items.append(
                SearchResultItem(
                    document_id=r["document_id"],
                    chunk_text=r["text"],
                    score=r["score"],
                    filename=filename,
                    chunk_index=r.get("chunk_index"),
                )
            )

        return SearchResponse(results=items, query=request.query)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

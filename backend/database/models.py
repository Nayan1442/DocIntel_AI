"""
Pydantic models for request/response validation and database documents.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Database document schemas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserModel(BaseModel):
    """Represents a user account in MongoDB."""
    name: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentModel(BaseModel):
    """Represents a stored document in MongoDB."""
    user_id: str  # owner
    filename: str
    original_name: str
    file_path: str
    file_type: str  # pdf, image
    file_size: int  # bytes
    status: str = "completed"  # processing, completed, failed
    progress_pct: Optional[int] = 0
    status_detail: Optional[str] = None
    classification: Optional[str] = None
    text_content: Optional[str] = None
    summary: Optional[str] = None
    extracted_data: Optional[dict] = None
    detected_language: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChunkModel(BaseModel):
    """Represents a text chunk with its embedding metadata."""
    document_id: str
    chunk_index: int
    text: str
    embedding_id: int  # FAISS index ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API request schemas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QueryRequest(BaseModel):
    """Request body for /ask-question."""
    question: str
    document_id: Optional[str] = None  # scope to specific doc


class SearchRequest(BaseModel):
    """Request body for /search."""
    query: str
    top_k: int = 5


class SummarizeRequest(BaseModel):
    """Request body for /summarize."""
    document_id: str
    num_points: int = 5


class ExtractionRequest(BaseModel):
    """Request body for /extract-data."""
    document_id: str
    fields: Optional[list[str]] = None  # custom fields to extract


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API response schemas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentResponse(BaseModel):
    """Response for document listing."""
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    status: str = "completed"
    progress_pct: Optional[int] = 0
    status_detail: Optional[str] = None
    classification: Optional[str] = None
    chunk_count: int = 0
    detected_language: Optional[str] = None
    created_at: datetime


class UploadResponse(BaseModel):
    """Response after document upload."""
    id: str
    filename: str
    message: str
    status: str = "completed"
    progress_pct: Optional[int] = 0
    status_detail: Optional[str] = None
    classification: Optional[str] = None


class AnswerResponse(BaseModel):
    """Response for question-answering."""
    answer: str
    sources: list[dict] = []


class SearchResultItem(BaseModel):
    """Single search result."""
    document_id: str
    chunk_text: str
    score: float
    filename: Optional[str] = None
    chunk_index: Optional[int] = None


class SearchResponse(BaseModel):
    """Response for semantic search."""
    results: list[SearchResultItem]
    query: str


class SummaryResponse(BaseModel):
    """Response for summarization."""
    document_id: str
    summary: str


class ExtractionResponse(BaseModel):
    """Response for structured data extraction."""
    document_id: str
    extracted_data: dict


class ReportResponse(BaseModel):
    """Response for AI insights report."""
    document_id: str
    filename: str
    classification: Optional[str] = None
    summary: str
    extracted_data: dict
    insights: list[str]

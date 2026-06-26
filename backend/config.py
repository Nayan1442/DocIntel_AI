"""
Application configuration using Pydantic BaseSettings.
Loads values from environment variables / .env file.
"""

import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "AI Document Intelligence Platform"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── MongoDB ──────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "doc_intelligence"

    # ── LLM Provider ─────────────────────────────────────
    LLM_PROVIDER: str = "openrouter"  # "groq" or "openrouter"
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = ""  # Leave empty to use provider default
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096

    # ── Embedding ────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ── FAISS ────────────────────────────────────────────
    FAISS_INDEX_PATH: str = str(Path(__file__).parent / "data" / "faiss_index")

    # ── Upload / Data ────────────────────────────────────
    UPLOAD_DIR: str = str(Path(__file__).parent / "data" / "documents")
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]

    # ── Chunking ─────────────────────────────────────────
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 128

    # ── RAG ──────────────────────────────────────────────
    RAG_TOP_K: int = 8

    # ── Auth ─────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    JWT_EXPIRY_HOURS: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)

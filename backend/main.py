"""
AI Document Intelligence Platform — FastAPI Application Entry Point.
Registers all routers, CORS, and manages startup/shutdown lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from database.db import connect_db, disconnect_db
from api.upload import router as upload_router
from api.query import router as query_router
from api.search import router as search_router
from api.extraction import router as extraction_router
from api.comparison import router as comparison_router
from api.advanced import router as advanced_router
from api.auth import router as auth_router
import time
from collections import defaultdict
import re
import json
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ─────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME}")
    
    # Enforce JWT Secret security in production mode
    if not settings.DEBUG and settings.JWT_SECRET_KEY == "change-me-to-a-random-secret-key-in-production":
        raise ValueError(
            "CRITICAL SECURITY ERROR: You must configure a secure JWT_SECRET_KEY in your .env file "
            "when running in production mode (DEBUG=False)."
        )
        
    await connect_db()
    
    # Preload the embedding model and FAISS index
    from services.embedding_service import initialize as init_embedding
    init_embedding()
    
    logger.info("All services initialized and ready")
    yield
    # ── Shutdown ────────────────────────────────────────
    await disconnect_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Upload documents and interact with them using AI — OCR, classification, RAG Q&A, summarization, and structured data extraction.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # restrict to local Next.js server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Input Sanitization Middleware ───────────────────────
HTML_CLEAN_RE = re.compile(
    r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>"
    r"|\bon\w+\s*=\s*[\"'][^\"']*[\"']"
    r"|\bon\w+\s*=\s*\w+"
    r"|javascript:\s*[^\"']*",
    re.IGNORECASE
)

def clean_html(text: str) -> str:
    """Strip script tags and inline handlers to prevent basic XSS while keeping markdown."""
    return HTML_CLEAN_RE.sub("", text)

def sanitize_value(val):
    if isinstance(val, str):
        return clean_html(val)
    elif isinstance(val, dict):
        return {k: sanitize_value(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_value(v) for v in val]
    return val

async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    request._receive = receive

@app.middleware("http")
async def sanitize_input_middleware(request: Request, call_next):
    """Sanitize incoming request JSON bodies against XSS payload components."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.body()
            if body:
                try:
                    data = json.loads(body.decode("utf-8"))
                    sanitized_data = sanitize_value(data)
                    sanitized_body = json.dumps(sanitized_data).encode("utf-8")
                    await set_body(request, sanitized_body)
                except Exception:
                    pass
    response = await call_next(request)
    return response

# ── Register routers ───────────────────────────────────
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(search_router)
app.include_router(extraction_router)
app.include_router(comparison_router)
app.include_router(advanced_router)


# ── Rate Limiting Middleware ────────────────────────────
rate_limit_store = defaultdict(list)
RATE_LIMIT = 30  # requests per minute

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple in-memory rate limiter — 30 requests/minute per IP."""
    client_ip = request.client.host
    now = time.time()
    # Clean old entries
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < 60]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again in a minute."},
        )
    rate_limit_store[client_ip].append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT - len(rate_limit_store[client_ip]))
    return response


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

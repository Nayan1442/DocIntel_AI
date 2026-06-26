FROM python:3.11-slim

# Install system deps (Tesseract OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (torch CPU-only first to avoid huge CUDA download)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --timeout=300 --retries=5 -r requirements.txt

# Pre-download embedding model to cache it in the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/documents data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

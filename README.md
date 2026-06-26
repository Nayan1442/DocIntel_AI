# 🧠 DocIntel AI — AI Document Intelligence Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Groq](https://img.shields.io/badge/Groq%20LLM-F55036?style=for-the-badge&logoColor=white)](https://groq.com/)

DocIntel AI is a production-ready, full-stack AI Document Intelligence and retrieval-augmented generation (RAG) platform. It allows users to upload complex, unstructured files (such as invoices, contracts, resumes, and reports) and perform real-time extraction, analysis, Q&A, and comparative studies using an intelligent multi-agent orchestration architecture.

The platform's backend is built with FastAPI and Python, integrating LangChain to coordinate specialized agents (QA, extraction, sentiment, summary, and comparison). Document ingestion is designed as a resilient, asynchronous background pipeline: uploaded files undergo automated OCR (PyMuPDF/Tesseract), semantic chunking, and metadata classification, and are vectorized using SentenceTransformers before being indexed into a local FAISS vector store. The backend also features a multi-provider LLM client with auto-failover capabilities (routing requests between Groq and OpenRouter to prevent rate-limiting or key-expiry downtime) and strict production security assertions.

The frontend is a modern Next.js (React) application. It provides a premium, responsive dashboard featuring a real-time ingestion pipeline tracker (polling document status from MongoDB), an SVG-based statistics donut chart for document distribution, and deep-linked chat routing.

---


## ⚙️ Core Architecture & Premium Features

### 1. Asynchronous Ingestion & Real-Time Progress Tracker
* **Background Processing**: File uploads are processed asynchronously using FastAPI `BackgroundTasks`. The server immediately returns a queue receipt while the document goes through a staged ingestion pipeline:
  1. **OCR Extraction** (`20%`): Extracts text using PyMuPDF and Tesseract OCR engines.
  2. **Text Chunking** (`45%`): Splits text into semantic chunks for vector indexing.
  3. **Classification & Summarization** (`65%`): Categorizes (Invoices, Contracts, Resumes, Reports) and creates summaries concurrently.
  4. **Vector Embedding & FAISS Indexing** (`85%`): Embeds text chunks via `all-MiniLM-L6-v2` and inserts them into the FAISS vector index.
  5. **Pipeline Complete** (`100%`): Marks status as completed and saves chunks to MongoDB.
* **Live UI Status**: Next.js client polls the document status dynamically, rendering active steps, animations, and progress percentages in real time.

### 2. Multi-Provider LLM Resiliency (Groq + OpenRouter)
* To guarantee high availability, the centralized LLM client is built with an **automatic provider failover loop**.
* If a primary endpoint (e.g., Groq) experiences rate limits, network timeouts, or authorization errors, the client automatically catches the error, logs a warning, switches to a fallback provider (e.g., OpenRouter), and retries the request seamlessly.

### 3. Dashboard Visuals & SVG Charts
* **SVG Stats ring**: Upgraded linear CSS progress bars on the Dashboard to a custom, interactive SVG Donut chart displaying categorization distributions dynamically.
* **Deep-Linked Chat Shortcuts**: Added quick "Chat with Doc" actions next to each document. Clicking a shortcut routes to the chat window pre-selected with the corresponding document ID.

### 4. Interactive RAG Chat & Voice Queries
* **Server-Sent Events (SSE)**: Streams answers token-by-token for a highly responsive typing effect.
* **Web Speech Integration**: Allows voice queries directly inside the chat wrapper via browser-native SpeechRecognition.
* **Context Grounding**: Displays the source chunks used by the retriever and calculates a custom confidence score based on vector search cosine similarity.
* **Smart Follow-ups**: Dynamically extracts key points from responses to propose relevant follow-up questions.

### 5. Document Comparison & Sentiment Tone
* **Side-by-Side Comparison**: Compares two separate documents concurrently to outline key differences, overlapping similarities, and actionable recommendations.
* **Metadata Auto-Tagging**: Scans texts for critical keywords and entities (emails, organization names, dates, financial amounts).
* **Section Sentiment**: Evaluates overall sentiment and maps section-specific tones with associated confidence indexes.

---

## 🛠️ Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14, React, Lucide Icons | Premium styling with Dark Theme, Glassmorphism, and spring animations. |
| **Backend** | FastAPI, Uvicorn, Aiofiles | High-concurrency Python ASGI server with asynchronous file streaming. |
| **Database** | MongoDB | Storing user profiles, document schemas, conversation records, and text chunks. |
| **Vector DB**| FAISS (Facebook AI Similarity Search) | In-memory indexing and L2 distance similarity matching. |
| **Embeddings**| SentenceTransformers (`all-MiniLM-L6-v2`)| Locally preloaded weights inside the container for instant cold starts. |
| **LLMs** | Groq API (Llama 3), OpenRouter | High-throughput, token-streaming endpoints with failover capabilities. |
| **OCR** | Tesseract OCR, PyMuPDF | OCR preprocessing, text normalization, and PDF reading. |

---

## 📁 Project Structure

```
ai-document-intelligence/
├── backend/
│   ├── main.py                # FastAPI entry point & input sanitization
│   ├── config.py              # Configuration & environment validation
│   ├── api/                   # REST API Endpoints
│   │   ├── auth.py            # Password complexity & JWT endpoints
│   │   ├── upload.py          # Asynchronous upload pipeline & polling details
│   │   ├── query.py           # RAG Q&A routes
│   │   ├── search.py          # FAISS semantic search
│   │   ├── extraction.py      # Entity & auto-tagging routes
│   │   ├── comparison.py      # Side-by-side document comparison
│   │   └── advanced.py        # Stats aggregation, chat history & streams
│   ├── services/              # Ingest & AI Service Layer
│   │   ├── ocr_service.py
│   │   ├── embedding_service.py
│   │   ├── llm_client.py      # Auto-failover client (Groq <-> OpenRouter)
│   │   └── rag_service.py     # Embeddings search & context-grounded prompting
│   ├── database/              # MongoDB operations and schemas
│   │   ├── db.py
│   │   └── models.py
│   └── utils/                 # General helpers (chunking, cleaning, lang-detect)
├── frontend/
│   ├── pages/                 # Next.js Routes
│   │   ├── _app.js            # Route guards, loaders, and context config
│   │   ├── login.js           # Auth (Register / Login tab switcher)
│   │   ├── index.js           # Landing page
│   │   └── app/               # Application Area
│   │       ├── index.js       # Dashboard, SVG Donut & Document List
│   │       ├── upload.js      # Drag-and-drop zone with Pipeline Step Tracker
│   │       ├── chat.js        # SSE Streaming chat with Deep Links
│   │       ├── search.js      # Semantic vector search view
│   │       ├── compare.js     # Side-by-side diff widget
│   │       └── document.js    # Doc analysis details, Sentiment, Report, Copy block
│   ├── styles/
│   │   └── globals.css        # Global Vanilla CSS style sheets and transitions
│   └── components/            # AuthContext state provider
├── docker-compose.yml         # Container mapping with health checks
└── .env.example               # Template environment parameters
```

---

## 🏃 Quick Start

### 1. Setup Environment Variables
Create a `.env` file in the project root:
```env
# Server details
DEBUG=True
JWT_SECRET_KEY=generate-a-secure-random-key-here

# LLM Providers (openrouter or groq)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

### 2. Run with Docker Compose (Recommended)
This runs the full stack, including MongoDB, pre-caches the embedding model, and launches healthchecks:
```bash
docker compose up --build
```
* **Frontend**: Access the Next.js portal at [http://localhost:3000](http://localhost:3000)
* **Backend**: FastAPI interactive docs can be inspected at [http://localhost:8000/docs](http://localhost:8000/docs)
* **MongoDB**: Accessible on port `27017`

### 3. Run Manually (Local Development)

#### Backend Setup
Make sure you have `Tesseract OCR` installed on your machine.
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Reference

### Document Operations
* `POST` `/upload-document`: Upload a single PDF/image. Schedules asynchronous analysis.
* `POST` `/batch-upload`: Upload up to 10 files. Returns execution ids.
* `GET` `/documents`: List documents, returns classification metadata, `progress_pct`, and `status_detail`.
* `GET` `/documents/{id}`: Detailed metadata, text summary, and parsed fields.
* `DELETE` `/documents/{id}`: Cleans up database collections, FAISS vectors, and files on disk.

### AI & Vector Operations
* `POST` `/chat/stream`: Stream context-grounded chat responses (SSE) using conversation history.
* `POST` `/search`: Run semantic vector query across chunks.
* `GET` `/report/{id}`: Generates insights report.
* `POST` `/auto-tag/{id}`: Auto-extract entities (organizations, amounts, emails) and keywords.
* `POST` `/sentiment/{id}`: Performs tone evaluation and key emotional parsing.
* `POST` `/compare-documents`: Analyzes similarities, differences, and recommendations for two files.
* `GET` `/stats`: Aggregated database size metrics, type distribution and conversation totals.

---

## 🔐 Production Hardening

* **Security Assertions**: Backend crashes on launch if `DEBUG=False` (production) while using the default JWT secret key, preventing accidental vulnerability exposures.
* **Input Sanitization**: Request bodies are scrubbed of HTML script injections via FastAPI middleware before hitting DB routers.
* **Complexity Validation**: Restricts signup registrations unless passwords have at least 8 characters, a number, a letter, and a special character.

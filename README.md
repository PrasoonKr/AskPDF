# DocMind — Local-First AI Research Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00599C.svg)](https://github.com/facebookresearch/faiss)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black.svg?logo=ollama)](https://ollama.com)

**DocMind** is an advanced, local-first AI Research Assistant powered by a production-grade **Retrieval-Augmented Generation (RAG)** pipeline. It allows users to upload complex research papers, technical manuals, and PDF documents, creating an isolated knowledge base to answer user queries with grounded citations and zero hallucinations.

---

## Key Highlights

- 🔍 **Two-Stage Hybrid Search**: Combines dense semantic vector search (**FAISS**) with sparse keyword search (**BM25**), fused via **Reciprocal Rank Fusion (RRF)**.
- 🎯 **Cross-Encoder Re-ranking**: Evaluates full self-attention across candidate passages using `BAAI/bge-reranker-base` for maximum precision.
- 🧠 **Contextual Query Rewriting**: Resolves multi-turn conversational references and pronouns with an intelligent LLM query rewriter.
- 🔒 **100% Privacy & Local Inference**: Runs quantized open-source LLMs (`qwen2.5:3b`, `llama3.2:3b`) locally through **Ollama**—no data ever leaves your machine.
- 👥 **Multi-Tenant Data Isolation**: Securely isolates document storage, vector indices, and chat sessions per user account.
- 🔑 **Google OAuth 2.0 & JWT Security**: Role-based access control with Google OAuth token verification and custom signed JWT bearer sessions.
- 📊 **Inspectable Retrieval Trace**: Complete transparency into the RAG lifecycle via an interactive UI accordion showing rewritten queries, semantic scores, keyword matches, and reranked distributions.
- ⚡ **Modern Full-Stack UI**: Responsive, glassmorphism dark-mode frontend built with React, TypeScript, Material UI (MUI), and Redux Toolkit (RTK) Query.

---

## Architecture Overview

```
User Query ──► Query Rewriter ──► Parallel Retrieval (FAISS Dense + BM25 Sparse)
                                                  │
                                                  ▼
                                       Reciprocal Rank Fusion (RRF)
                                                  │
                                                  ▼
                                       Cross-Encoder Re-ranking (BGE)
                                                  │
                                                  ▼
                                       Context Construction & Guardrails
                                                  │
                                                  ▼
                                       Local LLM Generator (Ollama)
                                                  │
                                                  ▼
                                       Answer + Source Chips + Trace
```

For complete architectural details, sequence diagrams, and lifecycle specifications, see:
- 📖 [Application Flow & Sequence Guide](docs/application_flow.md)
- 🏛️ [Architecture Specification](docs/architecture.md)
- 🎯 [SDE Interview Q&A Guide](docs/interview_qa.md)

---

## Tech Stack

| Domain | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Material UI (MUI), Redux Toolkit (RTK Query), React Router, React Markdown |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, PyPDF / PyMuPDF (`fitz`), Pydantic |
| **Vector DB & Search** | FAISS (`IndexFlatIP`), `rank_bm25` (BM25Okapi), Reciprocal Rank Fusion |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (384 dimensions, normalized L2) |
| **Reranker Model** | `BAAI/bge-reranker-base` (Cross-Encoder) |
| **LLM Inference** | Ollama (`qwen2.5:3b` / `llama3.2:3b`) |
| **Auth & Security** | Google OAuth 2.0 (`google-auth`), PyJWT (HS256) |

---

## Directory Structure

```text
├── backend/
│   ├── api/                  # FastAPI routers, schemas, dependencies, and app entry
│   │   ├── routers/          # auth, chat, documents, health, sessions
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── dependencies.py   # Auth & multi-tenant application injection
│   ├── config.py             # Global pipeline hyperparameters and model configs
│   ├── documents/            # User-isolated raw PDF storage
│   ├── embeddings/           # SentenceTransformers embedding services
│   ├── evaluation/           # Evidence and retrieval evaluation utilities
│   ├── ingestion/            # PDF extraction, chunking, and pipeline coordination
│   ├── llm/                  # Ollama client, generator, and memory managers
│   ├── models/               # Domain models (Document, Page, SearchResult)
│   ├── prompts/              # Prompt templates and context builders
│   ├── query/                # LLM & rule-based query rewriters
│   ├── reranking/            # Cross-encoder re-ranking implementation
│   ├── retrieval/            # FAISS DocumentStore, BM25, and HybridSearch
│   ├── services/             # Research assistant application orchestrator
│   └── storage/              # Persisted user vector databases and indices
├── frontend/
│   ├── src/
│   │   ├── api/              # RTK Query API slice and cache definitions
│   │   ├── components/       # Layout, ChatInterface, DocumentList, Uploader
│   │   ├── pages/            # Login and view pages
│   │   └── theme/            # Material UI dark theme configuration
├── docs/
│   ├── application_flow.md   # Step-by-step system execution flows & sequence diagrams
│   ├── architecture.md       # Technical specification and DDD architecture
│   └── interview_qa.md       # Comprehensive SDE interview preparation guide
```

---

## Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Ollama**: [Download & Install Ollama](https://ollama.com)

---

### 1. Pull Local LLM Model
Ensure Ollama is running and pull the lightweight Qwen 2.5 model:
```bash
ollama run qwen2.5:3b
```

---

### 2. Configure Environment Variables

**Backend Configuration (`backend/.env`):**
```bash
cp backend/.env.example backend/.env
```
Populate `backend/.env`:
```env
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
JWT_SECRET=your_super_secret_jwt_key_for_ai_research_assistant
```

**Frontend Configuration (`frontend/.env`):**
```bash
cp frontend/.env.example frontend/.env
```
Populate `frontend/.env`:
```env
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
```

---

### 3. Backend Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

---

### 4. Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### Start Backend API Server
From the project root:
```bash
uvicorn backend.api.app:app --reload
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`

### Start Frontend Client
In a separate terminal:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser, sign in with your Google account, and start researching!

---

## Diagnostic Health API

You can inspect the live status of the system at any time by calling `GET /health`:

```json
{
  "status": "healthy",
  "timestamp": "2026-08-06T17:50:00.000000Z",
  "services": {
    "api": "online",
    "ollama": {
      "status": "connected",
      "models": ["qwen2.5:3b"]
    }
  },
  "config": {
    "llm_model": "qwen2.5:3b",
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "reranker_model": "BAAI/bge-reranker-base",
    "chunk_size": 400,
    "top_k": 10,
    "rerank_top_k": 5
  }
}
```

---

## License
MIT License. Created for local, privacy-first, grounded AI research.
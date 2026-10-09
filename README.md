# AskPDF — Local-First AI Research Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00599C.svg)](https://github.com/facebookresearch/faiss)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black.svg?logo=ollama)](https://ollama.com)

**AskPDF** is an advanced, local-first AI Research Assistant powered by a production-grade **Retrieval-Augmented Generation (RAG)** pipeline. It allows users to upload complex research papers, technical manuals, and PDF documents, creating an isolated knowledge base to answer user queries with grounded citations and zero hallucinations.

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
| **Embedding Model** | Local: `BAAI/bge-small-en-v1.5` <br> Prod: Cohere Embeddings |
| **Reranker Model** | Local: `BAAI/bge-reranker-base` <br> Prod: Cohere Rerank |
| **LLM Inference** | Local: Ollama (`qwen2.5:3b`) <br> Prod: AWS Bedrock via OpenAI Proxy (`openai.gpt-oss-120b`) |
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
COHERE_API_KEY=your_cohere_api_key
OPENAI_API_KEY=your_aws_bedrock_bearer_token
OPENAI_BASE_URL=https://bedrock-mantle.ap-south-1.api.aws/v1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-bucket-name
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

# 2. Install dependencies (Local Development)
pip install -r backend/requirements.txt

# Or for Production (Excludes Torch/Ollama):
pip install -r backend/requirements-prod.txt
```

---

### 4. Frontend Setup

```bash
cd frontend
npm install
```

---

## Running the Application

### Option A: Production Mode (AWS EC2)
Build the frontend and serve everything from FastAPI utilizing Cloud APIs:
```bash
# Build React frontend
cd frontend && npm run build && cd ..

# Start the server (serves both API and React UI in production mode)
# Windows:
$env:RAG_ENVIRONMENT="production"; uvicorn backend.api.app:app --host 0.0.0.0 --port 8000
# Linux/macOS:
export RAG_ENVIRONMENT="production"
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000
```
- Application: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`
- Readiness: `http://localhost:8000/api/health/ready`

### Option B: Development Mode (Two Servers + Hot Reload)
```bash
# Terminal 1: Backend
uvicorn backend.api.app:app --reload

# Terminal 2: Frontend (Vite proxies /api → localhost:8000)
cd frontend && npm run dev
```
Open `http://localhost:5173` — Vite hot-reloads frontend changes and proxies API calls to the backend.

---

## API Endpoints

All API routes are prefixed with `/api`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health + config overview |
| `GET` | `/api/health/ready` | Readiness probe (embedding, reranker, Ollama) |
| `POST` | `/api/auth/google` | Google OAuth login |
| `POST` | `/api/auth/dev-login` | Dev/guest login (no Google required) |
| `POST` | `/api/sessions` | Create chat session |
| `POST` | `/api/chat/stream` | Streaming RAG chat (SSE) |
| `GET` | `/api/documents` | List uploaded documents |
| `POST` | `/api/documents` | Upload PDF(s) |
| `DELETE` | `/api/documents/{filename}` | Delete a document |

### Health Check (`GET /api/health`)

```json
{
  "status": "healthy",
  "timestamp": "2026-09-29T14:59:33.000000Z",
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
    "rerank_top_k": 3
  }
}
```

### Readiness Check (`GET /api/health/ready`)

Returns `200` when all services are loaded, `503` if any are missing:
```json
{
  "ready": true,
  "timestamp": "2026-09-29T14:59:33.700825Z",
  "checks": {
    "embedding_model": "ready",
    "reranker": "ready",
    "ollama": "ready"
  }
}
```

---

## License
MIT License. Created for local, privacy-first, grounded AI research.
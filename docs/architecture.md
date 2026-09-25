# DocMind Architecture & Technical Specification

This document details the production-ready, domain-driven Retrieval-Augmented Generation (RAG) architecture of **DocMind (AI Research Assistant)**.

---

## 1. System Overview

**DocMind** is a local-first, privacy-focused AI research platform designed to ingest complex multi-page documents (PDFs), construct a high-precision hybrid semantic index, and deliver grounded, citation-backed answers to user queries with zero external data leakage.

The application adheres strictly to **Domain-Driven Design (DDD)** and separation of concerns, operating in two primary operational phases:
1. **Multi-Tenant Ingestion Mode**: Extracts text, structures chunk hierarchies, and persists dual-index representations (dense vector + sparse lexical) isolated per user.
2. **Interactive Hybrid RAG Mode**: Loads persisted indices for sub-second retrieval, applies query contextualization, fuses dense and sparse candidate pools, re-ranks with cross-encoders, and generates grounded responses via local LLMs.

---

## 2. Core Domain Models

The domain logic is strictly modeled using immutable Python `dataclasses` located in `backend/models/`:

- **`SourceDocument`**: Encapsulates metadata of the raw uploaded file (filename, absolute path, user scope).
- **`Page`**: Represents an extracted document page preserving original document boundaries and page indexing.
- **`Document`**: The atomic retrieval unit containing:
  - `chunk_id` (Unique identifier)
  - `source` (`SourceDocument`)
  - `page` (Page number)
  - `text` (The chunk body)
- **`SearchResult`**: Wraps a matched `Document` alongside its computed relevance `score`.
- **`IngestionResult`**: Summary metric entity reporting processed documents and generated chunk counts.

---

## 3. The Ingestion Pipeline

The ingestion pipeline converts raw binary PDFs into search-optimized indices. It is coordinated by `IngestionPipeline`:

```text
PDF Upload -> Page Extractor (PyMuPDF) -> Text Chunker -> Dual Indexer (Dense + Sparse) -> Disk Persistence
```

### Components:
1. **Loader & Validator**: Validates file integrity and ensures destination directory exists at `backend/documents/{user_email}/`.
2. **Extractor (`PyMuPDF / fitz`)**: Reads document streams into a structured `List[Page]`, preserving page numbers.
3. **Chunker (`Chunker`)**: 
   - Chunk Size: **400 words** (~500 tokens).
   - Overlap: **75 words** to prevent context loss across boundaries.
   - Enriches each chunk with metadata (source name, page number, unique chunk ID).
4. **Embedding Service (`SentenceTransformers`)**: 
   - Model: **`BAAI/bge-small-en-v1.5`** (384-dimensional dense vectors).
   - All embeddings are L2-normalized to enable fast dot-product cosine similarity computation.
5. **Document Store & FAISS**: Stores dense vectors in a **`faiss.IndexFlatIP`** (Inner Product) index and pickles `Document` metadata to `documents.pkl`.
6. **BM25 Keyword Index**: Constructs a sparse inverted index using **`rank_bm25.BM25Okapi`** over lowercased tokens.

### Multi-Tenant Persistence
All indices are stored with strict user segregation under `backend/storage/{user_email}/`:
- `faiss.index`: Dense vector index.
- `documents.pkl`: Chunk metadata and raw text.
- `bm25.pkl`: Pickled BM25 search structures.

---

## 4. The Two-Stage Hybrid Retrieval Pipeline

DocMind implements an advanced **Hybrid Retrieval + Re-ranking** architecture to overcome the classic blind spots of pure vector search.

```text
User Question -> Query Rewriter (LLM) -> [Dense FAISS + Sparse BM25] -> Reciprocal Rank Fusion (RRF) -> Cross-Encoder Re-ranker -> Context Builder -> LLM Generator
```

### Pipeline Stages:

1. **Contextual Query Rewriting (`LLMRewriter`)**:
   - Takes current turn, recent chat history, and conversation summary.
   - Outputs a self-contained, disambiguated search query (e.g., resolving pronouns like "it" or "the latter").
   - Post-processes output to sanitize hyphens or formatting artifacts.

2. **Parallel Hybrid Search**:
   - **Dense Retrieval:** Generates a query embedding with `bge-small-en-v1.5` and searches the user's FAISS index for the Top-10 semantic neighbors.
   - **Sparse Retrieval:** Tokenizes the query into lowercase tokens and computes BM25 scores across the document corpus for the Top-10 exact keyword matches.

3. **Reciprocal Rank Fusion (RRF)**:
   - Merges dense and sparse rankings using the rank fusion formula ($k=60$):
     $$RRF(d) = \sum_{m \in \{Dense, Sparse\}} \frac{1}{60 + r_m(d)}$$
   - Generates a balanced candidate list of the Top-10 chunks.

4. **Cross-Encoder Re-Ranking (`CrossEncoderReranker`)**:
   - Model: **`BAAI/bge-reranker-base`**.
   - Computes full joint cross-attention between `(Query, Chunk)` pairs.
   - Sorts candidates by true semantic relevance and selects the **Top-5** highest-scoring chunks.

5. **Similarity Threshold Guard**:
   - Filters out chunks with relevance scores below `SIMILARITY_THRESHOLD = 0.40`.
   - If no chunks pass, injects a fallback message instructing the LLM that no context was found.

---

## 5. Grounded LLM Generation & Citation Attribution

1. **Context Building (`ContextBuilder`)**: Formats retrieved passages with explicit `[Document N]` delimiters, source filenames, and page numbers.
2. **Prompt Builder (`builder.py`) & Template (`templates.py`)**:
   - Strictly separates system instructions into a native `{"role": "system"}` message sent to the local LLM.
   - Prevents small-model context decay by placing an explicit grounding constraint at the bottom of the prompt.
3. **Local LLM Generator (`OllamaClient`)**:
   - Default Model: **`qwen2.5:3b`** (or `llama3.2:3b`).
   - Runs locally via Ollama with `temperature = 0.2` for deterministic, hallucination-free generation.
4. **Citation Extraction & Fallback**:
   - Automatically detects inline citations (e.g., `[system_design.pdf, Page 17]`).
   - If the LLM omits explicit citation formatting, the backend automatically falls back to attributing all high-confidence context documents passed to the prompt.

---

## 6. Multi-Tenancy & Security Architecture

1. **Google OAuth 2.0 Authentication**:
   - Frontend verifies Google ID tokens using `@react-oauth/google`.
   - Backend validates signatures via `google.oauth2.id_token` against `GOOGLE_CLIENT_ID`.
2. **Application JWT Session**:
   - Issues custom HS256-signed JWTs containing `sub`, `email`, and expiration claims.
   - Fast token validation via FastAPI `HTTPBearer` security dependency.
3. **Application Cache Isolation**:
   - `application_cache[user_email]` lazily initializes isolated application instances.
   - User A has zero access to the document storage, vector database, or session memory of User B.

---

## 7. Web Application & Observability

### FastAPI REST Layer (`backend/api/`):
- `POST /auth/google`: Authenticates Google credentials and issues JWT.
- `GET /documents`: Lists all uploaded documents for the active user.
- `POST /documents`: Ingests and indexes uploaded PDF files.
- `DELETE /documents/{filename}`: Removes a document and updates indices.
- `DELETE /documents`: Clears the user's entire knowledge base.
- `POST /sessions`: Creates an isolated chat session.
- `POST /chat`: Submits questions and returns generated answers with source chips and retrieval trace logs.
- `GET /health`: Diagnostic health check reporting Ollama connectivity, available local models, active configurations, and system uptime.

### React + TypeScript Frontend (`frontend/`):
- **Redux Toolkit Query (`apiSlice.ts`)**: Manages caching, optimistic updates, tag invalidation (`['Documents']`), and memory resets on logout.
- **UI Components**:
  - `Layout.tsx`: Responsive drawer layout with mobile drawer toggles and user profile controls.
  - `ChatInterface.tsx`: Markdown rendering (`react-markdown`, `remark-gfm`), Stop generation button, Source citation chips, and an expandable **Retrieval Trace Accordion** for complete transparency.
  - `DocumentList.tsx` & `DocumentUploader.tsx`: Ingestion tracking and knowledge base management.

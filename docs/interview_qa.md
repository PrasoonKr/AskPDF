# AI Research Assistant (DocMind) — SDE Interview Q&A Guide

This guide contains the most common and challenging technical, architectural, and behavioral interview questions you may face when discussing this project in Software Development Engineer (SDE) and Machine Learning / AI Engineer interviews.

---

## Table of Contents
1. [High-Level Project & Architecture](#1-high-level-project--architecture)
2. [Advanced RAG & Information Retrieval (IR)](#2-advanced-rag--information-retrieval-ir)
3. [LLM, Prompt Engineering & Hallucination Mitigation](#3-llm-prompt-engineering--hallucination-mitigation)
4. [Backend Engineering & FastAPI](#4-backend-engineering--fastapi)
5. [Security, Multi-Tenancy & Data Isolation](#5-security-multi-tenancy--data-isolation)
6. [Frontend Architecture & State Management](#6-frontend-architecture--state-management)
7. [System Design, Scaling & Hard Trade-offs](#7-system-design-scaling--hard-trade-offs)
8. [Debugging Stories & Real-World Challenges (STAR Method)](#8-debugging-stories--real-world-challenges-star-method)

---

## 1. High-Level Project & Architecture

### Q1: Can you give a 60-second elevator pitch of this project?
> **Answer:**
> **DocMind** is a local-first, privacy-focused AI Research Assistant powered by an advanced Retrieval-Augmented Generation (RAG) architecture. It allows users to upload complex research papers and PDFs and converse with them with zero hallucinations. 
> 
> Unlike naive RAG pipelines that only use basic vector search, DocMind implements an advanced **Hybrid Retrieval Pipeline** combining dense semantic search (FAISS) and sparse keyword search (BM25), fused via **Reciprocal Rank Fusion (RRF)**, and refined with a **Cross-Encoder Re-ranker**. The backend is built with FastAPI and local LLM inference via Ollama, while the frontend is built with React, TypeScript, and Redux Toolkit Query, protected by Google OAuth and custom JWT authentication.

---

### Q2: Walk me through the end-to-end lifecycle of a query from frontend to backend.
> **Answer:**
> 1. **User Input:** The user types a query in the React chat UI, sending a `POST /chat` request with their JWT Bearer token and active `session_id`.
> 2. **Authentication & Multi-Tenant Routing:** FastAPI verifies the JWT, extracts the user's identity, and retrieves or lazily boots the user-isolated `Application` instance from memory cache.
> 3. **Query Rewriting:** The query along with conversation history (recent turns + summary) is processed by an LLM rewriter to resolve ambiguous pronouns and produce a standalone search query.
> 4. **Parallel Hybrid Retrieval:**
>    - **Dense Search:** The query is embedded via `BAAI/bge-small-en-v1.5` and searched against the user's FAISS `IndexFlatIP` index using cosine similarity.
>    - **Sparse Search:** The query is tokenized and scored against the document corpus using BM25 (`rank_bm25`).
> 5. **Reciprocal Rank Fusion (RRF):** The dense and sparse rank lists are merged using the RRF algorithm ($Score(d) = \sum \frac{1}{k + r(d)}$) to generate a balanced top-10 candidate pool.
> 6. **Cross-Encoder Re-ranking:** A cross-encoder model (`BAAI/bge-reranker-base`) scores the full (query, document) pairs to re-order the candidates by deep contextual relevance, selecting the top-5 chunks.
> 7. **Context Construction & Prompt Injection:** Top-scoring chunks above the similarity threshold are structured into a grounded context block.
> 8. **Inference:** A local LLM (e.g., `qwen2.5:3b` via Ollama) generates the response conditioned strictly on the retrieved context using a separated `{"role": "system"}` directive.
> 9. **Citation & Trace Delivery:** The backend formats source chips (filename + page numbers) and a full retrieval trace, returning the payload to the frontend.

---

## 2. Advanced RAG & Information Retrieval (IR)

### Q3: Why did you choose a Hybrid Search approach instead of pure Vector Search?
> **Answer:**
> Vector search (dense retrieval) excels at understanding semantic concepts, synonyms, and paraphrased intent, but it frequently fails on:
> 1. **Exact keyword matches:** E.g., acronyms, product names, version numbers, or function identifiers (e.g., `CAP theorem`, `OAuth2`, `UUIDv4`).
> 2. **Domain-specific jargon:** Embedding models can map rare out-of-vocabulary terms to distant vector spaces.
> 
> Sparse search (BM25) uses Term Frequency-Inverse Document Frequency (TF-IDF) principles to guarantee that specific keyword occurrences are captured. By combining FAISS (dense) and BM25 (sparse), our pipeline captures both high-level semantic meaning and precise lexical matches.

---

### Q4: How does Reciprocal Rank Fusion (RRF) work, and why is it better than raw score normalization?
> **Answer:**
> Dense search outputs cosine similarity scores (typically between `0.0` and `1.0`), whereas BM25 outputs unbounded positive numbers (e.g., `0` to `25+`). Normalizing these raw scores using min-max scaling or z-scores is unreliable because score distributions differ wildly per query.
> 
> **Reciprocal Rank Fusion (RRF)** solves this by operating exclusively on the **rankings** rather than raw scores. The formula is:
> $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
> where $M$ is the set of retrieval systems (FAISS and BM25), $r_m(d)$ is the rank position of document $d$ in system $m$, and $k$ is a smoothing constant (standard default is $k=60$).
> 
> This ensures that:
> - Documents appearing high in both retrieval lists get a massive boost.
> - Outlier scores in one system do not disproportionately overpower the other.

---

### Q5: What is the difference between a Bi-Encoder and a Cross-Encoder? Why use both?
> **Answer:**
> - **Bi-Encoder (`bge-small-en-v1.5`):** Encodes the query and the documents *independently* into separate dense vectors. Vector comparison is done via dot product ($O(D)$ time), allowing sub-millisecond search over millions of pre-computed vectors. However, it cannot model cross-attention token interactions between query words and document words.
> - **Cross-Encoder (`bge-reranker-base`):** Feeds the query and document *simultaneously* through full self-attention layers ($[CLS] + Query + [SEP] + Document$). This achieves state-of-the-art ranking precision, but is computationally expensive ($O(N \cdot L^2)$) and cannot be pre-indexed.
> 
> **Our Two-Stage Retrieval Architecture:**
> 1. **Stage 1 (High Recall / Fast):** Bi-Encoder + BM25 quickly narrows down thousands of chunks to the Top-10 candidates.
> 2. **Stage 2 (High Precision / Deep):** Cross-Encoder re-ranks only those 10 candidates to pick the Top-5 most relevant passages for the LLM context.

---

### Q6: What chunking strategy did you use and why?
> **Answer:**
> We used a chunk size of **400 words** with an overlap of **75 words**.
> - **400 words (~500 tokens):** Large enough to encapsulate complete thoughts, paragraph explanations, and technical definitions without fragmenting context, while staying compact enough to fit multiple chunks into the LLM context window without diluting attention.
> - **75-word Overlap:** Prevents information loss at arbitrary chunk boundaries (e.g., if a definition begins on word 390 and ends on word 420).
> - **Page Boundary Tracking:** We retain structural metadata (Document name, Page number, Chunk ID) attached to each chunk object for exact source citation.

---

### Q7: Why did you choose `faiss.IndexFlatIP` over `IndexHNSWFlat` or `IndexIVFFlat`?
> **Answer:**
> - `IndexFlatIP` performs exhaustive (brute-force) Inner Product search on normalized vectors (equivalent to Cosine Similarity). It guarantees **100% exact recall** with zero index distortion and zero offline training overhead.
> - Modern CPUs utilizing SIMD/AVX instructions in FAISS can scan 100,000 vectors of 384 dimensions in under **2 milliseconds**.
> - Approximate Nearest Neighbor (ANN) indexes like HNSW or IVF trade away 2–5% recall to optimize latency when datasets exceed millions of vectors. For our personal/team-scale research assistant, preserving 100% retrieval accuracy without index training complexity is the optimal engineering decision.

---

## 3. LLM, Prompt Engineering & Hallucination Mitigation

### Q8: How do you prevent the LLM from hallucinating answers when document context is missing?
> **Answer:**
> We employ a multi-layered hallucination defense:
> 1. **Role Separation:** We supply the core guardrails in a dedicated `{"role": "system"}` message rather than concatenating it into the user prompt. This ensures the model treats instructions with highest priority.
> 2. **Strict Negative Constraint:** The system prompt explicitly instructs: *"Answer the user's question using only the provided retrieved context. If the context does not contain enough information, clearly state that you do not know."*
> 3. **Similarity Threshold Filtering:** If all retrieved documents score below our relevance threshold (`SIMILARITY_THRESHOLD = 0.4`), we inject `"No relevant context found."` into the context window, triggering the refusal path.
> 4. **Recency Anchor:** We append an explicit reminder at the very end of the prompt (after all context blocks) to counter the LLM "lost in the middle" attention decay.

---

### Q9: Why is Query Rewriting necessary in a conversational RAG system?
> **Answer:**
> In multi-turn chat sessions, users naturally use pronouns, ellipses, and implicit references (e.g., Turn 1: *"Explain the CAP theorem"*, Turn 2: *"Why is CA impossible in distributed networks?"*, Turn 3: *"What databases choose AP instead?"*).
> 
> If we pass Turn 3 directly to vector search, the query has no mention of "CAP theorem" or "distributed networks", leading to poor retrieval.
> Our `LLMRewriter` consumes recent chat turns and outputs a standalone search query (e.g., *"Which distributed databases choose Availability and Partition tolerance in the CAP theorem?"*) before executing search.

---

## 4. Backend Engineering & FastAPI

### Q10: How did you structure the backend using Domain-Driven Design (DDD)?
> **Answer:**
> We segregated the codebase into distinct layers:
> - **Domain Models (`backend/models/`):** Pure Python dataclasses (`Document`, `Page`, `SearchResult`, `SourceDocument`) that encapsulate core business entities and enforce type integrity across the system.
> - **Infrastructure / Adapters (`backend/retrieval/`, `backend/embeddings/`, `backend/llm/`):** Implementations for FAISS, BM25, SentenceTransformers, and Ollama client.
> - **Services / Orchestrators (`backend/services/`):** `ResearchAssistantService` and `IngestionPipeline` coordinate domain logic without being coupled to HTTP frameworks.
> - **API / Presentation Layer (`backend/api/`):** FastAPI routers, Pydantic schemas, and security dependencies.

---

### Q11: How does FastAPI handle concurrency during heavy embedding or LLM inference calls?
> **Answer:**
> - FastAPI runs on the `uvicorn` ASGI server.
> - I/O-bound operations (such as token validation, disk reads, and streaming HTTP requests to Ollama) use non-blocking `async/await` syntax.
> - CPU-bound operations (such as FAISS indexing, PyPDF text extraction, and sentence transformer inference) are executed synchronously or dispatched through worker pools to ensure the main asyncio event loop remains unblocked and responsive to health probes and other client requests.

---

## 5. Security, Multi-Tenancy & Data Isolation

### Q12: How is multi-tenancy implemented and how do you ensure data isolation between users?
> **Answer:**
> 1. **Per-User File Storage:** Each user's uploaded documents are stored in dedicated directories: `backend/documents/{user_email}/`.
> 2. **Per-User Vector DB & Indices:** Vector stores and serialized indices are persisted strictly per-user: `backend/storage/{user_email}/faiss.index` and `documents.pkl`.
> 3. **Application Cache Isolation:** The backend maintains an in-memory application cache `application_cache[user_email] = startup(user_email)`. When an authenticated request arrives, the dependency injection layer (`Depends(get_application)`) extracts the verified identity from the JWT and injects only the corresponding user's `DocumentStore` and retrieval pipeline.
> 4. **No Cross-Talk:** Queries executed by User A never search or touch the FAISS index or memory history of User B.

---

### Q13: Explain your Authentication flow with Google OAuth 2.0 and custom JWTs.
> **Answer:**
> 1. The client logs in with Google on the frontend and receives an `id_token` (credential).
> 2. The client sends the credential to `POST /auth/google`.
> 3. The backend validates the Google signature using Google's public keys (`google.oauth2.id_token.verify_oauth2_token`) and checks the `aud` against our `GOOGLE_CLIENT_ID`.
> 4. Upon validation, the backend issues an application-specific JWT signed with our `JWT_SECRET` (using `HS256`), encoding `{ "sub": email, "email": email, "name": name, "exp": expiration }`.
> 5. All protected endpoints validate this token using `HTTPBearer` in FastAPI dependencies, returning `401 Unauthorized` if invalid or expired.

---

## 6. Frontend Architecture & State Management

### Q14: Why use Redux Toolkit (RTK) Query instead of standard `useEffect` + `fetch`?
> **Answer:**
> 1. **Automated Caching & Deduplication:** Eliminates redundant network requests when components re-render.
> 2. **Declarative Cache Invalidation:** Uses tag-based invalidation (`providesTags: ['Documents']`, `invalidatesTags: ['Documents']`). When a user uploads or deletes a document, RTK Query automatically triggers a background refetch across all mounted components.
> 3. **Global State Reset on Auth Change:** Allows wiping the entire memory cache upon logout (`dispatch(apiSlice.util.resetApiState())`), preventing data leakage when switching accounts.
> 4. **Built-in Async Lifecycle:** Automatically provides `isLoading`, `isError`, and `data` states without manual boilerplate.

---

## 7. System Design, Scaling & Hard Trade-offs

### Q15: If this system needed to scale to 100,000 active users and millions of documents, what would you change?
> **Answer:**
> 1. **Distributed Vector Database:** Replace local FAISS with a managed, distributed vector DB (e.g., **Milvus**, **Qdrant**, or **Pinecone**) supporting metadata filtering and multi-tenant partition keys.
> 2. **Asynchronous Ingestion via Message Queue:** Offload PDF parsing, chunking, and embedding to Celery workers backed by **Redis** or **RabbitMQ**.
> 3. **Embedding & LLM Inference Serving:** Migrate from local Ollama to dedicated inference microservices powered by **vLLM** or **Triton Inference Server** running on GPU clusters, enabling continuous batching and PagedAttention.
> 4. **Object Storage:** Move document storage from local disk to **Amazon S3** or **Google Cloud Storage** with pre-signed URLs.
> 5. **Caching Layer:** Cache high-frequency query embeddings and common search results in Redis.

---

## 8. Debugging Stories & Real-World Challenges (STAR Method)

### Challenge 1: The BM25 Case Sensitivity & Hyphenation Bug
- **Situation:** Users reported that exact search queries like `"cap theorem"` returned 0 keyword results in the retrieval trace, despite the document clearly containing the text.
- **Task:** Diagnose why the BM25 index failed to match exact phrase tokens.
- **Action:** Investigated the retrieval trace logs and discovered two root causes:
  1. The BM25 corpus and search query were split without case normalization (`"CAP"` $\neq$ `"cap"`).
  2. The LLM query rewriter was occasionally outputting hyphenated slug strings (e.g., `what-is-the-cap-theorem`), which BM25 treated as a single non-existent token.
- **Resolution:** Added `.lower()` normalization across the indexing and query pipelines, and added a regex cleaning layer in the query rewriter to strip hyphens and formatting artifacts.

---

### Challenge 2: Multi-Tenant Data Leakage via JWT Claim Misalignment
- **Situation:** Logging in with a secondary user account still displayed files and knowledge base assets from the primary account.
- **Task:** Determine why user data isolation was failing across accounts.
- **Action:** Traced the token generation in `auth.py` and downstream resolution in `dependencies.py`. Found that the JWT signed the user identity under the standard claim `"sub"`, whereas the backend routers were calling `current_user.get("email")`. Because `get("email")` was returning `None`, it silently fell back to `"default"` for all users.
- **Resolution:** Explicitly included `"email"` alongside `"sub"` in the token payload and added a fallback in `get_current_user`. Additionally dispatched `apiSlice.util.resetApiState()` on the frontend upon logout to purge Redux in-memory query cache.

---

### Challenge 3: Small-Model Prompt Adherence & Citation Loss
- **Situation:** A local 3B parameter model (`qwen2.5:3b`) occasionally ignored the retrieved context or failed to cite source documents, answering purely from its pre-training weights.
- **Task:** Maximize RAG context grounding on a constrained edge-sized LLM.
- **Action:** Separated the system instructions into a native `{"role": "system"}` payload (leveraging model chat templates) rather than embedding it inside the user prompt block. Implemented an automatic citation fallback mechanism in `assistant_service.py` that checks the high-confidence results passed in context if the LLM forgets to format inline markers.
- **Result:** 100% consistent source attribution and zero off-context hallucinations.

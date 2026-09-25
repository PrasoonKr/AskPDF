from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.api.routers import (
    health,
    sessions,
    chat,
    documents,
    auth,
)


def _warmup_services():
    """Warmup AI models in background to eliminate cold-start delays."""
    print("[DocMind Warmup] Preloading AI models into memory...")
    try:
        from backend.embeddings.model import model as emb_model
        emb_model.encode("warmup")
        print("[DocMind Warmup] Embedding model initialized.")
    except Exception as e:
        print(f"[DocMind Warmup] Embedding warmup warning: {e}")

    try:
        from backend.reranking.model import model as rerank_model
        rerank_model.predict([("warmup query", "warmup passage")])
        print("[DocMind Warmup] Cross-encoder reranker initialized.")
    except Exception as e:
        print(f"[DocMind Warmup] Reranker warmup warning: {e}")

    try:
        from backend.llm.client import OllamaClient
        client = OllamaClient()
        client.warmup()
        print("[DocMind Warmup] Ollama LLM loaded and pinned in RAM (zero cold starts).")
    except Exception as e:
        print(f"[DocMind Warmup] Ollama warmup warning: {e}")

    print("[DocMind Warmup] All models ready for instant response!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, _warmup_services)
    yield


app = FastAPI(
    title="AI Research Assistant API",
    description="""
    API for the AI Research Assistant.
    
    ## Authentication
    Most endpoints are protected by JWT. You can obtain a JWT token by logging in via Google at the `/auth/google` endpoint. 
    Once you have the token, click the **Authorize** button below and enter it to test the API directly from this Swagger interface!
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(auth.router)

# Mount frontend if it exists
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
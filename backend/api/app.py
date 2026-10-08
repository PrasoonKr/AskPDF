import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import torch
    torch.set_num_threads(6)
except ImportError:
    pass

from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routers import (
    health,
    sessions,
    chat,
    documents,
    auth,
)


def _warmup_services():
    """Warmup AI models in background to eliminate cold-start delays."""
    env = os.getenv("RAG_ENVIRONMENT", "local").lower()
    if env == "production":
        print("[AskPDF Warmup] Running in production mode. Skipping local model warmup.", flush=True)
        return

    print("[AskPDF Warmup] Preloading AI models into memory...", flush=True)
    try:
        from backend.embeddings.model import model as emb_model
        emb_model.encode("warmup")
        print("[AskPDF Warmup] Embedding model initialized.", flush=True)
    except Exception as e:
        print(f"[AskPDF Warmup] Embedding warmup warning: {e}", flush=True)

    try:
        from backend.reranking.model import model as rerank_model
        rerank_model.predict([("warmup query", "warmup passage")])
        print("[AskPDF Warmup] Cross-encoder reranker initialized.", flush=True)
    except Exception as e:
        print(f"[AskPDF Warmup] Reranker warmup warning: {e}", flush=True)

    try:
        from backend.llm.client import OllamaClient
        client = OllamaClient()
        client.warmup()
        print("[AskPDF Warmup] Ollama LLM loaded into RAM (unloads after 5m of inactivity).", flush=True)
    except Exception as e:
        print(f"[AskPDF Warmup] Ollama warmup warning: {e}", flush=True)

    print("[AskPDF Warmup] All models ready for instant response!", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables (no-op if they already exist)
    from backend.database.session import engine
    from backend.database.models import Base
    Base.metadata.create_all(bind=engine)
    print("[AskPDF] Database tables initialized.", flush=True)

    # Block startup until all models are loaded — prevents cold-start on first query
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _warmup_services)
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

# All API routes under /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(auth.router)
app.include_router(api_router)

# Serve React frontend from build output
_frontend_dist = Path("frontend/dist")
if _frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Catch-all: serve index.html for any non-API route (SPA client-side routing)."""
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dist / "index.html")
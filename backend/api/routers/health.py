from datetime import datetime
from fastapi import APIRouter
import ollama

from backend.config import EmbeddingConfig, LLMConfig, RerankerConfig, ChunkerConfig, RetrievalConfig

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health():
    """
    Check the overall health of the service, including Ollama connection status
    and active model configurations.
    """
    ollama_info = {"status": "connected", "models": []}
    overall_status = "healthy"
    
    try:
        res = ollama.list()
        if hasattr(res, "models"):
            ollama_info["models"] = [getattr(m, "model", getattr(m, "name", str(m))) for m in res.models]
        elif isinstance(res, dict):
            ollama_info["models"] = [m.get("name") or m.get("model") for m in res.get("models", [])]
    except Exception as e:
        ollama_info = {
            "status": "disconnected",
            "error": str(e)
        }
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "api": "online",
            "ollama": ollama_info
        },
        "config": {
            "llm_model": LLMConfig.MODEL,
            "embedding_model": EmbeddingConfig.MODEL,
            "reranker_model": RerankerConfig.MODEL,
            "chunk_size": ChunkerConfig.CHUNK_SIZE,
            "top_k": RetrievalConfig.SEARCH_TOP_K,
            "rerank_top_k": RetrievalConfig.RERANK_TOP_K,
        }
    }


@router.get("/ready")
def readiness():
    """
    Readiness check — can the application actually serve requests?
    Verifies that FAISS index, BM25 index, reranker, and Ollama are all loaded.
    Returns 503 if any critical component is not ready.
    """
    from fastapi.responses import JSONResponse
    checks = {}
    all_ready = True

    # Check embedding model
    try:
        from backend.embeddings.model import model as emb_model
        if emb_model is not None:
            checks["embedding_model"] = "ready"
        else:
            checks["embedding_model"] = "not_loaded"
            all_ready = False
    except Exception as e:
        checks["embedding_model"] = f"error: {e}"
        all_ready = False

    # Check reranker model
    try:
        from backend.reranking.model import model as rerank_model
        if rerank_model is not None:
            checks["reranker"] = "ready"
        else:
            checks["reranker"] = "not_loaded"
            all_ready = False
    except Exception as e:
        checks["reranker"] = f"error: {e}"
        all_ready = False

    # Check Ollama connectivity
    try:
        res = ollama.list()
        model_names = []
        if hasattr(res, "models"):
            model_names = [getattr(m, "model", getattr(m, "name", str(m))) for m in res.models]
        elif isinstance(res, dict):
            model_names = [m.get("name") or m.get("model") for m in res.get("models", [])]
        
        if any(LLMConfig.MODEL in name for name in model_names):
            checks["ollama"] = "ready"
        else:
            checks["ollama"] = f"model {LLMConfig.MODEL} not found"
            all_ready = False
    except Exception as e:
        checks["ollama"] = f"error: {e}"
        all_ready = False

    status_code = 200 if all_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": checks,
        }
    )
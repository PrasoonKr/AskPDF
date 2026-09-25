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
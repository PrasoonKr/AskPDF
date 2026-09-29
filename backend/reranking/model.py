from sentence_transformers import CrossEncoder
from backend.config import RerankerConfig

_model = None


def get_reranker_model():
    global _model
    if _model is None:
        # Free Ollama memory if active to avoid Windows commit limit
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=b'{"model": "qwen2.5:3b", "keep_alive": 0}',
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=1)
        except Exception:
            pass

        _model = CrossEncoder(
            RerankerConfig.MODEL,
            model_kwargs={"low_cpu_mem_usage": False}
        )
    return _model


class _LazyModelProxy:
    def predict(self, *args, **kwargs):
        return get_reranker_model().predict(*args, **kwargs)


model = _LazyModelProxy()
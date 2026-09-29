from sentence_transformers import SentenceTransformer
from backend.config import EmbeddingConfig

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            EmbeddingConfig.MODEL,
            model_kwargs={"low_cpu_mem_usage": False},
        )
    return _model


class _LazyEmbeddingProxy:
    def encode(self, *args, **kwargs):
        return get_embedding_model().encode(*args, **kwargs)

    def get_embedding_dimension(self, *args, **kwargs):
        return get_embedding_model().get_embedding_dimension(*args, **kwargs)


model = _LazyEmbeddingProxy()
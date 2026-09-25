from sentence_transformers import SentenceTransformer

from backend.config import EmbeddingConfig

model = SentenceTransformer(EmbeddingConfig.MODEL)
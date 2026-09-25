from sentence_transformers import CrossEncoder
from backend.config import RerankerConfig

model = CrossEncoder(RerankerConfig.MODEL)
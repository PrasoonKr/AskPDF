from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.evaluation.evaluator import RetrievalEvaluator


embedding_service = EmbeddingService()

document_store = DocumentStore(
    embedding_service
)

document_store.load()

evaluator = RetrievalEvaluator(
    embedding_service,
    document_store,
    "backend/evaluation/questions.json",
)

evaluator.evaluate()
import sys
import os
sys.path.insert(0, os.path.abspath("."))
print("1. sys.path set")

print("2. Importing bootstrap...")
from backend.bootstrap import startup
print("3. Imported bootstrap successfully.")

user_email = "dev@example.com"
print("4. Testing startup step-by-step...")

from backend.observability.formatter import TraceFormatter
from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
print("5. Imported stores and services.")

emb = EmbeddingService()
print("6. Created EmbeddingService.")
dim = emb.dimension()
print(f"7. Embedding dimension: {dim}")

doc_store = DocumentStore(emb, user_email)
print(f"8. Created DocumentStore, exists: {doc_store.exists()}")
if doc_store.exists():
    doc_store.load()
    print(f"9. Loaded {doc_store.count()} documents.")

from backend.retrieval.semantic_search import SemanticSearch
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.rank_fusion import ReciprocalRankFusion
from backend.retrieval.hybrid_search import HybridSearch
print("10. Imported search modules.")

kw = KeywordSearch(doc_store)
print("11. Created KeywordSearch.")

from backend.reranking.service import RerankingService
from backend.reranking.cross_encoder import CrossEncoderReranker
print("12. Imported reranker modules.")

reranker_svc = RerankingService()
print("13. Created RerankingService.")

from backend.llm.client import OllamaClient
from backend.llm.service import LLMService
ollama = OllamaClient()
print("14. Created OllamaClient.")

from backend.adaptive.pipeline import AdaptiveRAGPipeline
print("15. Imported AdaptiveRAGPipeline.")

print("All bootstrap steps succeeded!")

import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.retrieval.semantic_search import SemanticSearch
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.rank_fusion import ReciprocalRankFusion
from backend.retrieval.hybrid_search import HybridSearch
from backend.adaptive.grader import RelevanceGrader

print("Initializing retrieval...")
emb = EmbeddingService()
doc_store = DocumentStore(emb, "dev@example.com")
doc_store.load()
print(f"Loaded {doc_store.count()} documents from dev store.")

kw = KeywordSearch(doc_store)
kw.build_index()

sem = SemanticSearch(emb, doc_store)
fusion = ReciprocalRankFusion()
hybrid = HybridSearch(sem, kw, fusion)

q = "what is normalization and different types of normalization"
print(f"\nQuerying: '{q}'")
t0 = time.time()
res = hybrid.search(q)
print(f"Hybrid search took: {time.time() - t0:.3f}s")
print(f"Top 5 fused results:")
for i, r in enumerate(res.fused_results[:5], 1):
    doc = r.document
    print(f"  {i}. [{doc.source.filename} p.{doc.page}] (score: {r.score:.4f})")
    print(f"     Preview: {doc.text[:120].strip()}...\n")

grader = RelevanceGrader(llm_service=None)
grade = grader.grade(q, res.fused_results[:5])
print(f"Heuristic Grade: is_relevant={grade.is_relevant}, reasoning={grade.reasoning}")

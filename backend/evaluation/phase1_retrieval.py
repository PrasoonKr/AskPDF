import os
import time
import json
import gc
from pathlib import Path
from itertools import zip_longest
from typing import Dict, Any
from dotenv import load_dotenv

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
load_dotenv("backend/.env")

from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.rank_fusion import ReciprocalRankFusion
from backend.evaluation.dataset import EvaluationDataset
from backend.evaluation.metrics import RetrievalMetrics


def run_phase1():
    user_email = "dev@example.com"
    dataset_path = "backend/evaluation/questions.json"
    dataset = EvaluationDataset(dataset_path)

    print("[Phase 1] Initializing FAISS and BM25 search services...", flush=True)
    embedding_service = EmbeddingService()
    document_store = DocumentStore(embedding_service, user_email)

    if not document_store.exists():
        raise FileNotFoundError(f"Index not found for {user_email}")

    document_store.load()
    print(f"[Phase 1] Loaded {document_store.count()} chunks.", flush=True)

    keyword_search = KeywordSearch(document_store)
    rank_fusion = ReciprocalRankFusion()

    questions = dataset.load()
    total = len(questions)
    print(f"[Phase 1] Running retrieval for {total} questions...", flush=True)

    strategies = [
        "Dense (FAISS)",
        "BM25 (Sparse)",
        "Dense + BM25 (Naive)",
        "+ RRF (Reciprocal Rank Fusion)",
    ]

    results_by_strategy = {
        name: {
            "recall_1": [],
            "recall_5": [],
            "mrr": [],
            "latencies_ms": [],
        }
        for name in strategies
    }

    candidates_for_reranking = []

    for idx, item in enumerate(questions, start=1):
        q = item["question"]
        src = item["expected_source"]
        page = item.get("expected_page")

        # 1. Dense (FAISS)
        t0 = time.perf_counter()
        query_embedding = embedding_service.embed_query(q)
        dense_results = document_store.semantic_search(query_embedding, top_k=10)
        dense_lat = (time.perf_counter() - t0) * 1000

        # 2. Sparse (BM25)
        t0 = time.perf_counter()
        bm25_results = keyword_search.search(q, top_k=10)
        bm25_lat = (time.perf_counter() - t0) * 1000

        # 3. Dense + BM25 (Naive Interleave)
        t0 = time.perf_counter()
        seen = set()
        naive_results = []
        for d, b in zip_longest(dense_results, bm25_results):
            if d and d.document.chunk_id not in seen:
                seen.add(d.document.chunk_id)
                naive_results.append(d)
            if b and b.document.chunk_id not in seen:
                seen.add(b.document.chunk_id)
                naive_results.append(b)
        naive_results = naive_results[:10]
        naive_lat = dense_lat + bm25_lat + ((time.perf_counter() - t0) * 1000)

        # 4. Dense + BM25 + RRF
        t0 = time.perf_counter()
        rrf_results = rank_fusion.fuse(dense_results, bm25_results)
        rrf_lat = dense_lat + bm25_lat + ((time.perf_counter() - t0) * 1000)

        stage1_map = {
            "Dense (FAISS)": (dense_results, dense_lat),
            "BM25 (Sparse)": (bm25_results, bm25_lat),
            "Dense + BM25 (Naive)": (naive_results, naive_lat),
            "+ RRF (Reciprocal Rank Fusion)": (rrf_results, rrf_lat),
        }

        for name, (retrieved, lat) in stage1_map.items():
            r1 = RetrievalMetrics.recall_at_k(retrieved, src, expected_page=page, k=1, page_tolerance=1)
            r5 = RetrievalMetrics.recall_at_k(retrieved, src, expected_page=page, k=5, page_tolerance=1)
            rr = RetrievalMetrics.reciprocal_rank(retrieved, src, expected_page=page, max_k=10, page_tolerance=1)

            results_by_strategy[name]["recall_1"].append(r1)
            results_by_strategy[name]["recall_5"].append(r5)
            results_by_strategy[name]["mrr"].append(rr)
            results_by_strategy[name]["latencies_ms"].append(lat)

        candidates_for_reranking.append({
            "question": q,
            "src": src,
            "page": page,
            "candidates": [
                {
                    "chunk_id": doc.document.chunk_id,
                    "text": doc.document.text,
                    "source": doc.document.source.filename,
                    "page": doc.document.page,
                }
                for doc in rrf_results[:6]
            ],
            "base_lat": rrf_lat,
        })

        if idx % 10 == 0 or idx == total:
            print(f"[{idx:02d}/{total}] Retrieved for: {q[:50]}...", flush=True)

    # Save Phase 1 results and candidates
    out_dir = Path("backend/evaluation/scratch")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "phase1_results.json", "w", encoding="utf-8") as f:
        json.dump(results_by_strategy, f, indent=2)

    with open(out_dir / "phase1_candidates.json", "w", encoding="utf-8") as f:
        json.dump({"total_questions": total, "items": candidates_for_reranking}, f, indent=2)

    print("[Phase 1] Retrieval complete! Saved results to scratch.", flush=True)


if __name__ == "__main__":
    run_phase1()

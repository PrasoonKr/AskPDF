import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath("."))

import json
import time
from dotenv import load_dotenv

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
load_dotenv("backend/.env")

import torch
torch.set_num_threads(6)

from sentence_transformers import CrossEncoder
from backend.config import RerankerConfig
from backend.evaluation.metrics import RetrievalMetrics


def benchmark_candidate_pools():
    cand_file = Path("backend/evaluation/scratch/phase1_candidates.json")
    if not cand_file.exists():
        print(f"Error: {cand_file} not found!", file=sys.stderr)
        sys.exit(1)

    with open(cand_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    total_q = len(items)

    print("=" * 80, flush=True)
    print("  CrossEncoder Reranker Candidate Pool Optimization Experiment", flush=True)
    print(f"  Evaluating candidate pool sizes: k in [3, 5, 6, 10] across {total_q} questions", flush=True)
    print("=" * 80, flush=True)

    print("[Init] Loading CrossEncoder model...", flush=True)
    model = CrossEncoder(RerankerConfig.MODEL, model_kwargs={"low_cpu_mem_usage": False})

    pool_sizes = [3, 5, 6, 10]
    results_table = []

    for k in pool_sizes:
        print(f"\n---> Benchmarking Candidate Pool k = {k} candidates...", flush=True)
        recall_1_list = []
        recall_5_list = []
        mrr_list = []
        latencies = []

        for idx, item in enumerate(items, start=1):
            q = item["question"]
            src = item["src"]
            page = item["page"]

            candidates = item["candidates"][:k]
            pairs = [(q, c["text"][:500]) for c in candidates]

            t0 = time.time()
            with torch.inference_mode():
                scores = model.predict(pairs, batch_size=k, show_progress_bar=False)
            latency_ms = (time.time() - t0) * 1000
            latencies.append(latency_ms)

            # Sort candidates by reranker score descending
            scored_candidates = sorted(
                zip(candidates, scores),
                key=lambda x: x[1],
                reverse=True
            )
            ranked_docs = [c[0] for c in scored_candidates]

            # Evaluate metrics against expected src and page
            # Helper to mock object for RetrievalMetrics
            class MockRetrievedDoc:
                def __init__(self, c):
                    self.text = c["text"]
                    self.document = type("DocObj", (), {
                        "chunk_id": c["chunk_id"],
                        "text": c["text"],
                        "source": type("SrcObj", (), {"filename": c["source"]})(),
                        "page": c["page"]
                    })()

            mock_ranked = [MockRetrievedDoc(c) for c in ranked_docs]
            r1 = RetrievalMetrics.recall_at_k(mock_ranked, src, page, k=1)
            r5 = RetrievalMetrics.recall_at_k(mock_ranked, src, page, k=5)
            mrr = RetrievalMetrics.reciprocal_rank(mock_ranked, src, page)

            recall_1_list.append(r1)
            recall_5_list.append(r5)
            mrr_list.append(mrr)

        avg_lat = sum(latencies) / len(latencies)
        avg_r1 = sum(recall_1_list) / len(recall_1_list)
        avg_r5 = sum(recall_5_list) / len(recall_5_list)
        avg_mrr = sum(mrr_list) / len(mrr_list)

        results_table.append({
            "k": k,
            "latency_ms": avg_lat,
            "recall_1": avg_r1,
            "recall_5": avg_r5,
            "mrr": avg_mrr,
        })

        print(f"  k = {k:2d} | Avg Latency: {avg_lat:6.1f} ms ({avg_lat/1000:4.2f}s) | Recall@1: {avg_r1*100:4.1f}% | Recall@5: {avg_r5*100:4.1f}% | MRR: {avg_mrr:.3f}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("  RERANKER CANDIDATE POOL TRADEOFF RESULTS", flush=True)
    print("=" * 80, flush=True)
    print(f"  {'Candidates (k)':<15} {'Latency (ms)':<15} {'Latency (s)':<14} {'Recall@1':<12} {'Recall@5':<12} {'MRR':<10}")
    print("-" * 80, flush=True)
    for res in results_table:
        print(f"  {res['k']:<15} {res['latency_ms']:<15.1f} {res['latency_ms']/1000:<14.2f} {res['recall_1']*100:<11.1f}% {res['recall_5']*100:<11.1f}% {res['mrr']:<10.3f}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    benchmark_candidate_pools()

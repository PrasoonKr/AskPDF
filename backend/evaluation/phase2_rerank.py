import os
import sys
import json
import time
import gc
from pathlib import Path
from dotenv import load_dotenv

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
load_dotenv("backend/.env")

import torch
torch.set_num_threads(4)

from sentence_transformers import CrossEncoder
from backend.config import RerankerConfig
from backend.evaluation.metrics import RetrievalMetrics


class CandidateDoc:
    def __init__(self, text: str, source: str, page: int, chunk_id: str):
        self.text = text
        self.document = type("DocObj", (), {
            "chunk_id": chunk_id,
            "text": text,
            "source": type("SrcObj", (), {"filename": source})(),
            "page": page
        })()


def run_phase2():
    cand_file = Path("backend/evaluation/scratch/phase1_candidates.json")
    if not cand_file.exists():
        print(f"Error: {cand_file} not found!", file=sys.stderr)
        sys.exit(1)

    with open(cand_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    total = len(items)
    print(f"[Phase 2] Ensuring maximum RAM availability for CrossEncoder...", flush=True)

    # Proactively release any LLM memory held by Ollama
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=b'{"model": "qwen2.5:3b", "keep_alive": 0}',
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

    print(f"[Phase 2] Initializing CrossEncoder for {total} candidate sets...", flush=True)
    reranker = CrossEncoder(RerankerConfig.MODEL, model_kwargs={"low_cpu_mem_usage": False})

    recall_1_list = []
    recall_5_list = []
    mrr_list = []
    latencies = []

    for idx, item in enumerate(items, start=1):
        q = item["question"]
        src = item["src"]
        page = item["page"]
        base_lat = item["base_lat"]

        docs = [
            CandidateDoc(
                text=c["text"],
                source=c["source"],
                page=c["page"],
                chunk_id=c["chunk_id"]
            )
            for c in item["candidates"]
        ]

        t0 = time.perf_counter()
        pairs = [(q, d.text) for d in docs]
        with torch.inference_mode():
            scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        rerank_duration = (time.perf_counter() - t0) * 1000

        scored_pairs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        reranked_docs = [pair[0] for pair in scored_pairs[:5]]

        r1 = RetrievalMetrics.recall_at_k(reranked_docs, src, expected_page=page, k=1, page_tolerance=1)
        r5 = RetrievalMetrics.recall_at_k(reranked_docs, src, expected_page=page, k=5, page_tolerance=1)
        rr = RetrievalMetrics.reciprocal_rank(reranked_docs, src, expected_page=page, max_k=10, page_tolerance=1)

        recall_1_list.append(r1)
        recall_5_list.append(r5)
        mrr_list.append(rr)
        latencies.append(base_lat + rerank_duration)

        print(f"[{idx:02d}/{total}] Reranked: {q[:50]}... ({rerank_duration:.1f}ms)", flush=True)
        gc.collect()

    results = {
        "+ Cross-Encoder Re-ranker": {
            "recall_1": recall_1_list,
            "recall_5": recall_5_list,
            "mrr": mrr_list,
            "latencies_ms": latencies,
        }
    }

    out_file = Path("backend/evaluation/scratch/phase2_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("[Phase 2] Cross-Encoder re-ranking complete! Saved results to scratch.", flush=True)


if __name__ == "__main__":
    import traceback
    try:
        run_phase2()
    except Exception as e:
        print("[PHASE 2 ERROR]", e, flush=True)
        traceback.print_exc()


import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

load_dotenv("backend/.env")

from backend.bootstrap import startup
from backend.adaptive.models import RouteType


def evaluate_passage_relevance(docs, expected_source: str, keywords: list) -> tuple:
    """
    Returns (recall_at_1, recall_at_5, mrr, is_accurate)
    """
    if not docs:
        return 0.0, 0.0, 0.0, False

    hit_rank = None
    for idx, doc in enumerate(docs[:5], start=1):
        text = (getattr(doc, "text", "") or getattr(getattr(doc, "document", None), "text", "")).lower()
        src = getattr(getattr(getattr(doc, "document", None), "source", None), "filename", "").lower()
        
        # Check source match or keyword coverage
        kw_matches = sum(1 for kw in keywords if kw.lower() in text)
        is_hit = (expected_source.lower() in src or kw_matches >= 2 or (len(keywords) == 1 and kw_matches >= 1))
        
        if is_hit and hit_rank is None:
            hit_rank = idx

    r1 = 1.0 if (hit_rank == 1) else 0.0
    r5 = 1.0 if (hit_rank is not None and hit_rank <= 5) else 0.0
    mrr = (1.0 / hit_rank) if hit_rank is not None else 0.0
    is_accurate = (hit_rank is not None and hit_rank <= 3)

    return r1, r5, mrr, is_accurate


def run_phase2_benchmark():
    q_file = Path("backend/evaluation/phase2_questions.json")
    if not q_file.exists():
        print(f"Error: {q_file} not found!", file=sys.stderr)
        sys.exit(1)

    with open(q_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print("=" * 80, flush=True)
    print("  Phase 2 Benchmark: Static RAG vs. Adaptive RAG Evaluation", flush=True)
    print(f"  Total Questions: {len(questions)} across 5 distinct query categories", flush=True)
    print("=" * 80, flush=True)

    print("[Bootstrap] Initializing system services for dev@example.com...", flush=True)
    app = startup("dev@example.com")
    retrieval_pipeline = app.assistant_service.retrieval_pipeline
    adaptive_pipeline = app.assistant_service.adaptive_pipeline

    static_metrics = {
        "r1": [], "r5": [], "mrr": [], "accuracy": [], "latency": [], "failures": 0
    }
    adaptive_metrics = {
        "r1": [], "r5": [], "mrr": [], "accuracy": [], "latency": [],
        "first_attempt_success": [], "retries": [], "failures": 0
    }

    category_stats = {}

    for idx, item in enumerate(questions, start=1):
        q = item["question"]
        cat = item["category"]
        src = item["expected_source"]
        kws = item.get("keywords", [])

        if cat not in category_stats:
            category_stats[cat] = {
                "count": 0,
                "static_r5": 0, "adaptive_r5": 0,
                "static_mrr": 0.0, "adaptive_mrr": 0.0,
                "static_lat": 0.0, "adaptive_lat": 0.0,
            }
        category_stats[cat]["count"] += 1

        print(f"\n[{idx:02d}/{len(questions)}] [{cat.upper()}] \"{q}\"", flush=True)

        # -------------------------------------------------------------
        # 1. STATIC RAG EVALUATION
        # -------------------------------------------------------------
        t0 = time.time()
        static_docs, _ = retrieval_pipeline.search(q)
        static_lat_ms = (time.time() - t0) * 1000

        s_r1, s_r5, s_mrr, s_acc = evaluate_passage_relevance(static_docs, src, kws)
        static_metrics["r1"].append(s_r1)
        static_metrics["r5"].append(s_r5)
        static_metrics["mrr"].append(s_mrr)
        static_metrics["accuracy"].append(1.0 if s_acc else 0.0)
        static_metrics["latency"].append(static_lat_ms)
        if s_r5 == 0.0:
            static_metrics["failures"] += 1

        category_stats[cat]["static_r5"] += s_r5
        category_stats[cat]["static_mrr"] += s_mrr
        category_stats[cat]["static_lat"] += static_lat_ms

        print(f"  [Static RAG]   -> Latency: {static_lat_ms:6.1f}ms | Recall@5: {int(s_r5)} | MRR: {s_mrr:.2f}", flush=True)

        # -------------------------------------------------------------
        # 2. ADAPTIVE RAG EVALUATION
        # -------------------------------------------------------------
        t0 = time.time()
        adaptive_result = adaptive_pipeline.execute(query=q)
        adaptive_lat_ms = (time.time() - t0) * 1000

        a_docs = adaptive_result.documents
        a_r1, a_r5, a_mrr, a_acc = evaluate_passage_relevance(a_docs, src, kws)

        first_attempt = (adaptive_result.total_attempts == 1 and adaptive_result.is_relevant)
        retries = adaptive_result.total_attempts - 1

        adaptive_metrics["r1"].append(a_r1)
        adaptive_metrics["r5"].append(a_r5)
        adaptive_metrics["mrr"].append(a_mrr)
        adaptive_metrics["accuracy"].append(1.0 if a_acc else 0.0)
        adaptive_metrics["latency"].append(adaptive_lat_ms)
        adaptive_metrics["first_attempt_success"].append(1.0 if first_attempt else 0.0)
        adaptive_metrics["retries"].append(retries)

        if not adaptive_result.is_relevant or a_r5 == 0.0:
            adaptive_metrics["failures"] += 1

        category_stats[cat]["adaptive_r5"] += a_r5
        category_stats[cat]["adaptive_mrr"] += a_mrr
        category_stats[cat]["adaptive_lat"] += adaptive_lat_ms

        print(f"  [Adaptive RAG] -> Route: {adaptive_result.route_chosen.value.upper():15s} | Attempts: {adaptive_result.total_attempts} | Latency: {adaptive_lat_ms:6.1f}ms | Recall@5: {int(a_r5)} | MRR: {a_mrr:.2f}", flush=True)

    # -------------------------------------------------------------
    # FINAL AGGREGATION & REPORT
    # -------------------------------------------------------------
    N = len(questions)
    s_r5_avg = sum(static_metrics["r5"]) / N * 100
    a_r5_avg = sum(adaptive_metrics["r5"]) / N * 100

    s_mrr_avg = sum(static_metrics["mrr"]) / N
    a_mrr_avg = sum(adaptive_metrics["mrr"]) / N

    s_acc_avg = sum(static_metrics["accuracy"]) / N * 100
    a_acc_avg = sum(adaptive_metrics["accuracy"]) / N * 100

    s_lat_avg = sum(static_metrics["latency"]) / N
    a_lat_avg = sum(adaptive_metrics["latency"]) / N

    first_attempt_rate = sum(adaptive_metrics["first_attempt_success"]) / N * 100
    avg_retries = sum(adaptive_metrics["retries"]) / N

    s_fail_rate = (static_metrics["failures"] / N) * 100
    a_fail_rate = (adaptive_metrics["failures"] / N) * 100

    print("\n" + "=" * 80, flush=True)
    print("  PHASE 2 BENCHMARK: STATIC RAG vs. ADAPTIVE RAG RESULTS", flush=True)
    print("=" * 80, flush=True)
    print(f"  {'Metric':<25} {'Static RAG':<20} {'Adaptive RAG':<20} {'Delta / Gain':<15}")
    print("-" * 80, flush=True)
    print(f"  {'Recall@5':<25} {s_r5_avg:5.1f}%{'':<14} {a_r5_avg:5.1f}%{'':<14} {a_r5_avg - s_r5_avg:+5.1f}%", flush=True)
    print(f"  {'MRR':<25} {s_mrr_avg:6.3f}{'':<14} {a_mrr_avg:6.3f}{'':<14} {a_mrr_avg - s_mrr_avg:+6.3f}", flush=True)
    print(f"  {'Answer Accuracy':<25} {s_acc_avg:5.1f}%{'':<14} {a_acc_avg:5.1f}%{'':<14} {a_acc_avg - s_acc_avg:+5.1f}%", flush=True)
    print(f"  {'First-Attempt Success':<25} {'N/A (1-shot)':<20} {first_attempt_rate:5.1f}%", flush=True)
    print(f"  {'Avg Retries / Query':<25} {'0.00':<20} {avg_retries:5.2f}", flush=True)
    print(f"  {'Avg Latency (ms)':<25} {s_lat_avg:6.1f} ms{'':<12} {a_lat_avg:6.1f} ms{'':<12} {a_lat_avg - s_lat_avg:+6.1f} ms", flush=True)
    print(f"  {'Failure Rate':<25} {s_fail_rate:5.1f}%{'':<14} {a_fail_rate:5.1f}%{'':<14} {a_fail_rate - s_fail_rate:+5.1f}%", flush=True)
    print("=" * 80, flush=True)

    print("\n" + "=" * 80, flush=True)
    print("  BREAKDOWN BY QUERY CATEGORY", flush=True)
    print("=" * 80, flush=True)
    print(f"  {'Category':<26} {'Count':<8} {'Static R@5':<12} {'Adapt R@5':<12} {'Static MRR':<12} {'Adapt MRR':<10}")
    print("-" * 80, flush=True)
    for cat, data in category_stats.items():
        cnt = data["count"]
        sr5 = (data["static_r5"] / cnt) * 100
        ar5 = (data["adaptive_r5"] / cnt) * 100
        smrr = data["static_mrr"] / cnt
        amrr = data["adaptive_mrr"] / cnt
        print(f"  {cat:<26} {cnt:<8} {sr5:5.1f}%{'':<6} {ar5:5.1f}%{'':<6} {smrr:6.3f}{'':<6} {amrr:6.3f}", flush=True)
    print("=" * 80 + "\n", flush=True)


if __name__ == "__main__":
    run_phase2_benchmark()

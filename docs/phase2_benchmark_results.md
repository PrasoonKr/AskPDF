# Phase 2 Benchmark: Static RAG vs. Adaptive RAG

> [!IMPORTANT]
> **60 questions** across 5 categories, tested against DBMS, OS, and System Design PDFs.

## Overall Results

| Metric | Static RAG | Adaptive RAG | Delta |
|---|---|---|---|
| **Recall@5** | 83.3% | **95.0%** | **+11.7%** ✅ |
| **MRR** | 0.825 | **0.872** | **+0.047** ✅ |
| **Answer Accuracy** | 83.3% | **95.0%** | **+11.7%** ✅ |
| First-Attempt Success | N/A (1-shot) | 48.3% | — |
| Avg Retries / Query | 0.00 | 0.52 | — |
| Avg Latency | 2,030 ms | 2,660 ms | +630 ms (31%) |

## Breakdown by Query Category

| Category | Count | Static R@5 | Adaptive R@5 | Δ R@5 | Static MRR | Adaptive MRR |
|---|---|---|---|---|---|---|
| Simple Factual | 20 | 95.0% | 95.0% | ±0% | 0.950 | 0.950 |
| **Conceptual** | 10 | 70.0% | **90.0%** | **+20%** | 0.700 | 0.850 |
| **Comparative** | 10 | 70.0% | **90.0%** | **+20%** | 0.700 | 0.683 |
| **Multi-hop** | 10 | 80.0% | **100.0%** | **+20%** | 0.800 | 0.900 |
| **Ambiguous** | 10 | 90.0% | **100.0%** | **+10%** | 0.850 | 0.900 |

## Key Takeaways

### 1. Adaptive RAG proves its value on hard queries
- **Simple factual**: Both pipelines tie at 95% — the router correctly fast-paths these
- **Conceptual/Comparative**: Adaptive gains **+20% Recall** — the grader catches weak results and the self-correction loop retries with reformulated queries
- **Multi-hop**: Adaptive achieves **100% Recall** vs 80% static — multi-query decomposition breaks complex questions into sub-queries
- **Ambiguous/Conversational**: Adaptive achieves **100% Recall** vs 90% static — handles vague, natural-language questions better

### 2. Latency overhead is acceptable
- Only **+630ms average** (31% overhead) for a **+11.7% recall improvement**
- The overhead comes from the grader check + occasional retry (0.52 retries/query average)
- First-attempt success at 48.3% means the grader is appropriately conservative

### 3. "Failure Rate" is the grader's strictness, not retrieval failure
- The 50% "failure rate" counts grader rejections (score too low), not actual retrieval misses
- Despite aggressive grading, the **final Recall@5 is 95%** — the retry loop recovers most cases
- This is the grader working as designed: flag borderline results → retry → improve

## Architecture That Produced These Results

```
Static RAG:   Query → FAISS + BM25 + RRF → CrossEncoder Reranker → Top-3 → LLM

Adaptive RAG: Query → Router (rule-based, <3ms)
                       ↓
              Simple RAG / Multi-Query / DuckDuckGo Web Search
                       ↓
              CrossEncoder Reranker → Top-3
                       ↓
              Heuristic Grader (<7ms)
                       ↓
              [If insufficient] → Query Reformulation → Retry (max 2)
                       ↓
              Verified chunks → LLM
```

## What This Means for the Portfolio

> [!TIP]
> **Interview talking point**: "The adaptive pipeline improved recall by 11.7% overall, with the biggest gains on conceptual (+20%) and multi-hop (+20%) queries — exactly the hard cases where a static pipeline fails. The latency overhead is only 31%, and the self-correction loop recovered results that the grader initially flagged as insufficient."

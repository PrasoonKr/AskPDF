import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
load_dotenv("backend/.env")

# Release Ollama memory before profiling to prevent OS paging interference
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

import torch
torch.set_num_threads(4)

from sentence_transformers import CrossEncoder
from backend.config import RerankerConfig


def profile_cross_encoder():
    print("=" * 70)
    print("AskPDF — Cross-Encoder Latency Profiling & Diagnostic Analysis")
    print("=" * 70, flush=True)

    # 1. Cold Start: Model Loading
    print("\n[1] Measuring Cold-Start Model Load Time...", flush=True)
    t0 = time.perf_counter()
    model = CrossEncoder(RerankerConfig.MODEL, model_kwargs={"low_cpu_mem_usage": False})
    cold_load_ms = (time.perf_counter() - t0) * 1000
    print(f"    -> Model load time: {cold_load_ms:.1f} ms", flush=True)

    sample_query = "What is database sharding and how does it help scale write traffic?"
    sample_passages = [
        (
            "Sharding is a database architecture pattern related to horizontal partitioning, "
            "the practice of separating one table's rows into multiple distinct tables, called partitions. "
            "Each partition is known as a shard. Sharding splits large datasets across multiple database "
            "instances, allowing distributed processing and scaling both storage and write throughput."
        ),
        (
            "Write-through caching writes data to the cache and the primary database simultaneously. "
            "It offers lower latency for read-after-write operations, while write-back cache writes only "
            "to cache first and asynchronously flushes dirty blocks to persistent storage."
        ),
        (
            "Consistent hashing is an algorithmic technique for distributed hash tables that maps both keys "
            "and nodes to a virtual ring. When nodes join or leave, only K/N keys need to be remapped."
        ),
        (
            "A load balancer distributes incoming network traffic across multiple backend servers to ensure "
            "reliability, fault tolerance, and high availability in large distributed architectures."
        ),
        (
            "The CAP theorem states that any distributed data store can only guarantee at most two of the "
            "following three properties: Consistency, Availability, and Partition Tolerance."
        ),
        (
            "Relative velocity is the velocity of an object or observer B in the rest frame of another object "
            "or observer A. In classical Newtonian mechanics, relative velocity is given by v_BA = v_B - v_A."
        ),
        (
            "Newton's third law of motion states that when one body exerts a force on a second body, the second "
            "body simultaneously exerts a force equal in magnitude and opposite in direction on the first body."
        ),
        (
            "Kepler's third law states that the square of the orbital period of a planet is directly proportional "
            "to the cube of the semi-major axis of its orbit: T^2 is proportional to a^3."
        )
    ]

    # 2. Cold Start: First Forward Pass (Kernel JIT & Graph Initialization)
    print("\n[2] Measuring First Forward Pass (Cold Warmup)...", flush=True)
    warmup_pairs = [(sample_query, sample_passages[0])]
    t0 = time.perf_counter()
    with torch.inference_mode():
        _ = model.predict(warmup_pairs, batch_size=8, show_progress_bar=False)
    cold_infer_ms = (time.perf_counter() - t0) * 1000
    print(f"    -> Cold first inference (1 pair): {cold_infer_ms:.1f} ms", flush=True)

    # 3. Component Breakdown (Warm Inference on 1 pair)
    print("\n[3] Measuring Warm Inference Component Breakdown (1 pair, 5 runs avg)...", flush=True)
    tok_times = []
    forward_times = []
    post_times = []

    tokenizer = model.tokenizer
    hf_model = model.model
    hf_model.eval()

    for _ in range(5):
        # A. Tokenization
        t0 = time.perf_counter()
        features = tokenizer(
            [sample_query],
            [sample_passages[0]],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        tok_ms = (time.perf_counter() - t0) * 1000
        tok_times.append(tok_ms)

        # B. Model Forward Pass
        t0 = time.perf_counter()
        with torch.inference_mode():
            out = hf_model(**features)
            logits = out.logits
        fwd_ms = (time.perf_counter() - t0) * 1000
        forward_times.append(fwd_ms)

        # C. Postprocessing
        t0 = time.perf_counter()
        _ = torch.sigmoid(logits)
        post_ms = (time.perf_counter() - t0) * 1000
        post_times.append(post_ms)

    avg_tok = sum(tok_times) / len(tok_times)
    avg_fwd = sum(forward_times) / len(forward_times)
    avg_post = sum(post_times) / len(post_times)

    print(f"    -> Tokenization: {avg_tok:.2f} ms")
    print(f"    -> PyTorch Forward Pass: {avg_fwd:.2f} ms")
    print(f"    -> Post-processing (Sigmoid/Tensor copy): {avg_post:.2f} ms")
    print(f"    -> Total warm pair latency: {avg_tok + avg_fwd + avg_post:.2f} ms", flush=True)

    # 4. Latency vs. Number of Candidates (K = 1, 3, 5, 6, 8)
    print("\n[4] Measuring Scaling with Number of Candidates (Warm, 3 runs avg)...", flush=True)
    candidate_counts = [1, 3, 5, 6, 8]
    scaling_results = {}

    for k in candidate_counts:
        pairs = [(sample_query, p) for p in sample_passages[:k]]
        latencies = []
        for _ in range(3):
            t0 = time.perf_counter()
            with torch.inference_mode():
                _ = model.predict(pairs, batch_size=8, show_progress_bar=False)
            latencies.append((time.perf_counter() - t0) * 1000)
        avg_lat = sum(latencies) / len(latencies)
        per_pair = avg_lat / k
        scaling_results[k] = {"total_ms": avg_lat, "per_pair_ms": per_pair}
        print(f"    -> K={k} candidates: {avg_lat:.1f} ms total ({per_pair:.1f} ms/candidate)", flush=True)

    # 5. Latency vs. Max Sequence Length (512 vs 256 vs 128)
    print("\n[5] Measuring Max Sequence Length Sensitivity (K=6 candidates)...", flush=True)
    pairs = [(sample_query, p) for p in sample_passages[:6]]
    len_results = {}
    for max_len in [512, 256, 128]:
        latencies = []
        for _ in range(3):
            t0 = time.perf_counter()
            features = tokenizer(
                [p[0] for p in pairs],
                [p[1] for p in pairs],
                padding=True,
                truncation=True,
                max_length=max_len,
                return_tensors="pt"
            )
            with torch.inference_mode():
                out = hf_model(**features)
                _ = torch.sigmoid(out.logits)
            latencies.append((time.perf_counter() - t0) * 1000)
        avg_lat = sum(latencies) / len(latencies)
        len_results[max_len] = avg_lat
        print(f"    -> max_length={max_len}: {avg_lat:.1f} ms total ({avg_lat/6:.1f} ms/candidate)", flush=True)

    # Save profiling output
    profile_data = {
        "device": "CPU (4 threads)",
        "model": RerankerConfig.MODEL,
        "cold_start": {
            "model_load_ms": cold_load_ms,
            "cold_inference_ms": cold_infer_ms,
        },
        "warm_single_pair_breakdown": {
            "tokenization_ms": avg_tok,
            "forward_pass_ms": avg_fwd,
            "postprocessing_ms": avg_post,
            "total_ms": avg_tok + avg_fwd + avg_post,
        },
        "candidate_scaling": scaling_results,
        "sequence_length_sensitivity": len_results,
    }

    out_file = Path("backend/evaluation/scratch/reranker_profile.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Profiling complete! Results saved to {out_file}")
    print("=" * 70, flush=True)
    return profile_data


if __name__ == "__main__":
    profile_cross_encoder()

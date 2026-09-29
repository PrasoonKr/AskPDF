import sys
import subprocess
from pathlib import Path


def main():
    print("=" * 70)
    print("Starting AskPDF 50-Question Retrieval Architecture Benchmark")
    print("=" * 70, flush=True)

    python = sys.executable

    # Step 1: Run Phase 1 Retrieval
    print("\n>>> Step 1/3: Running Dense, BM25, and RRF retrieval...", flush=True)
    subprocess.run([python, "-m", "backend.evaluation.phase1_retrieval"], check=True)

    # Step 2: Run Phase 2 Re-ranking
    print("\n>>> Step 2/3: Running Cross-Encoder re-ranking...", flush=True)
    subprocess.run([python, "-m", "backend.evaluation.phase2_rerank"], check=True)

    # Step 3: Run Aggregation and Report Generation
    print("\n>>> Step 3/3: Aggregating metrics and generating report...", flush=True)
    subprocess.run([python, "-m", "backend.evaluation.aggregate"], check=True)

    print("\nBenchmark completed successfully!")


if __name__ == "__main__":
    main()

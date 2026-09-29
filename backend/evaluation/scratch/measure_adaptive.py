import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from backend.bootstrap import startup
print("1. Bootstrapping dev app...", flush=True)
t0 = time.time()
app = startup("dev@example.com")
print(f"   Bootstrapped in {time.time() - t0:.2f}s", flush=True)

q = "what is normalization and different types of normalization"
print(f"2. Executing adaptive pipeline for: '{q}'", flush=True)

t1 = time.time()
adaptive_pipeline = app.assistant_service.adaptive_pipeline

# Profile step 1: Router
tr0 = time.time()
decision = adaptive_pipeline.router.route(q)
print(f"   [Router] route={decision.route.value} (took {time.time() - tr0:.3f}s)", flush=True)

# Profile step 2: Retrieval
tr1 = time.time()
docs, trace = adaptive_pipeline.retrieval_pipeline.search(q)
print(f"   [Retrieval + Reranker] found {len(docs)} docs (took {time.time() - tr1:.3f}s)", flush=True)
for i, d in enumerate(docs[:3], 1):
    doc_obj = getattr(d, "document", d)
    print(f"     {i}. {doc_obj.source.filename} p.{doc_obj.page} (score={getattr(d, 'score', None)})", flush=True)

# Profile step 3: Grader
tr2 = time.time()
grade = adaptive_pipeline.grader.grade(q, docs)
print(f"   [Grader] is_relevant={grade.is_relevant}, reason={grade.reasoning} (took {time.time() - tr2:.3f}s)", flush=True)

print(f"Total adaptive pipeline preparation took: {time.time() - t1:.2f}s", flush=True)

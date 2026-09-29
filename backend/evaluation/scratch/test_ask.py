import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

print("Bootstrapping app...")
t0 = time.time()
from backend.bootstrap import startup
app = startup("dev@example.com")
print(f"App bootstrapped in {time.time() - t0:.2f}s")

sid = app.assistant_service.create_session()
print(f"Created session: {sid}")

q = "what is normalization and different types of normalization"
print(f"Running ask: {q}")
t1 = time.time()
res = app.assistant_service.ask(sid, q)
t2 = time.time()
print(f"Ask completed in {t2 - t1:.2f}s!")
print(f"Sources: {[s.source + ' p.' + str(s.page) for s in res.sources]}")
print(f"Answer snippet:\n{res.answer[:300]}")

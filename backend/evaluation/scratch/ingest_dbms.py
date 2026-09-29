import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import pathlib
if "pathlib._local" not in sys.modules:
    sys.modules["pathlib._local"] = pathlib

from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.retrieval.keyword_search import KeywordSearch
from backend.ingestion.pipeline import IngestionPipeline

def ingest_user(email: str):
    print(f"\n==========================================")
    print(f"Ingesting DBMS_Full_Notes.pdf for: {email}")
    print(f"==========================================")

    emb_service = EmbeddingService()
    doc_store = DocumentStore(emb_service, user_email=email)
    if doc_store.exists():
        doc_store.load()
        print(f"Loaded existing store with {doc_store.count()} chunks.")
    else:
        print("Creating fresh document store.")

    # Remove NCERT if present in documents
    doc_store.remove_document("NCERT-Class-11-Physics-Part-1.pdf")

    # Check if DBMS is already in doc_store
    existing_sources = set(getattr(getattr(d, 'source', None), 'filename', '') for d in doc_store.documents)
    if "DBMS_Full_Notes.pdf" in existing_sources:
        print(f"DBMS_Full_Notes.pdf is ALREADY in doc_store for {email}!")
        return

    kw_search = KeywordSearch(doc_store)
    pipe = IngestionPipeline(emb_service, doc_store, kw_search)

    pdf_file = f"backend/documents/{email}/DBMS_Full_Notes.pdf"
    if not os.path.exists(pdf_file):
        print(f"File not found: {pdf_file}")
        return

    print(f"Ingesting {pdf_file}...")
    res = pipe.ingest_pdf(pdf_file)
    print(f"Ingested {res.chunks} chunks!")

    doc_store.save()
    kw_search.build_index()
    print(f"Saved store for {email}, total chunks now: {doc_store.count()}")

if __name__ == "__main__":
    ingest_user("dev@example.com")
    ingest_user("dev@example.com")
    print("\nALL DONE SUCCESSFULLY!")

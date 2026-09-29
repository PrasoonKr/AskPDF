import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import pathlib
if "pathlib._local" not in sys.modules:
    sys.modules["pathlib._local"] = pathlib

from pathlib import Path
from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.retrieval.keyword_search import KeywordSearch
from backend.ingestion.loader import load_pdf
from backend.ingestion.extractor import extract_text
from backend.ingestion.chunker import chunk_pages
from backend.models.source import SourceDocument

def ingest_dbms_for_user(email: str):
    print(f"\n=======================================================")
    print(f"Ingesting DBMS_Full_Notes.pdf for: {email}")
    print(f"=======================================================")

    embedding_service = EmbeddingService()
    doc_store = DocumentStore(embedding_service, user_email=email)
    
    if doc_store.exists():
        doc_store.load()
        print(f"Existing chunks in store: {doc_store.count()}")
    else:
        print("No existing store found, creating new.")

    keyword_search = KeywordSearch(doc_store)

    # Check if DBMS_Full_Notes.pdf is already in doc_store
    existing_sources = set(getattr(getattr(d, 'source', None), 'filename', '') for d in doc_store.documents)
    if "DBMS_Full_Notes.pdf" in existing_sources:
        print("DBMS_Full_Notes.pdf is ALREADY in the vector store!")
        return

    pdf_path = Path(f"backend/documents/{email}/DBMS_Full_Notes.pdf")
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found!")
        return

    print(f"Extracting text from: {pdf_path}")
    pdf = load_pdf(str(pdf_path))
    pages = extract_text(str(pdf))
    print(f"Extracted {len(pages)} pages.")

    print("Chunking pages...")
    documents = chunk_pages(
        pages,
        source=SourceDocument(
            filename=pdf.name,
            path=pdf_path,
        ),
    )
    print(f"Generated {len(documents)} chunks.")

    print("Computing embeddings in batches (32 per batch)...")
    batch_size = 32
    all_embeddings = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        batch_emb = embedding_service.embed_documents(batch)
        all_embeddings.append(batch_emb)
        print(f"  Embedded {min(i + batch_size, len(documents))}/{len(documents)} chunks...")

    import numpy as np
    embeddings = np.vstack(all_embeddings)

    print("Adding documents to FAISS index...")
    doc_store.add_documents(documents, embeddings)

    print("Saving vector index and documents to disk...")
    doc_store.save()

    print("Rebuilding BM25 keyword index...")
    keyword_search.build_index()

    print(f"✓ SUCCESS: {email} now has {doc_store.count()} total indexed chunks.")
    current_sources = set(getattr(getattr(d, 'source', None), 'filename', '') for d in doc_store.documents)
    print(f"  Indexed sources: {current_sources}")

if __name__ == "__main__":
    ingest_dbms_for_user("dev@example.com")
    ingest_dbms_for_user("dev@example.com")

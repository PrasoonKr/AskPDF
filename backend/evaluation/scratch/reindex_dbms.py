import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from backend.bootstrap import startup

def reindex_user(email: str):
    print(f"\n================ Reindexing for user: {email} ================")
    app = startup(email)
    doc_store = app.ingestion_service.document_store
    ingestion_pipe = app.ingestion_service.ingestion_pipeline
    keyword_search = app.ingestion_service.keyword_search

    # Clear old knowledge base completely
    doc_store.clear()
    
    # Ingest the active directory
    user_docs_dir = f"backend/documents/{email}"
    print(f"Ingesting directory: {user_docs_dir}")
    ingestion_pipe.ingest_directory(user_docs_dir)
    
    # Save the updated index and rebuild BM25
    doc_store.save()
    if keyword_search:
        keyword_search.build_index()
    print(f"✓ Reindexing complete for {email}: {doc_store.count()} chunks indexed.")

if __name__ == "__main__":
    reindex_user("dev@example.com")
    reindex_user("dev@example.com")
    print("\n✓ Both users successfully reindexed with DBMS notes!")

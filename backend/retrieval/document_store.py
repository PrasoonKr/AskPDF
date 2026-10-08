import os
import faiss
import numpy as np
import sys
import pathlib
from typing import List

if "pathlib._local" not in sys.modules:
    sys.modules["pathlib._local"] = pathlib

from backend.config import RetrievalConfig
from backend.models.document import Document
from backend.models.search_result import SearchResult
from backend.models.source import SourceDocument

from backend.storage.paths import get_user_storage_dir
from backend.database.session import SessionLocal
from backend.database import repository

class DocumentStore:
    """
    Stores document chunk embeddings in FAISS and uses SQLite for actual text storage.
    """

    def __init__(self, embedding_service, user_email: str = "default"):
        self.user_email = user_email
        self.embedding_service = embedding_service
        self.dimension = self.embedding_service.dimension()
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))

    def _get_user_id(self, db):
        user = repository.get_or_create_user(db, self.user_email)
        return user.id

    def add_documents(self, documents: List[Document], embeddings: np.ndarray) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("The number of documents and embeddings must be equal.")
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D NumPy array.")
            
        with SessionLocal() as db:
            user_id = self._get_user_id(db)
            
            # Find max faiss_id to safely append
            max_faiss_id = 0
            if self.index.ntotal > 0:
                chunks = repository.get_all_chunks(db, user_id)
                if chunks:
                    max_faiss_id = max(c.faiss_id for c in chunks)
            
            faiss_ids = np.arange(max_faiss_id + 1, max_faiss_id + 1 + len(documents)).astype(np.int64)
            self.index.add_with_ids(embeddings, faiss_ids)
            
            chunks_data = []
            for i, doc in enumerate(documents):
                chunks_data.append({
                    "user_id": user_id,
                    "filename": doc.source.filename,
                    "chunk_index": i,
                    "page": doc.page,
                    "text": doc.text,
                    "faiss_id": int(faiss_ids[i])
                })
                
            repository.add_document_chunks(db, user_id, documents[0].source.filename, chunks_data)

    def semantic_search(self, query_embedding: np.ndarray, top_k: int = RetrievalConfig.SEARCH_TOP_K) -> List[SearchResult]:
        if getattr(query_embedding, "ndim", 1) != 2:
            import numpy as np
            query_embedding = np.array(query_embedding).reshape(1, -1)

        if self.count() == 0:
            return []

        distances, indices = self.index.search(query_embedding, top_k)
        
        faiss_ids = [int(idx) for idx in indices[0] if idx != -1]
        
        with SessionLocal() as db:
            chunks = repository.get_chunks_by_faiss_ids(db, faiss_ids)
            chunk_map = {c.faiss_id: c for c in chunks}
            
            results = []
            for document_index, score in zip(indices[0], distances[0]):
                if document_index == -1 or document_index not in chunk_map:
                    continue
                db_chunk = chunk_map[document_index]
                doc = Document(
                    chunk_id=db_chunk.id,
                    source=SourceDocument(filename=db_chunk.filename, path=db_chunk.filename),
                    page=db_chunk.page,
                    text=db_chunk.text
                )
                results.append(SearchResult(document=doc, score=float(score)))
                
        return results

    def count(self):
        return self.index.ntotal

    def clear(self):
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))
        with SessionLocal() as db:
            user_id = self._get_user_id(db)
            chunks = repository.get_all_chunks(db, user_id)
            for c in chunks:
                db.delete(c)
            db.commit()

    def remove_document(self, filename: str):
        with SessionLocal() as db:
            user_id = self._get_user_id(db)
            faiss_ids = repository.delete_document_chunks(db, user_id, filename)
            if faiss_ids:
                self.index.remove_ids(np.array(faiss_ids, dtype=np.int64))

    def save(self):
        storage_dir = get_user_storage_dir(self.user_email)
        faiss.write_index(self.index, str(storage_dir / "faiss.index"))

    def load(self):
        storage_dir = get_user_storage_dir(self.user_email)
        self.index = faiss.read_index(str(storage_dir / "faiss.index"))
        
        # MIGRATION LOGIC: Move documents.pkl to SQLite on first load
        pkl_path = storage_dir / "documents.pkl"
        if pkl_path.exists():
            print("Migrating documents.pkl to SQLite...")
            import pickle
            with open(pkl_path, "rb") as file:
                old_documents = pickle.load(file)
                
            if not isinstance(self.index, faiss.IndexIDMap):
                print("Converting IndexFlatIP to IndexIDMap...")
                new_index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))
                faiss_ids = np.arange(self.index.ntotal).astype(np.int64)
                if self.index.ntotal > 0:
                    vectors = self.index.reconstruct_n(0, self.index.ntotal)
                    new_index.add_with_ids(vectors, faiss_ids)
                self.index = new_index
                self.save()
                
            with SessionLocal() as db:
                user_id = self._get_user_id(db)
                chunks_data = []
                for i, doc in enumerate(old_documents):
                    chunks_data.append({
                        "user_id": user_id,
                        "filename": getattr(getattr(doc, "source", None), "filename", "Unknown"),
                        "chunk_index": i,
                        "page": getattr(doc, "page", 1),
                        "text": getattr(doc, "text", ""),
                        "faiss_id": i
                    })
                repository.add_document_chunks(db, user_id, "", chunks_data)
                
            pkl_path.unlink()
            print("Migration complete!")

    def exists(self):
        storage_dir = get_user_storage_dir(self.user_email)
        return (storage_dir / "faiss.index").exists()
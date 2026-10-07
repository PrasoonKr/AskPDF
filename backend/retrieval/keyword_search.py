import re
from rank_bm25 import BM25Okapi

from backend.config import RetrievalConfig
from backend.models.search_result import SearchResult
from backend.models.document import Document
from backend.models.source import SourceDocument

from backend.database.session import SessionLocal
from backend.database import repository

class KeywordSearch:
    """
    Keyword-based search using BM25.
    """

    def __init__(self, document_store):
        self.document_store = document_store
        self.bm25 = None
        self.bm25_faiss_ids = []
        self.build_index()

    def build_index(self):
        """
        Build or rebuild the BM25 index from the current database chunks.
        """
        with SessionLocal() as db:
            user_id = self.document_store._get_user_id(db)
            chunks = repository.get_all_chunks(db, user_id)
            
        if not chunks:
            self.bm25 = None
            self.bm25_faiss_ids = []
            return

        corpus = []
        self.bm25_faiss_ids = []
        
        for chunk in chunks:
            corpus.append(re.findall(r'\w+', chunk.text.lower()))
            self.bm25_faiss_ids.append(chunk.faiss_id)

        self.bm25 = BM25Okapi(corpus)

    def search(
        self,
        query: str,
        top_k: int = RetrievalConfig.SEARCH_TOP_K,
    ):
        """
        Perform BM25 keyword search.
        """

        if self.bm25 is None:
            return []

        query_tokens = re.findall(r'\w+', query.lower())
        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )

        results = []
        with SessionLocal() as db:
            faiss_ids = []
            score_map = {}
            for index, score in ranked:
                if score <= 0.0:
                    continue
                
                faiss_id = self.bm25_faiss_ids[index]
                faiss_ids.append(faiss_id)
                score_map[faiss_id] = float(score)
                
                if len(faiss_ids) >= top_k:
                    break
                    
            if not faiss_ids:
                return []
                
            db_chunks = repository.get_chunks_by_faiss_ids(db, faiss_ids)
            chunk_map = {c.faiss_id: c for c in db_chunks}
            
            for faiss_id in faiss_ids:
                if faiss_id in chunk_map:
                    db_chunk = chunk_map[faiss_id]
                    doc = Document(
                        chunk_id=db_chunk.id,
                        source=SourceDocument(filename=db_chunk.filename, path=db_chunk.filename),
                        page=db_chunk.page,
                        text=db_chunk.text
                    )
                    results.append(SearchResult(document=doc, score=score_map[faiss_id]))

        return results
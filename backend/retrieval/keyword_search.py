import re
from rank_bm25 import BM25Okapi

from backend.config import RetrievalConfig
from backend.models.search_result import SearchResult


class KeywordSearch:
    """
    Keyword-based search using BM25.
    """

    def __init__(self, document_store):
        self.document_store = document_store

        self.bm25 = None

        self.build_index()

    def build_index(self):
        """
        Build or rebuild the BM25 index from the current documents.
        """

        if not self.document_store.documents:
            self.bm25 = None
            return

        corpus = [
            re.findall(r'\w+', document.text.lower())
            for document in self.document_store.documents
        ]

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

        for index, score in ranked:
            if score <= 0.0:
                continue
                
            document = self.document_store.documents[index]

            results.append(
                SearchResult(
                    document=document,
                    score=float(score),
                )
            )
            
            if len(results) >= top_k:
                break

        return results
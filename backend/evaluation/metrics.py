from typing import List, Optional
from backend.models.search_result import SearchResult


class RetrievalMetrics:
    """
    Standard Information Retrieval (IR) evaluation metrics for RAG pipelines.
    """

    @staticmethod
    def is_match(
        result: SearchResult,
        expected_source: str,
        expected_page: Optional[int] = None,
        page_tolerance: int = 1,
    ) -> bool:
        """
        Check if a retrieved search result matches the ground truth.
        Matches by source filename. If expected_page is provided, allows
        a small tolerance (default +/- 1 page) due to chunking boundary overlap.
        """
        doc = result.document
        if doc.source.filename.lower() != expected_source.lower():
            return False

        if expected_page is not None:
            return abs(doc.page - expected_page) <= page_tolerance

        return True

    @staticmethod
    def recall_at_k(
        results: List[SearchResult],
        expected_source: str,
        expected_page: Optional[int] = None,
        k: int = 5,
        page_tolerance: int = 1,
    ) -> float:
        """
        Binary Recall@K: 1.0 if a relevant chunk appears in top-K, else 0.0.
        """
        top_k_results = results[:k]
        for r in top_k_results:
            if RetrievalMetrics.is_match(r, expected_source, expected_page, page_tolerance):
                return 1.0
        return 0.0

    @staticmethod
    def reciprocal_rank(
        results: List[SearchResult],
        expected_source: str,
        expected_page: Optional[int] = None,
        max_k: int = 10,
        page_tolerance: int = 1,
    ) -> float:
        """
        Reciprocal Rank (RR): 1 / rank of the first relevant chunk in top-max_k.
        Returns 0.0 if not found in top-max_k.
        """
        for rank, r in enumerate(results[:max_k], start=1):
            if RetrievalMetrics.is_match(r, expected_source, expected_page, page_tolerance):
                return 1.0 / rank
        return 0.0

    @staticmethod
    def precision_at_k(
        results: List[SearchResult],
        expected_source: str,
        expected_page: Optional[int] = None,
        k: int = 5,
        page_tolerance: int = 1,
    ) -> float:
        """
        Precision@K: Fraction of top-K results that are relevant.
        """
        top_k_results = results[:k]
        if not top_k_results:
            return 0.0
        hits = sum(
            1 for r in top_k_results
            if RetrievalMetrics.is_match(r, expected_source, expected_page, page_tolerance)
        )
        return hits / float(k)
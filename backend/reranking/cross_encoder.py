from backend.config import RetrievalConfig
from backend.models.search_result import SearchResult


class CrossEncoderReranker:

    def __init__(
        self,
        reranking_service,
    ):
        self.reranking_service = reranking_service

    def rerank(self, query: str, results: list[SearchResult], top_k: int = RetrievalConfig.RERANK_TOP_K) -> list[SearchResult]:
        """
        Re-rank retrieved documents using a Cross Encoder.
        """

        if not results:
            return []

        documents = [
            result.document
            for result in results
        ]

        scores = self.reranking_service.score(
            query,
            documents,
        )

        reranked_results = []

        for result, score in zip(results, scores):
            reranked_results.append(
                SearchResult(
                    document=result.document,
                    score=float(score),
                )
            )

        reranked_results.sort(
            key=lambda x: x.score,
            reverse=True,
        )

        return reranked_results[:top_k]
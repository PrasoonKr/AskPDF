from backend.models.search_result import SearchResult
from collections import defaultdict


class ReciprocalRankFusion:

    def __init__(
        self,
        k: int = 60,
    ):
        self.k = k

    def fuse(
        self,
        semantic_results,
        keyword_results,
    ):

        scores = defaultdict(float)

        documents = {}

        for rank, result in enumerate(
            semantic_results,
            start=1,
        ):

            doc_id = result.document.chunk_id

            scores[doc_id] += 1 / (
                self.k + rank
            )

            documents[doc_id] = result.document

        for rank, result in enumerate(
            keyword_results,
            start=1,
        ):

            doc_id = result.document.chunk_id

            scores[doc_id] += 1 / (
                self.k + rank
            )

            documents[doc_id] = result.document

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []

        for doc_id, score in ranked:

            results.append(
                SearchResult(
                    document=documents[doc_id],
                    score=score,
                )
            )

        return results
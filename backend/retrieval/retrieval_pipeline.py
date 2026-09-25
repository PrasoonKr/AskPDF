from backend.config import RetrievalConfig

from backend.observability.trace import (
    RetrievalTrace,
)


class RetrievalPipeline:

    def __init__(
        self,
        hybrid_search,
        reranker,
        query_rewriter,
    ):
        self.hybrid_search = hybrid_search
        self.reranker = reranker
        self.query_rewriter = query_rewriter

    def search(
        self,
        query: str,
        recent_turns=None,
        summary: str = "",
    ):

        trace = RetrievalTrace(
            original_query=query
        )

        # --------------------------------
        # Query rewriting
        # --------------------------------

        if RetrievalConfig.ENABLE_QUERY_REWRITING and (recent_turns or summary):
            rewritten_query = (
                self.query_rewriter.rewrite(
                    query=query,
                    recent_turns=recent_turns,
                    summary=summary,
                )
            )
        else:
            rewritten_query = query

        trace.rewritten_query = rewritten_query

        # --------------------------------
        # Hybrid search
        # --------------------------------

        hybrid_result = (
            self.hybrid_search.search(
                rewritten_query
            )
        )

        trace.semantic_results = (
            hybrid_result.semantic_results
        )

        trace.keyword_results = (
            hybrid_result.keyword_results
        )

        trace.fused_results = (
            hybrid_result.fused_results
        )

        results = hybrid_result.fused_results

        if not results:
            return [], trace

        # --------------------------------
        # Adaptive reranking
        # --------------------------------

        if (
            RetrievalConfig.ENABLE_RERANKING
            # and self._should_rerank(results)
        ):

            results = self.reranker.rerank(
                rewritten_query,
                results,
            )

            trace.reranked_results = results

        else:

            results = results[
                :RetrievalConfig.RERANK_TOP_K
            ]

        results = [
            r for r in results
            if r.score >= RetrievalConfig.SIMILARITY_THRESHOLD
        ]

        trace.final_results = results

        return results, trace

    # def _should_rerank(
    #     self,
    #     results,
    # ) -> bool:

    #     if len(results) < 2:
    #         return False

    #     score_difference = (
    #         results[0].score
    #         - results[1].score
    #     )

    #     return (
    #         score_difference
    #         < RetrievalConfig.RERANK_SCORE_MARGIN
    #     )
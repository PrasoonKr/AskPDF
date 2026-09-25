from backend.models.hybrid_search_result import (
    HybridSearchResult,
)


class HybridSearch:

    def __init__(
        self,
        semantic_search,
        keyword_search,
        rank_fusion,
    ):
        self.semantic_search = semantic_search
        self.keyword_search = keyword_search
        self.rank_fusion = rank_fusion

    def search(
        self,
        query: str,
    ) -> HybridSearchResult:

        semantic_results = (
            self.semantic_search.search(query)
        )

        keyword_results = (
            self.keyword_search.search(query)
        )

        fused_results = (
            self.rank_fusion.fuse(
                semantic_results,
                keyword_results,
            )
        )

        return HybridSearchResult(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            fused_results=fused_results,
        )
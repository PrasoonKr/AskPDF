from dataclasses import dataclass


@dataclass(slots=True)
class HybridSearchResult:
    """
    Contains all stages of hybrid retrieval.
    """

    semantic_results: list

    keyword_results: list

    fused_results: list
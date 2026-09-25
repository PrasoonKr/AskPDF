from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalTrace:
    """
    Stores debugging information for one retrieval request.
    """

    original_query: str

    rewritten_query: str = ""

    semantic_results: list[Any] = field(
        default_factory=list
    )

    keyword_results: list[Any] = field(
        default_factory=list
    )

    fused_results: list[Any] = field(
        default_factory=list
    )

    reranked_results: list[Any] = field(
        default_factory=list
    )

    final_results: list[Any] = field(
        default_factory=list
    )
from dataclasses import dataclass

from backend.models.search_result import SearchResult


@dataclass(slots=True)
class ChatResponse:

    answer: str

    sources: list[SearchResult]
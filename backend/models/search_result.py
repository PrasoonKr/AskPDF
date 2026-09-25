from dataclasses import dataclass

from backend.models.document import Document


@dataclass(slots=True)
class SearchResult:
    document: Document
    score: float
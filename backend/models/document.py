from backend.models.source import SourceDocument
from dataclasses import dataclass


@dataclass(slots=True)
class Document:
    """
    Represents a chunk of a document.
    """

    chunk_id: str

    source: SourceDocument

    page: int

    text: str
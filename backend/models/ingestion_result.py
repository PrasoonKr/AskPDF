from dataclasses import dataclass


@dataclass(slots=True)
class IngestionResult:
    """
    Represents the result of a document ingestion operation.
    """
    
    filename: str
    chunks: int
from dataclasses import dataclass


@dataclass(slots=True)
class Page:
    """
    Represents a single page extracted from a PDF.
    """

    number: int
    text: str
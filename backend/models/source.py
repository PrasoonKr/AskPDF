from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class SourceDocument:
    filename: str
    path: Path
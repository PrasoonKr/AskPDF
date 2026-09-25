from backend.config import ChunkerConfig
from backend.models.document import Document


def chunk_pages(
    pages,
    source,
    chunk_size=ChunkerConfig.CHUNK_SIZE,
    overlap=ChunkerConfig.OVERLAP,
):
    """
    Chunk every page separately.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be positive."
        )

    if overlap < 0:
        raise ValueError(
            "overlap must be non-negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size."
        )

    documents = []

    step = chunk_size - overlap

    for page in pages:

        words = page.text.split()

        chunk_number = 1

        for start in range(0, len(words), step):

            chunk = " ".join(words[start:start + chunk_size]).strip()

            if not chunk:
                continue

            documents.append(
                Document(
                    chunk_id=(
                        f"{source.filename}_"
                        f"page_{page.number}_"
                        f"chunk_{chunk_number}"
                    ),
                    source=source,
                    page=page.number,
                    text=chunk,
                )
            )

            chunk_number += 1

    return documents
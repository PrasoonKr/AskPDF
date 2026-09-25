from backend.models.source import SourceDocument
from pathlib import Path
from backend.ingestion.loader import load_pdf
from backend.ingestion.extractor import extract_text
from backend.ingestion.chunker import chunk_pages
from backend.models.ingestion_result import IngestionResult


class IngestionPipeline:
    """
    Coordinates the document ingestion process.
    """

    def __init__(
        self,
        embedding_service,
        document_store,
        keyword_search=None,
    ):
        self.embedding_service = embedding_service
        self.document_store = document_store
        self.keyword_search = keyword_search

    def ingest_pdf(self, pdf_path: str) -> IngestionResult:
        """
        Ingest a single PDF into the document store.
        """

        pdf = load_pdf(pdf_path)

        print(f"\nLoading: {pdf.name}")

        pages = extract_text(str(pdf))

        documents = chunk_pages(
            pages,
            source=SourceDocument(
                filename=pdf.name,
                path=Path(pdf_path),
            ),
        )

        embeddings = self.embedding_service.embed_documents(documents)

        self.document_store.add_documents(
            documents,
            embeddings,
        )

        result = IngestionResult(
            filename=pdf.name,
            chunks=len(documents),
        )
        
        if self.keyword_search is not None:
            self.keyword_search.build_index()

        print(f"✓ Indexed {result.chunks} chunks")

        return result

    def ingest_directory(self, directory_path: str):
        """
        Ingest all PDF files from a directory.
        """

        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(
                f"Directory not found: {directory_path}"
            )

        pdf_files = sorted(directory.glob("*.pdf"))

        if not pdf_files:
            print("No PDF files found.")
            return

        print("=" * 60)
        print("Building Knowledge Base")
        print("=" * 60)

        results = []

        for pdf in pdf_files:
            result = self.ingest_pdf(str(pdf))
            results.append(result)

        total_chunks = sum(
            result.chunks
            for result in results
        )

        print("\n" + "=" * 60)
        print("Knowledge Base Built Successfully")
        print("=" * 60)

        print(f"Files Indexed : {len(results)}")
        print(f"Chunks Indexed: {total_chunks}")

        print("=" * 60)
class IngestionService:

    def __init__(
        self,
        ingestion_pipeline,
        document_store,
        keyword_search,
    ):
        self.ingestion_pipeline = ingestion_pipeline
        self.document_store = document_store
        self.keyword_search = keyword_search

    def ingest(
        self,
        file_path: str,
    ):
        result = self.ingestion_pipeline.ingest_pdf(
            file_path
        )
        return result
from backend.config import RetrievalConfig


class SemanticSearch:

    def __init__(
        self,
        embedding_service,
        document_store,
    ):
        self.embedding_service = embedding_service
        self.document_store = document_store

    def search(
        self,
        query: str,
    ):

        embedding = self.embedding_service.embed_query(query)

        return self.document_store.semantic_search(
            embedding,
            top_k=RetrievalConfig.SEARCH_TOP_K,
        )
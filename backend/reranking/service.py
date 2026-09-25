from backend.reranking.model import model


class RerankingService:
    """
    Service responsible for scoring
    (query, document) pairs.
    """

    def score(self, query: str, documents):

        pairs = [
            (query, document.text)
            for document in documents
        ]

        scores = model.predict(pairs)

        return scores
import torch
from backend.reranking.model import model



class RerankingService:
    """
    Service responsible for scoring (query, document) pairs.
    Optimized for fast CPU inference by using sequence truncation, multi-threading,
    and batching.
    """

    def score(self, query: str, documents):
        if not documents:
            return []


        # Only rerank top 5 candidates and truncate to 500 chars to avoid O(N^2) attention cost on CPU
        target_docs = documents[:5]
        pairs = [
            (query, doc.text[:500])
            for doc in target_docs
        ]

        with torch.inference_mode():
            scores = model.predict(pairs, batch_size=5, show_progress_bar=False)

        return list(scores)
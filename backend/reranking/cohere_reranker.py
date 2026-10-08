import os
import cohere
from typing import List, Any
from backend.retrieval.rank_fusion import SearchResult

class NativeCohereReranker:
    """
    Client for reranking using Cohere's Native API.
    Uses 'rerank-english-v3.0'.
    """
    def __init__(self, model="rerank-english-v3.0"):
        self.model = model
        self.client = cohere.Client(os.getenv("COHERE_API_KEY", "dummy_key"))

    def rerank(self, query: str, documents: List[Any], top_k: int = 5) -> List[SearchResult]:
        if not documents:
            return []

        # Extract text content from documents
        doc_texts = []
        for doc in documents:
            if isinstance(doc, dict):
                doc_texts.append(doc.get("content", ""))
            else:
                doc_obj = getattr(doc, "document", doc)
                doc_texts.append(getattr(doc_obj, "page_content", str(doc)))

        try:
            response = self.client.rerank(
                query=query,
                documents=doc_texts,
                model=self.model,
                top_n=top_k
            )

            reranked_results = []
            for result in response.results:
                original_doc = documents[result.index]
                reranked_results.append(SearchResult(
                    document=getattr(original_doc, "document", original_doc),
                    score=result.relevance_score
                ))

            return reranked_results
        except Exception as e:
            print(f"Error calling Cohere Rerank: {e}")
            return [SearchResult(
                document=getattr(doc, "document", doc), 
                score=0.0
            ) for doc in documents[:top_k]]

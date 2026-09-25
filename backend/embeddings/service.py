from backend.models.document import Document
from typing import List

# import faiss
import numpy as np

from backend.embeddings.model import model


class EmbeddingService:
    """
    Service responsible for generating and preparing embeddings.

    Responsibilities:
    - Generate query embeddings
    - Generate document embeddings
    - Convert embeddings to NumPy arrays
    - Convert embeddings to float32
    - Normalize embeddings for cosine similarity
    - Provide embedding dimension
    """

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate an embedding for a user query.
        """
        embedding = model.encode(query)
        return self._prepare_query_embedding(embedding)

    def embed_documents(self, documents: List[Document]) -> np.ndarray:
        """
        Generate embeddings for multiple documents.
        """
        texts = [document.text for document in documents]
        embeddings = model.encode(texts)
        return self._prepare_document_embeddings(embeddings)

    def dimension(self) -> int:
        """
        Return the embedding dimension of the current model.
        """
        return model.get_embedding_dimension()

    def _prepare_query_embedding(
        self,
        embedding: np.ndarray
    ) -> np.ndarray:
        """
        Prepare a single query embedding for FAISS.
        """

        embedding = np.asarray(embedding, dtype=np.float32)

        # FAISS expects shape (1, dimension)
        embedding = embedding.reshape(1, -1)

        # Normalize for cosine similarity
        # faiss.normalize_L2(embedding)
        embedding /= np.linalg.norm(embedding, axis=1, keepdims=True)

        return embedding

    def _prepare_document_embeddings(
        self,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Prepare document embeddings for FAISS.
        """

        embeddings = np.asarray(embeddings, dtype=np.float32)

        # Shape should be (num_documents, dimension)
        embeddings = embeddings.reshape(
            len(embeddings),
            self.dimension()
        )

        # Normalize for cosine similarity
        # faiss.normalize_L2(embeddings)
        embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)

        return embeddings
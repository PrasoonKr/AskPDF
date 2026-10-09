import os
import cohere

class CohereEmbeddingService:
    """
    Client for generating embeddings using Cohere's Native API.
    Uses 'embed-english-v3.0' which outputs 1024 dimensions.
    """
    def __init__(self, model="embed-english-v3.0"):
        self.model = model
        self.client = cohere.Client(os.getenv("COHERE_API_KEY", "dummy_key"))

    def embed_query(self, query: str) -> list[float]:
        response = self.client.embed(
            texts=[query], 
            model=self.model, 
            input_type="search_query"
        )
        import numpy as np
        emb = np.array(response.embeddings[0], dtype=np.float32).reshape(1, -1)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        return emb

    def dimension(self) -> int:
        return 1024

    def embed_documents(self, documents: list) -> list[list[float]]:
        # Extract text from Document objects or dicts
        texts = []
        for doc in documents:
            if hasattr(doc, "text"):
                texts.append(doc.text)
            elif isinstance(doc, dict):
                texts.append(doc.get("text", str(doc)))
            else:
                texts.append(str(doc))

        import numpy as np
        # Cohere API limits to 96 texts per call — batch accordingly
        BATCH_SIZE = 96
        all_embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            response = self.client.embed(
                texts=batch,
                model=self.model,
                input_type="search_document"
            )
            all_embeddings.append(np.array(response.embeddings, dtype=np.float32))

        emb = np.vstack(all_embeddings)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        return emb

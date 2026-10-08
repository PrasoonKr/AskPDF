import json
import boto3
import numpy as np
from typing import List
from backend.models.document import Document

class BedrockEmbeddingService:
    """
    Embedding service using Amazon Titan via AWS Bedrock.
    """
    def __init__(self, model_id="amazon.titan-embed-text-v2:0", region_name="us-east-1"):
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self._dim = 1024 # Titan v2 default dimension

    def dimension(self) -> int:
        return self._dim

    def embed_query(self, query: str) -> np.ndarray:
        body = json.dumps({"inputText": query})
        response = self.client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get('body').read())
        embedding = response_body.get('embedding')
        
        # Prepare for FAISS (reshape and normalize)
        emb = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        return emb

    def embed_documents(self, documents: List[Document]) -> np.ndarray:
        embeddings = []
        for doc in documents:
            body = json.dumps({"inputText": doc.text})
            response = self.client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get('body').read())
            embeddings.append(response_body.get('embedding'))
            
        emb = np.asarray(embeddings, dtype=np.float32)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
        return emb

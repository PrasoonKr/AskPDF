import os
import cohere
import numpy as np

client = cohere.Client(os.getenv("COHERE_API_KEY"))
response = client.embed(texts=["test"], model="embed-english-v3.0", input_type="search_query")
emb = np.array(response.embeddings[0], dtype=np.float32)
print("Shape:", emb.shape)
print("ndim:", emb.ndim)
emb = emb.reshape(1, -1)
print("After reshape:", emb.shape)

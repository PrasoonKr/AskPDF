import os
from openai import OpenAI

client = OpenAI()

try:
    print("Testing embeddings on proxy...")
    # Trying standard OpenAI embedding model name, or a proxy-specific name
    response = client.embeddings.create(
        model="amazon.titan-embed-text-v2:0", 
        input=["Hello world"]
    )
    print("SUCCESS!")
    print("Dimension:", len(response.data[0].embedding))
except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", e)
    if hasattr(e, 'body'):
        print("BODY:", e.body)

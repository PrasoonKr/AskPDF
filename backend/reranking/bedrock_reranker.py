import json
import boto3
from typing import List
from backend.models.search_result import SearchResult

class BedrockCohereReranker:
    """
    Reranker using Cohere Rerank 3.5 via AWS Bedrock.
    """
    def __init__(self, region_name="us-east-1"):
        self.model_id = "cohere.rerank-v3-5:0"
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def rerank(self, query: str, search_results: List[SearchResult]) -> List[SearchResult]:
        if not search_results:
            return []
            
        documents = [res.document.text for res in search_results]
        
        body = json.dumps({
            "query": query,
            "documents": documents,
            "api_version": 2
        })
        
        response = self.client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        results = response_body.get('results', [])
        
        # Sort original search_results based on new scores
        reranked = []
        for res in results:
            idx = res.get('index')
            score = res.get('relevance_score')
            original_result = search_results[idx]
            original_result.score = score
            reranked.append(original_result)
            
        return reranked

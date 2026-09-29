class EmbeddingConfig:
    MODEL = "BAAI/bge-small-en-v1.5"

class ChunkerConfig:
    CHUNK_SIZE = 400
    OVERLAP = 75

class LLMConfig:
    MODEL = "qwen2.5:3b"
    TEMPERATURE = 0.2
    NUM_CTX = 2048  # Profiled: 2048 gives 0.6s TTFT vs 4.3s with 4096 on CPU
    
class RerankerConfig:
    MODEL = "BAAI/bge-reranker-base"

class RetrievalConfig:
    SEARCH_TOP_K = 10
    RERANK_TOP_K = 3  # 3 chunks is the sweet spot for CPU Ollama latency
    ENABLE_RERANKING = True
    RERANK_SCORE_MARGIN = 0.05
    SIMILARITY_THRESHOLD = 0.35
    RERANK_THRESHOLD = 0.001
    ENABLE_QUERY_REWRITING = True
    
class ConversationConfig:
    MAX_RECENT_TURNS = 5
    SUMMARIZE_TURN_COUNT = 2
    REWRITE_HISTORY_TURNS = 3
    GENERATION_HISTORY_TURNS = 3

class DebugConfig:
    DEBUG = False
    SHOW_SEARCH_RESULTS = False
    
class ObservabilityConfig:
    ENABLE_TRACING = True
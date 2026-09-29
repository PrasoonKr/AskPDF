import sys
import os
sys.path.insert(0, os.path.abspath("."))

imports = [
    "from backend.application import Application",
    "from backend.services.assistant_service import ResearchAssistantService",
    "from backend.services.ingestion_service import IngestionService",
    "from backend.services.session_service import SessionService",
    "from backend.retrieval.rank_fusion import ReciprocalRankFusion",
    "from backend.config import ObservabilityConfig, ConversationConfig",
    "from backend.observability.formatter import TraceFormatter",
    "from backend.conversation.summarizer import ConversationSummarizer",
    "from backend.conversation.formatter import ConversationFormatter",
    "from backend.conversation.memory import ConversationMemory",
    "from backend.llm.service import LLMService",
    "from backend.llm.client import OllamaClient",
    "from backend.llm.generator import AnswerGenerator",
    "from backend.query.hybrid_rewriter import HybridRewriter",
    "from backend.query.llm_rewriter import LLMRewriter",
    "from backend.query.rule_based import RuleBasedRewriter",
    "from backend.prompts.context_builder import ContextBuilder",
    "from backend.retrieval.retrieval_pipeline import RetrievalPipeline",
    "from backend.reranking.service import RerankingService",
    "from backend.reranking.cross_encoder import CrossEncoderReranker",
    "from backend.retrieval.semantic_search import SemanticSearch",
    "from backend.retrieval.keyword_search import KeywordSearch",
    "from backend.retrieval.hybrid_search import HybridSearch",
    "from backend.embeddings.service import EmbeddingService",
    "from backend.retrieval.document_store import DocumentStore",
    "from backend.ingestion.pipeline import IngestionPipeline",
    "from backend.adaptive.pipeline import AdaptiveRAGPipeline",
]

for stmt in imports:
    print(f"Testing: {stmt}", flush=True)
    exec(stmt)
    print(f"  OK", flush=True)

print("ALL IMPORTS COMPLETED!", flush=True)

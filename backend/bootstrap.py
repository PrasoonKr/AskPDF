
from backend.application import Application

from backend.services.assistant_service import ResearchAssistantService
from backend.services.ingestion_service import IngestionService
from backend.services.session_service import SessionService

from backend.retrieval.rank_fusion import ReciprocalRankFusion
from backend.config import ObservabilityConfig, ConversationConfig
from backend.observability.formatter import TraceFormatter
from backend.conversation.summarizer import ConversationSummarizer
from backend.conversation.formatter import ConversationFormatter
from backend.conversation.memory import ConversationMemory
from backend.llm.service import LLMService
from backend.llm.client import OllamaClient
from backend.llm.generator import AnswerGenerator
from backend.query.hybrid_rewriter import HybridRewriter
from backend.query.llm_rewriter import LLMRewriter
from backend.query.rule_based import RuleBasedRewriter
from backend.prompts.context_builder import ContextBuilder
from backend.retrieval.retrieval_pipeline import RetrievalPipeline
from backend.reranking.service import RerankingService
from backend.reranking.cross_encoder import CrossEncoderReranker
from backend.retrieval.semantic_search import SemanticSearch
from backend.retrieval.keyword_search import KeywordSearch
from backend.retrieval.hybrid_search import HybridSearch
from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.ingestion.pipeline import IngestionPipeline


def startup(user_email: str = "default") -> Application:
    """
    Build the application and all long-lived services.
    """

    trace_formatter = TraceFormatter()
    embedding_service = EmbeddingService()
    document_store = DocumentStore(embedding_service, user_email)

    semantic_search = SemanticSearch(embedding_service, document_store)
    keyword_search = KeywordSearch(document_store)
    rank_fusion = ReciprocalRankFusion()
    hybrid_search = HybridSearch(semantic_search, keyword_search, rank_fusion)

    reranking_service = RerankingService()
    reranker = CrossEncoderReranker(reranking_service)

    ollama_client = OllamaClient()
    llm_service = LLMService(ollama_client)
    answer_generator = AnswerGenerator(llm_service)

    conversation_formatter = ConversationFormatter()
    conversation_summarizer = ConversationSummarizer(
        llm_service=llm_service,
        conversation_formatter=conversation_formatter,
    )

    def memory_factory():
        return ConversationMemory(
            summarizer=conversation_summarizer,
            max_recent_turns=ConversationConfig.MAX_RECENT_TURNS,
            summarize_turn_count=ConversationConfig.SUMMARIZE_TURN_COUNT,
        )

    session_service = SessionService(memory_factory=memory_factory)

    rule_rewriter = RuleBasedRewriter()
    llm_rewriter = LLMRewriter(llm_service, conversation_formatter)
    query_rewriter = HybridRewriter(rule_rewriter, llm_rewriter)

    retrieval_pipeline = RetrievalPipeline(hybrid_search, reranker, query_rewriter)
    context_builder = ContextBuilder()

    ingestion_pipeline = IngestionPipeline(
        embedding_service, document_store, keyword_search
    )

    if document_store.exists():
        print("Loading Knowledge Base...")
        document_store.load()
        keyword_search.build_index()
        print(f"Loaded {document_store.count()} documents.")
    else:
        import os
        os.makedirs(f"backend/documents/{user_email}", exist_ok=True)
        ingestion_pipeline.ingest_directory(f"backend/documents/{user_email}")
        document_store.save()
        print("Knowledge Base saved.")

    assistant_service = ResearchAssistantService(
        retrieval_pipeline=retrieval_pipeline,
        context_builder=context_builder,
        answer_generator=answer_generator,
        conversation_formatter=conversation_formatter,
        session_service=session_service,
        trace_formatter=trace_formatter,
    )

    ingestion_service = IngestionService(
        ingestion_pipeline=ingestion_pipeline,
        document_store=document_store,
        keyword_search=keyword_search,
    )

    return Application(
        assistant_service=assistant_service,
        ingestion_service=ingestion_service,
    )
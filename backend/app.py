from backend.retrieval.rank_fusion import ReciprocalRankFusion
from backend.config import ObservabilityConfig
from backend.observability.formatter import TraceFormatter
from backend.conversation.summarizer import ConversationSummarizer
from backend.conversation.formatter import ConversationFormatter
from backend.config import ConversationConfig
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
# from backend.evaluation.test import embedding_service
from backend.retrieval.hybrid_search import HybridSearch
from backend.config import DebugConfig
from backend.utils.display import print_search_results
from backend.embeddings.service import EmbeddingService
from backend.retrieval.document_store import DocumentStore
from backend.ingestion.pipeline import IngestionPipeline
from backend.prompts.builder import build_prompt


def startup():
    
    trace_formatter = TraceFormatter()

    # --------------------------------
    # Embeddings
    # --------------------------------

    embedding_service = EmbeddingService()

    # --------------------------------
    # Document Store
    # --------------------------------

    document_store = DocumentStore(
        embedding_service
    )

    # --------------------------------
    # Semantic Search
    # --------------------------------

    semantic_search = SemanticSearch(
        embedding_service,
        document_store,
    )

    # --------------------------------
    # Keyword Search
    # --------------------------------

    keyword_search = KeywordSearch(
        document_store
    )

    # --------------------------------
    # Hybrid Search
    # --------------------------------

    rank_fusion = ReciprocalRankFusion()

    hybrid_search = HybridSearch(
        semantic_search=semantic_search,
        keyword_search=keyword_search,
        rank_fusion=rank_fusion,
    )

    # --------------------------------
    # Reranking
    # --------------------------------

    reranking_service = RerankingService()

    reranker = CrossEncoderReranker(
        reranking_service
    )

    # --------------------------------
    # LLM
    # --------------------------------

    ollama_client = OllamaClient()

    llm_service = LLMService(
        ollama_client
    )

    answer_generator = AnswerGenerator(
        llm_service
    )
    
    
    # --------------------------------
    # Conversation Memory
    # --------------------------------
    
    conversation_formatter = (
        ConversationFormatter()
    )

    conversation_summarizer = (
        ConversationSummarizer(
            llm_service=llm_service,
            conversation_formatter=(
                conversation_formatter
            ),
        )
    )

    conversation_memory = (
        ConversationMemory(
            summarizer=conversation_summarizer,
            max_recent_turns=(
                ConversationConfig.MAX_RECENT_TURNS
            ),
            summarize_turn_count=(
                ConversationConfig
                .SUMMARIZE_TURN_COUNT
            ),
        )
    )
    

    # --------------------------------
    # Query Rewriting
    # --------------------------------

    rule_rewriter = RuleBasedRewriter()

    llm_rewriter = LLMRewriter(
        llm_service, conversation_formatter
    )

    query_rewriter = HybridRewriter(
        rule_rewriter,
        llm_rewriter,
    )

    # --------------------------------
    # Retrieval Pipeline
    # --------------------------------

    retrieval_pipeline = RetrievalPipeline(
        hybrid_search,
        reranker,
        query_rewriter,
    )

    # --------------------------------
    # Context Builder
    # --------------------------------

    context_builder = ContextBuilder()

    # --------------------------------
    # Ingestion
    # --------------------------------

    pipeline = IngestionPipeline(
        embedding_service,
        document_store,
        keyword_search,
    )

    # --------------------------------
    # Knowledge Base
    # --------------------------------

    if document_store.exists():

        print("Loading Knowledge Base...")

        document_store.load()

        keyword_search.build_index()

        print(
            f"Loaded {document_store.count()} documents."
        )

    else:

        pipeline.ingest_directory(
            "backend/documents"
        )

        document_store.save()

        print("Knowledge Base saved.")

    return (
        retrieval_pipeline,
        context_builder,
        answer_generator,
        conversation_memory,
        conversation_formatter,
        trace_formatter
    )


def chat_loop(retrieval_pipeline, context_builder, answer_generator, conversation_memory, conversation_formatter, trace_formatter):
    """
    Start the interactive chat.
    """

    while True:

        query = input("\nAsk a question ('exit' to quit): ").strip()

        if query.lower() == "exit":
            print("\nGoodbye!")
            break
        
        # --------------------------------
        # History for query rewriting
        # --------------------------------

        summary = (
            conversation_memory.get_summary()
        )
        
        rewrite_history = (
            conversation_memory.get_recent_turns(
                limit=(
                    ConversationConfig
                    .GENERATION_HISTORY_TURNS
                )
            )
        )

        # --------------------------------
        # Retrieval
        # --------------------------------

        results, trace = retrieval_pipeline.search(
            query=query,
            recent_turns=rewrite_history,
            summary=summary
        )
        
        if ObservabilityConfig.ENABLE_TRACING:
            print(
                trace_formatter.format(trace)
            )
        
        # if DebugConfig.DEBUG and DebugConfig.SHOW_SEARCH_RESULTS:
        #     print_search_results(results)
            
        # --------------------------------
        # Retrieved context
        # --------------------------------

        context = context_builder.build(
            results
        )

        # --------------------------------
        # History for answer generation
        # --------------------------------

        generation_history = (
            conversation_memory.get_recent_turns(
                limit=(
                    ConversationConfig
                    .GENERATION_HISTORY_TURNS
                )
            )
        )


        formatted_conversation = (
            conversation_formatter.format(
                generation_history
            )
        )

        # --------------------------------
        # Final prompt
        # --------------------------------

        prompt = build_prompt(
            query=query,
            context=context,
            conversation=formatted_conversation,
            conversation_summary=summary
        )

        # --------------------------------
        # Generate answer
        # --------------------------------

        answer = answer_generator.generate(
            prompt
        )

        # --------------------------------
        # Save completed turn
        # --------------------------------

        conversation_memory.add_turn(
            user=query,
            assistant=answer,
        )

        # --------------------------------
        # Display answer
        # --------------------------------

        print("\nAnswer")
        print("-" * 60)
        print(answer)


def main():

    retrieval_pipeline, context_builder, answer_generator, conversation_memory, conversation_formatter, trace_formatter = startup()

    chat_loop(retrieval_pipeline, context_builder, answer_generator, conversation_memory, conversation_formatter, trace_formatter)


if __name__ == "__main__":
    main()
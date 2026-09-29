import time
import sys
from typing import List, Dict, Any, Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.adaptive.models import (
    RouteType,
    RouteDecision,
    GradeResult,
    AdaptiveStepTrace,
    AdaptiveRAGResult,
)
from backend.adaptive.router import AdaptiveRouter
from backend.adaptive.grader import RelevanceGrader
from backend.adaptive.rewriter import SelfCorrectingRewriter
from backend.adaptive.web_search import WebSearchService
from backend.retrieval.rank_fusion import ReciprocalRankFusion


class AdaptiveRAGPipeline:
    """
    Adaptive RAG Architecture:
    1. Query Analyzer / Router: Routes to simple_rag, multi_query_rag, or web_search
    2. Execution:
       - simple_rag: Single-pass hybrid search + RRF
       - multi_query_rag: Multi-perspective decomposition, parallel retrieval & fusion
       - web_search: Outside world / real-time knowledge
    3. Cross-Encoder Re-ranking on top fused candidates
    4. Relevance Grading & Iterative Self-Correction:
       - If relevance grader flags context as insufficient, rewrites query and re-retrieves
       - Prevents hallucinations before sending context to LLM generator
    """

    def __init__(
        self,
        retrieval_pipeline,
        llm_service=None,
        max_retries: int = 2,
    ):
        self.retrieval_pipeline = retrieval_pipeline
        self.llm_service = llm_service
        self.max_retries = max_retries

        self.router = AdaptiveRouter(llm_service=llm_service)
        self.grader = RelevanceGrader(llm_service=llm_service)
        self.rewriter = SelfCorrectingRewriter(llm_service=llm_service)
        self.web_search = WebSearchService()
        self.rank_fusion = ReciprocalRankFusion()

    def execute(
        self,
        query: str,
        recent_turns=None,
        summary: str = "",
    ) -> AdaptiveRAGResult:
        trace_steps: List[AdaptiveStepTrace] = []
        step_idx = 1

        print("\n" + "=" * 65, flush=True)
        print("  🧠 AskPDF Adaptive RAG Decision Layer", flush=True)
        print("=" * 65, flush=True)
        print(f"  [Input Query]: \"{query}\"", flush=True)

        # -------------------------------------------------------------
        # STEP 1: Query Analysis & Routing
        # -------------------------------------------------------------
        t_route_start = time.time()
        decision: RouteDecision = self.router.route(query)
        route_time = time.time() - t_route_start

        print(f"\n  🔀 [Step 1: Router] -> {decision.route.value.upper()} (Confidence: {decision.confidence:.2f}, Latency: {route_time*1000:.1f}ms)", flush=True)
        print(f"     └─ Reasoning: {decision.reasoning}", flush=True)

        trace_steps.append(
            AdaptiveStepTrace(
                step_number=step_idx,
                step_type="routing",
                query_used=query,
                decision_or_grade=decision.route.value,
                details={
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "sub_queries": decision.sub_queries,
                },
            )
        )
        step_idx += 1

        # -------------------------------------------------------------
        # BRANCH: Web Search (Outside Knowledge)
        # -------------------------------------------------------------
        if decision.route == RouteType.WEB_SEARCH:
            print(f"  🌐 [Step 2: External Web Search] Querying DuckDuckGo...", flush=True)
            t_web_start = time.time()
            web_results = self.web_search.search(query)
            web_time = time.time() - t_web_start
            print(f"     └─ Retrieved {len(web_results)} live web sources in {web_time:.2f}s", flush=True)

            context_blocks = [
                f"[Source: {r['source']} - {r['title']}]\n{r['text']}"
                for r in web_results
            ]
            context_text = "\n\n".join(context_blocks)
            trace_steps.append(
                AdaptiveStepTrace(
                    step_number=step_idx,
                    step_type="web_search",
                    query_used=query,
                    decision_or_grade="retrieved_from_web",
                    details={"results_count": len(web_results)},
                )
            )
            print("=" * 65 + "\n", flush=True)
            return AdaptiveRAGResult(
                route_chosen=RouteType.WEB_SEARCH,
                total_attempts=1,
                is_relevant=True,
                documents=web_results,
                context_text=context_text,
                trace=trace_steps,
            )

        # -------------------------------------------------------------
        # BRANCH: Document Retrieval (Simple RAG or Multi-Query RAG)
        # with Relevance Grading & Self-Correction Loop
        # -------------------------------------------------------------
        current_query = query
        attempt = 1
        final_docs = []
        is_relevant = False

        while attempt <= self.max_retries:
            t_retrieval_start = time.time()
            if decision.route == RouteType.MULTI_QUERY_RAG and attempt == 1:
                print(f"  🔎 [Step 2: Query Decomposition] Multi-Perspective Decomposition:", flush=True)
                for idx, sq in enumerate(decision.sub_queries, 1):
                    prefix = "├─" if idx < len(decision.sub_queries) else "└─"
                    print(f"     {prefix} Perspective {idx}: \"{sq}\"", flush=True)

                candidate_lists = []
                for sq in decision.sub_queries:
                    # Fast hybrid retrieval on each perspective without repeated CPU cross-encoder rerank
                    h_res = self.retrieval_pipeline.hybrid_search.search(sq)
                    candidate_lists.append(h_res.fused_results)

                # Fuse multiple query perspectives via RRF
                if len(candidate_lists) >= 2:
                    fused_candidates = self.rank_fusion.fuse(candidate_lists[0], candidate_lists[1])
                elif candidate_lists:
                    fused_candidates = candidate_lists[0]
                else:
                    fused_candidates = []

                # Single-pass CrossEncoder rerank on the fused candidate pool
                retrieved_docs = self.retrieval_pipeline.reranker.rerank(query, fused_candidates)
                ret_time = time.time() - t_retrieval_start
                top_doc = retrieved_docs[0] if retrieved_docs else None
                top_name = getattr(getattr(getattr(top_doc, "document", None), "source", None), "filename", "None")
                top_page = getattr(getattr(top_doc, "document", None), "page", "?")
                top_score = getattr(top_doc, "score", 0.0)
                print(f"  🔗 [RRF Rank Fusion & Rerank] Fused {len(fused_candidates)} -> Top Result: [{top_name} p.{top_page}] Score: {top_score:.3f} ({ret_time:.2f}s)", flush=True)
            else:
                prefix = f"[Attempt {attempt}]" if attempt > 1 else "[Step 2: Retrieval]"
                print(f"  📚 {prefix} Hybrid Retrieval & Cross-Encoder Reranking...", flush=True)
                # Direct hybrid search + rerank (bypasses LLM query rewriter which costs ~6s on CPU)
                h_res = self.retrieval_pipeline.hybrid_search.search(current_query)
                retrieved_docs = self.retrieval_pipeline.reranker.rerank(current_query, h_res.fused_results)
                ret_time = time.time() - t_retrieval_start
                top_doc = retrieved_docs[0] if retrieved_docs else None
                top_name = getattr(getattr(getattr(top_doc, "document", None), "source", None), "filename", "None")
                top_page = getattr(getattr(top_doc, "document", None), "page", "?")
                top_score = getattr(top_doc, "score", 0.0)
                print(f"     └─ Top Result: [{top_name} p.{top_page}] Score: {top_score:.3f} (Retrieved in {ret_time:.2f}s)", flush=True)

            # 2. Relevance Grading
            t_grade_start = time.time()
            grade: GradeResult = self.grader.grade(query, retrieved_docs)
            grade_time = time.time() - t_grade_start

            grade_icon = "✅" if grade.is_relevant else "❌"
            print(f"  {grade_icon} [Step 3: Relevance Grader] -> {'RELEVANT' if grade.is_relevant else 'INSUFFICIENT'} ({grade_time*1000:.1f}ms)", flush=True)
            print(f"     └─ Evaluation: {grade.reasoning}", flush=True)

            trace_steps.append(
                AdaptiveStepTrace(
                    step_number=step_idx,
                    step_type=f"retrieval_attempt_{attempt}",
                    query_used=current_query,
                    decision_or_grade="RELEVANT" if grade.is_relevant else "NOT_RELEVANT",
                    details={
                        "retrieved_count": len(retrieved_docs),
                        "grade_reasoning": grade.reasoning,
                        "missing_aspects": grade.missing_aspects,
                        "top_score": getattr(retrieved_docs[0], "score", None) if retrieved_docs else None,
                    },
                )
            )
            step_idx += 1

            if grade.is_relevant:
                is_relevant = True
                final_docs = retrieved_docs
                break
            else:
                # 3. Self-Correction: Query Reformulation
                if attempt < self.max_retries:
                    print(f"  🔄 [Self-Correction Loop] Triggering Query Reformulation for Attempt {attempt+1}...", flush=True)
                    new_query = self.rewriter.rewrite_failed_query(
                        original_query=query,
                        critique=grade.reasoning,
                        missing_aspects=grade.missing_aspects,
                        attempt_number=attempt,
                    )
                    print(f"     └─ Reformulated: \"{new_query}\"", flush=True)

                    trace_steps.append(
                        AdaptiveStepTrace(
                            step_number=step_idx,
                            step_type="query_self_correction",
                            query_used=current_query,
                            decision_or_grade=f"rewritten_to: {new_query}",
                            details={
                                "original": query,
                                "rewritten": new_query,
                                "missing_targeted": grade.missing_aspects,
                            },
                        )
                    )
                    step_idx += 1
                    current_query = new_query
                    attempt += 1
                else:
                    # Exceeded retries; keep whatever was retrieved
                    print(f"  ⚠️  [Max Retries Exceeded] Returning best available candidate context.", flush=True)
                    final_docs = retrieved_docs
                    attempt += 1
                    break

        from backend.config import RetrievalConfig
        top_k = RetrievalConfig.RERANK_TOP_K
        print(f"  🤖 [Answer Generation] Passing {len(final_docs[:top_k])} verified chunks to LLM...", flush=True)
        print("=" * 65 + "\n", flush=True)

        # Assemble final context (truncate each chunk to keep prompt lean for CPU inference)
        context_blocks = []
        for d in final_docs[:top_k]:
            doc_obj = getattr(d, "document", d)
            text = getattr(doc_obj, "text", str(d))[:400]
            meta_src = getattr(getattr(doc_obj, "source", None), "filename", "Document")
            meta_page = getattr(doc_obj, "page", None)
            loc = f"{meta_src}, Page {meta_page}" if meta_page is not None else meta_src
            context_blocks.append(f"[{loc}]\n{text}")

        context_text = "\n\n---\n\n".join(context_blocks)

        return AdaptiveRAGResult(
            route_chosen=decision.route,
            total_attempts=min(attempt, self.max_retries),
            is_relevant=is_relevant,
            documents=final_docs,
            context_text=context_text,
            trace=trace_steps,
        )

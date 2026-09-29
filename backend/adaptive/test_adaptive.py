import sys
from backend.adaptive.models import RouteType
from backend.adaptive.router import AdaptiveRouter
from backend.adaptive.grader import RelevanceGrader
from backend.adaptive.rewriter import SelfCorrectingRewriter
from backend.adaptive.web_search import WebSearchService


def test_adaptive_routing():
    print("\n--- 1. Testing Adaptive Router ---")
    router = AdaptiveRouter()

    test_queries = [
        ("What is the CAP theorem in distributed systems?", RouteType.SIMPLE_RAG),
        ("What are the seven base SI units in physics?", RouteType.SIMPLE_RAG),
        ("Compare write-through vs write-back caching and how does it affect database replication?", RouteType.MULTI_QUERY_RAG),
        ("What is the difference between sharding and partitioning?", RouteType.MULTI_QUERY_RAG),
        ("What is the latest news and weather today in New York?", RouteType.WEB_SEARCH),
        ("Search the web for current bitcoin stock price", RouteType.WEB_SEARCH),
    ]

    for q, expected in test_queries:
        decision = router.route(q)
        status = "PASSED" if decision.route == expected else "FAILED"
        print(f"[{status}] Query: '{q[:50]}...'")
        print(f"         -> Route: {decision.route.value} (Expected: {expected.value})")
        print(f"         -> Reasoning: {decision.reasoning}")
        if decision.sub_queries and len(decision.sub_queries) > 1:
            print(f"         -> Sub-queries: {decision.sub_queries}")


def test_relevance_grader():
    print("\n--- 2. Testing Relevance Grader ---")
    grader = RelevanceGrader()

    class MockDoc:
        def __init__(self, text, score=0.8):
            self.text = text
            self.score = score

    # Case A: Highly relevant documents
    query_a = "What is database sharding and partitioning?"
    docs_a = [
        MockDoc("Database sharding is a horizontal partitioning technique that splits rows across multiple database servers."),
        MockDoc("Partitioning divides large tables into smaller logical chunks to improve query performance."),
    ]
    grade_a = grader.grade(query_a, docs_a)
    print(f"[RELEVANT TEST] Result: {'PASSED' if grade_a.is_relevant else 'FAILED'}")
    print(f"                Reason: {grade_a.reasoning}")

    # Case B: Irrelevant noise documents
    query_b = "What is the CAP theorem in distributed systems?"
    docs_b = [
        MockDoc("Centripetal acceleration in circular motion is directed towards the center of curvature."),
        MockDoc("Relative velocity in one dimension is calculated by subtracting reference velocities."),
    ]
    grade_b = grader.grade(query_b, docs_b)
    print(f"[IRRELEVANT TEST] Result: {'PASSED' if not grade_b.is_relevant else 'FAILED'}")
    print(f"                  Reason: {grade_b.reasoning}")
    print(f"                  Missing aspects: {grade_b.missing_aspects}")


def test_self_correcting_rewriter():
    print("\n--- 3. Testing Self-Correcting Query Rewriter ---")
    rewriter = SelfCorrectingRewriter()
    original_query = "What is CAP theorem?"
    critique = "Retrieved passages discuss rotational kinematics; missing CAP theorem and consistency properties."
    missing_aspects = ["cap", "theorem", "consistency", "partition", "tolerance"]

    rewritten = rewriter.rewrite_failed_query(original_query, critique, missing_aspects, attempt_number=1)
    print(f"Original:  '{original_query}'")
    print(f"Rewritten: '{rewritten}'")
    assert "cap" in rewritten.lower()


def test_web_search():
    print("\n--- 4. Testing Web Search (Outside Knowledge) ---")
    web_service = WebSearchService()
    results = web_service.search("What is the capital of France?")
    print(f"Retrieved {len(results)} external results:")
    for r in results[:2]:
        print(f"  - [{r['source']}] {r['title']}: {r['text'][:90]}...")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing AskPDF Adaptive RAG Decision Layer Components")
    print("=" * 70)
    test_adaptive_routing()
    test_relevance_grader()
    test_self_correcting_rewriter()
    test_web_search()
    print("\n" + "=" * 70)
    print("All Adaptive RAG unit tests completed successfully!")
    print("=" * 70)

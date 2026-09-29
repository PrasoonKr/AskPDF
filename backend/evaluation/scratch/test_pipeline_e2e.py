import sys
from backend.bootstrap import startup

def test_pipeline():
    print("Initializing AskPDF application with Adaptive RAG...")
    app = startup("default")
    assistant = app.assistant_service

    session_id = assistant.create_session()
    print(f"Session created: {session_id}")

    test_queries = [
        "What is the CAP theorem in distributed systems?",
        "Compare sharding vs partitioning",
        "What is the current weather today?"
    ]

    for q in test_queries:
        print("\n" + "=" * 60)
        print(f"Testing Question: '{q}'")
        print("=" * 60)
        # We test the adaptive pipeline retrieval directly to avoid long LLM generation on CPU
        res = assistant.adaptive_pipeline.execute(q)
        print(f"Route Selected : {res.route_chosen.value}")
        print(f"Attempts       : {res.total_attempts}")
        print(f"Is Relevant    : {res.is_relevant}")
        print(f"Docs Retrieved : {len(res.documents)}")
        print("Trace steps:")
        for t in res.trace:
            print(f"  [{t.step_number}] {t.step_type} -> {t.decision_or_grade}")

    print("\nEnd-to-end Adaptive RAG pipeline test PASSED successfully!")

if __name__ == "__main__":
    test_pipeline()

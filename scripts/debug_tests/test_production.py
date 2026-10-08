import os
import asyncio

# Need to set these before bootstrapping
os.environ["RAG_ENVIRONMENT"] = "production"

from backend.bootstrap import startup

async def main():
    app = startup()
    print("\n[Test] Sending query to production pipeline...\n")
    
    # Query something basic to trigger LLM without complex RAG needed
    response = app.assistant_service.ask(
        session_id="test_session",
        question="Say hello in one sentence."
    )
    print("RESPONSE:")
    print(response.answer)

if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.bootstrap import startup
from backend.api.schemas.chat import ChatRequest

# Ragas imports
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision,
)
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings

def run_evaluations():
    print("🚀 Initializing AskPDF Application...")
    app = startup("test_user_evals")
    
    print("📊 Loading Golden Dataset...")
    dataset_path = Path(__file__).parent / "golden_dataset.json"
    with open(dataset_path, "r") as f:
        golden_data = json.load(f)

    # Prepare for Ragas
    data_for_ragas = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }

    print("🤖 Generating answers for golden dataset (This may take a minute)...")
    for item in golden_data:
        q = item["question"]
        print(f"  -> Asking: {q}")
        
        # We need a new session for each to keep them independent
        session_id = app.assistant_service.create_session()
        
        # The assistant_service returns ChatResponse
        response = app.assistant_service.ask(session_id, q)
        
        # Get the retrieved context from the trace or re-run retrieval
        # Wait, the easiest way to get the exact string contexts is from the adaptive pipeline manually
        # or we can just run the pipeline directly instead of full ask() to get context list,
        # but ask() gives the final answer.
        
        # Let's run adaptive pipeline to get the exact contexts used
        adaptive_res = app.assistant_service.adaptive_pipeline.execute(query=q)
        contexts = []
        for d in adaptive_res.documents[:3]:
            text = getattr(getattr(d, "document", d), "text", str(d))
            if isinstance(d, dict) and "text" in d:
                text = d["text"]
            contexts.append(text)
            
        data_for_ragas["question"].append(q)
        data_for_ragas["answer"].append(response.answer)
        data_for_ragas["contexts"].append(contexts)
        data_for_ragas["ground_truth"].append(item["ground_truth"])

    print("✅ Answer generation complete. Preparing Ragas Dataset...")
    hf_dataset = Dataset.from_dict(data_for_ragas)

    print("🧠 Initializing Local LLM Judges for Ragas...")
    # Use our local models for free evals!
    judge_llm = ChatOllama(model="qwen2.5:3b", temperature=0)
    judge_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    print("📈 Running Ragas Evaluation Suite...")
    result = evaluate(
        dataset=hf_dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )

    print("\n" + "="*50)
    print("📊 EVALUATION RESULTS:")
    print("="*50)
    print(result)

    # Save results
    result_df = result.to_pandas()
    result_df.to_csv(Path(__file__).parent / "eval_results.csv", index=False)
    print(f"\n✅ Detailed results saved to backend/evals/eval_results.csv")

if __name__ == "__main__":
    # Workaround for async event loops in scripts
    try:
        run_evaluations()
    except Exception as e:
        print(f"Evaluation Failed: {e}")

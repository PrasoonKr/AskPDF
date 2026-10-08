import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.bootstrap import startup
from backend.llm.client import OllamaClient

def run_evaluations():
    print("🚀 Initializing AskPDF Application...")
    app = startup("default")
    
    print("📊 Loading Golden Dataset...")
    dataset_path = Path(__file__).parent.parent / "evaluation" / "phase2_questions.json"
    with open(dataset_path, "r") as f:
        golden_data = json.load(f)
    print(f"📊 Loaded Golden Dataset (Found {len(golden_data)} questions)...")

    print("🧠 Initializing Local LLM Judge (Ollama qwen2.5:3b)...")
    judge_llm = OllamaClient()

    print("\n" + "="*50)
    print("📈 RUNNING CUSTOM LLM-AS-A-JUDGE EVALUATION SUITE")
    print("="*50)

    total_faithfulness = 0
    total_relevancy = 0

    for idx, item in enumerate(golden_data):
        q = item["question"]
        print(f"\n[Test Case {idx+1}] Question: {q}")
        
        session_id = app.assistant_service.create_session()
        response = app.assistant_service.ask(session_id, q)
        answer = response.answer
        
        print(f"  -> Generated Answer: {answer[:80]}...")

        # 1. Evaluate Relevancy
        rel_prompt = f"""You are an expert evaluator. Score how relevant the generated answer is to the question on a scale of 1 to 5. Output ONLY a single number from 1 to 5.
Question: {q}
Generated Answer: {answer}"""
        
        rel_score_str = judge_llm.generate(prompt=rel_prompt).strip()
        try:
            rel_score = float(rel_score_str)
        except:
            rel_score = 0
            
        print(f"  -> Answer Relevancy Score: {rel_score}/5.0")
        total_relevancy += rel_score

        # 2. Evaluate Faithfulness
        faith_prompt = f"""You are an expert evaluator. Compare the Generated Answer to the Ground Truth. Score how factually consistent the answer is with the Ground Truth on a scale of 1 to 5. Output ONLY a single number from 1 to 5.
Ground Truth: {item.get("expected_answer", item.get("ground_truth", ""))}
Generated Answer: {answer}"""
        
        faith_score_str = judge_llm.generate(prompt=faith_prompt).strip()
        try:
            faith_score = float(faith_score_str)
        except:
            faith_score = 0
            
        print(f"  -> Faithfulness Score:    {faith_score}/5.0")
        total_faithfulness += faith_score

    print("\n" + "="*50)
    print("📊 FINAL AGGREGATE SCORES:")
    print("="*50)
    print(f"Average Answer Relevancy: {total_relevancy / len(golden_data)} / 5.0")
    print(f"Average Faithfulness:     {total_faithfulness / len(golden_data)} / 5.0")
    print("="*50)

if __name__ == "__main__":
    run_evaluations()

import json
import os
import pandas as pd
from datasets import Dataset

# For generating evaluation results
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)

from app.evaluation.runner import runner
from app.core.llm import get_llm
from app.core.embeddings import embedding_service

def run_evaluation(data_path: str, output_csv: str):
    with open(data_path, "r") as f:
        ground_truth_data = json.load(f)

    # Define the Ablation Study Matrix
    configs = [
        {"name": "Base", "kwargs": {"use_routing": False, "use_rbac": False, "use_guardrails": False}},
        {"name": "+Routing", "kwargs": {"use_routing": True, "use_rbac": False, "use_guardrails": False}},
        {"name": "+RBAC", "kwargs": {"use_routing": True, "use_rbac": True, "use_guardrails": False}},
        {"name": "+Guardrails", "kwargs": {"use_routing": True, "use_rbac": True, "use_guardrails": True}},
    ]

    ragas_llm = get_llm()
    ragas_embeddings = embedding_service.get_embeddings()
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness
    ]

    all_results = []

    for cfg in configs:
        print(f"\\n--- Running Ablation Stage: {cfg['name']} ---")
        
        data_dict = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": []
        }
        
        for item in ground_truth_data:
            res = runner.run_query(
                query=item["query"],
                user_role=item["user_role"],
                **cfg["kwargs"]
            )
            
            data_dict["question"].append(item["query"])
            data_dict["answer"].append(res["answer"])
            data_dict["contexts"].append(res["contexts"])
            data_dict["ground_truth"].append(item["ground_truth"])
            
        dataset = Dataset.from_dict(data_dict)
        
        try:
            print(f"Evaluating {len(dataset)} responses...")
            result = evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=ragas_llm,
                embeddings=ragas_embeddings,
            )
            
            # Extract scores from result dictionary safely
            scores = {m.name: result.get(m.name, 0.0) for m in metrics}
        except Exception as e:
            print(f"RAGAs evaluation failed for {cfg['name']}: {e}")
            scores = {m.name: 0.0 for m in metrics}

        scores["Configuration"] = cfg["name"]
        all_results.append(scores)

    # Save outputs
    df = pd.DataFrame(all_results)
    
    # Reorder columns to make 'Configuration' the first column natively
    cols = ["Configuration"] + [c for c in df.columns if c != "Configuration"]
    df = df[cols]
    
    # Ensure directory exists just in case
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    
    print(f"\\n✅ Evaluation complete. Ablation Results saved to {output_csv}")
    print(df.to_markdown(index=False))


if __name__ == "__main__":
    pwd = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.abspath(os.path.join(pwd, "../../data/eval/ground_truth.json"))
    out_file = os.path.abspath(os.path.join(pwd, "../../data/eval/ablation_results.csv"))
        
    print(f"Loading Ground Truth definitions from: {data_file}")
    run_evaluation(data_file, out_file)

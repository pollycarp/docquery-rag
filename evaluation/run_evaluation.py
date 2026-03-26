"""
Evaluation CLI + MLflow Tracking
---------------------------------
Run this script to evaluate the RAG system against the golden dataset
and log the results to MLflow for experiment tracking.

Usage:
    python evaluation/run_evaluation.py
    python evaluation/run_evaluation.py --top-k 3
    python evaluation/run_evaluation.py --no-mlflow   (skip MLflow logging)

MLflow UI:
    After running, launch the UI to see results visually:
    mlflow ui
    Then open http://127.0.0.1:5000 in your browser.
"""

import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.config import settings
from evaluation.evaluator import run_evaluation


def main():
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline")
    parser.add_argument("--top-k",    type=int, default=5, help="Chunks to retrieve per question")
    parser.add_argument("--no-mlflow", action="store_true",  help="Skip MLflow logging")
    args = parser.parse_args()

    print("=" * 60)
    print("RAG EVALUATION")
    print(f"Model:     {settings.ollama_model}")
    print(f"Embedding: {settings.embedding_model}")
    print(f"Top-K:     {args.top_k}")
    print(f"Chunk size:{settings.chunk_size} chars")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        results = run_evaluation(db, top_k=args.top_k, verbose=True)
    finally:
        db.close()

    summary = results["summary"]

    # ── Print summary report ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"  Questions evaluated : {summary['total_questions']}")
    print(f"  Hit Rate @{args.top_k}         : {summary['hit_rate']:.0%}")
    print(f"  MRR                 : {summary['mrr']:.4f}")
    print(f"  Exact Match Rate    : {summary['exact_match_rate']:.0%}")
    print(f"  Citation Rate       : {summary['citation_rate']:.0%}")
    print("=" * 60)

    # ── Save results to JSON ──────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"evaluation/results_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")

    # ── MLflow logging ────────────────────────────────────────────────────────
    if not args.no_mlflow:
        try:
            import mlflow

            mlflow.set_experiment("rag-evaluation")
            with mlflow.start_run(run_name=f"top_k={args.top_k}_{timestamp}"):

                # Log configuration parameters
                mlflow.log_params({
                    "top_k":           args.top_k,
                    "llm_model":       settings.ollama_model,
                    "embedding_model": settings.embedding_model,
                    "chunk_size":      settings.chunk_size,
                    "chunk_overlap":   settings.chunk_overlap,
                })

                # Log evaluation metrics
                mlflow.log_metrics({
                    "hit_rate":         summary["hit_rate"],
                    "mrr":              summary["mrr"],
                    "exact_match_rate": summary["exact_match_rate"],
                    "citation_rate":    summary["citation_rate"],
                })

                # Save the full results JSON as an artifact
                mlflow.log_artifact(output_path)

            print("Results logged to MLflow. Run 'mlflow ui' to view them.")

        except ImportError:
            print("MLflow not installed. Run: pip install mlflow")
        except Exception as e:
            print(f"MLflow logging failed (non-critical): {e}")


if __name__ == "__main__":
    main()

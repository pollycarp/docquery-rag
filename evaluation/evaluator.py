"""
Evaluation Runner
-----------------
Runs every question in the golden dataset through the full RAG pipeline
and computes retrieval + answer metrics for each one.

How it works:
  For each question in golden_dataset.json:
    1. Run retrieval → get top-k chunks
    2. Check if retrieved chunks contain relevant phrases (Hit Rate, MRR)
    3. Run the full QA pipeline → get an answer
    4. Check if the answer contains the expected answer (Exact Match)
    5. Check if a citation is present (Citation Rate)
  Then aggregate into a summary report.
"""

import json
import time
from pathlib import Path
from sqlalchemy.orm import Session
from app.services.retriever import retrieve
from app.services.qa import answer_question
from evaluation.metrics import hit_rate, reciprocal_rank, exact_match, citation_present, compute_summary


def load_golden_dataset(path: str | None = None) -> list[dict]:
    """Load the golden Q&A dataset from JSON."""
    if path is None:
        path = Path(__file__).parent / "golden_dataset.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(db: Session, top_k: int = 5, verbose: bool = True) -> dict:
    """
    Run the full evaluation against the golden dataset.

    Args:
        db:      Database session
        top_k:   Number of chunks to retrieve per question
        verbose: Print progress to console

    Returns:
        A dict with per-question results and an overall summary
    """
    dataset = load_golden_dataset()
    per_question_results = []

    for item in dataset:
        question        = item["question"]
        expected_answer = item["expected_answer"]
        relevant_phrases = item["relevant_phrases"]

        if verbose:
            print(f"\n[Q{item['id']}] {question}")

        # ── Step 1: Retrieval ────────────────────────────────────────────────
        t0 = time.perf_counter()
        chunks = retrieve(question, db, top_k=top_k)
        retrieval_ms = round((time.perf_counter() - t0) * 1000, 1)

        retrieved_contents = [c.content for c in chunks]
        source_filename    = chunks[0].filename if chunks else ""

        hit      = hit_rate(retrieved_contents, relevant_phrases)
        rr       = reciprocal_rank(retrieved_contents, relevant_phrases)

        if verbose:
            print(f"  Retrieval: {'HIT' if hit else 'MISS'} | RR={rr:.2f} | {retrieval_ms}ms")

        # ── Step 2: Answer generation ────────────────────────────────────────
        t0 = time.perf_counter()
        qa_result = answer_question(question, db, top_k=top_k)
        answer_ms = round((time.perf_counter() - t0) * 1000, 1)

        answer = qa_result["answer"]
        em     = exact_match(answer, expected_answer)
        cited  = citation_present(answer, source_filename)

        if verbose:
            print(f"  Answer:    {'MATCH' if em else 'NO MATCH'} | Citation: {'YES' if cited else 'NO'} | {answer_ms}ms")
            print(f"  Generated: {answer[:120]}...")

        per_question_results.append({
            "id":               item["id"],
            "question":         question,
            "expected_answer":  expected_answer,
            "generated_answer": answer,
            "hit":              hit,
            "reciprocal_rank":  rr,
            "exact_match":      em,
            "citation_present": cited,
            "retrieval_ms":     retrieval_ms,
            "answer_ms":        answer_ms,
        })

    summary = compute_summary(per_question_results)

    return {
        "summary":   summary,
        "questions": per_question_results,
    }

"""
Evaluation Metrics
------------------
Functions to measure how well the RAG system is performing.

RETRIEVAL METRICS
-----------------
These measure whether the right chunks were retrieved.

  Hit Rate @k
    "Did at least one of the top-k chunks contain the relevant information?"
    Hit Rate = (questions with a hit) / (total questions)
    A Hit Rate of 1.0 means the retriever always found something relevant.

  MRR — Mean Reciprocal Rank
    "On average, how high up in the ranked list is the first relevant chunk?"
    If the relevant chunk is rank 1 → score = 1/1 = 1.0  (perfect)
    If the relevant chunk is rank 3 → score = 1/3 = 0.33
    If no relevant chunk found    → score = 0.0
    MRR = average of these scores across all questions.

ANSWER METRICS
--------------
These measure whether the generated answer is correct.

  Exact Match Rate
    "Does the answer contain the expected key phrase?"
    Simple but effective for factual questions with known answers.

  Citation Rate
    "Does the answer include a citation (mentions a filename)?"
    Checks our citation prompt is being followed.
"""


def hit_rate(retrieved_contents: list[str], relevant_phrases: list[str]) -> bool:
    """
    Returns True if any retrieved chunk contains at least one relevant phrase.

    Args:
        retrieved_contents: List of chunk text strings (in rank order)
        relevant_phrases:   List of expected phrases from the golden dataset
    """
    combined = " ".join(retrieved_contents).lower()
    return any(phrase.lower() in combined for phrase in relevant_phrases)


def reciprocal_rank(retrieved_contents: list[str], relevant_phrases: list[str]) -> float:
    """
    Returns 1/rank of the first relevant chunk, or 0 if none found.

    Args:
        retrieved_contents: List of chunk text strings (in rank order, best first)
        relevant_phrases:   List of expected phrases from the golden dataset
    """
    for rank, content in enumerate(retrieved_contents, start=1):
        if any(phrase.lower() in content.lower() for phrase in relevant_phrases):
            return 1.0 / rank
    return 0.0


def exact_match(answer: str, expected_answer: str) -> bool:
    """
    Returns True if the expected answer phrase appears in the generated answer.
    Case-insensitive.
    """
    return expected_answer.lower() in answer.lower()


def citation_present(answer: str, filename: str) -> bool:
    """
    Returns True if the answer mentions the source filename,
    indicating a citation was included.
    """
    return filename.lower() in answer.lower()


def compute_summary(results: list[dict]) -> dict:
    """
    Aggregates per-question results into overall metrics.

    Args:
        results: List of per-question result dicts (from evaluator.py)

    Returns:
        Summary dict with averaged metrics
    """
    n = len(results)
    if n == 0:
        return {}

    return {
        "total_questions":   n,
        "hit_rate":          round(sum(r["hit"] for r in results) / n, 4),
        "mrr":               round(sum(r["reciprocal_rank"] for r in results) / n, 4),
        "exact_match_rate":  round(sum(r["exact_match"] for r in results) / n, 4),
        "citation_rate":     round(sum(r["citation_present"] for r in results) / n, 4),
    }

"""
LLM Service (Ollama)
--------------------
Sends a question + retrieved context to a local Ollama model and
returns a cited answer.

How citations work:
  - Each retrieved chunk is labelled [Source 1], [Source 2], etc.
  - The system prompt instructs the model to always cite using
    "According to [filename, page X]..." format.
  - The model sees the chunk labels so it knows which source to cite.
"""

import ollama
from app.services.retriever import RetrievedChunk
from app.config import settings

# System prompt — the instructions we give the LLM before every question
_SYSTEM_PROMPT = """You are a precise document Q&A assistant.

Your job is to answer the user's question using ONLY the context provided below.

Rules you must follow:
1. Always cite your source using this format: "According to [filename, page X]..."
   If there is no page number, use: "According to [filename]..."
2. If the answer spans multiple sources, cite each one.
3. If the context does not contain enough information to answer, respond with:
   "I could not find information about this in the provided documents."
4. Never make up facts. Only use what is in the context.
5. Be concise and direct."""


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    """
    Generate a cited answer for the question using the retrieved chunks.

    Args:
        question: The user's natural language question
        chunks:   The top-k relevant chunks from the retriever

    Returns:
        A string answer with inline citations
    """
    if not chunks:
        return "I could not find any relevant information in the provided documents."

    # Build the context block — each chunk gets a numbered label
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        page_info = f", page {chunk.page_number}" if chunk.page_number else ""
        label = f"[Source {i}: {chunk.filename}{page_info}]"
        context_parts.append(f"{label}\n{chunk.content}")

    context = "\n\n".join(context_parts)

    user_message = f"""Context:
{context}

Question: {question}

Answer with citations:"""

    response = ollama.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        options={"temperature": 0.1},  # low temperature = more factual, less creative
    )

    return response["message"]["content"].strip()

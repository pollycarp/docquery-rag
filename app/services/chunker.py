"""
Text Chunking Service
---------------------
Splits a page of text into smaller, overlapping chunks.

Why chunk?
  LLMs have a limited context window and embedding models work best
  on focused pieces of text. We split long documents into chunks of
  ~512 characters with a small overlap so context isn't lost at boundaries.

Strategy: Recursive Character Splitting
  Try to split on paragraphs (\n\n), then sentences (\n), then words ( ).
  This keeps chunks semantically coherent wherever possible.
"""

from dataclasses import dataclass
from app.services.loader import Page


@dataclass
class Chunk:
    """A single piece of text ready to be embedded and stored."""
    content: str
    chunk_index: int       # 0-based position within the document
    page_number: int | None
    source: str


def chunk_pages(pages: list[Page], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """
    Takes all pages of a document and returns a flat list of Chunk objects.

    Args:
        pages:         List of pages returned by the loader
        chunk_size:    Max characters per chunk (default 512 in config)
        chunk_overlap: How many characters to repeat between chunks (default 64)
    """
    all_chunks: list[Chunk] = []
    chunk_index = 0

    for page in pages:
        text_chunks = _split_text(page["text"], chunk_size, chunk_overlap)

        for text in text_chunks:
            if text.strip():  # ignore empty chunks
                all_chunks.append(Chunk(
                    content=text.strip(),
                    chunk_index=chunk_index,
                    page_number=page["page_number"],
                    source=page["source"],
                ))
                chunk_index += 1

    return all_chunks


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Recursively split text using these separators in order:
      1. Double newline (paragraph break)
      2. Single newline (line break)
      3. Space (word boundary)
      4. Character (last resort)
    """
    separators = ["\n\n", "\n", " ", ""]
    return _recursive_split(text, separators, chunk_size, chunk_overlap)


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Core recursive splitting logic."""

    # If the text already fits in one chunk, we're done
    if len(text) <= chunk_size:
        return [text]

    separator = separators[0]
    remaining_separators = separators[1:]

    # Split the text using the current separator
    splits = text.split(separator) if separator else list(text)

    chunks: list[str] = []
    current_chunk = ""

    for split in splits:
        piece = split + separator  # re-attach the separator we removed

        if len(current_chunk) + len(piece) <= chunk_size:
            # Piece fits — keep building the current chunk
            current_chunk += piece
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip(separator))

            if len(piece) > chunk_size and remaining_separators:
                # Piece is too big even on its own — recurse with next separator
                sub_chunks = _recursive_split(
                    piece, remaining_separators, chunk_size, chunk_overlap
                )
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                # Start a new chunk with overlap from the previous one
                overlap_text = current_chunk[-chunk_overlap:] if current_chunk else ""
                current_chunk = overlap_text + piece

    if current_chunk:
        chunks.append(current_chunk.rstrip(separator))

    return chunks

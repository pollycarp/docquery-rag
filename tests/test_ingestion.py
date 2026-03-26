"""
Phase 1 Tests — Ingestion Pipeline (no database or API calls required)
"""

import pytest
from app.services.chunker import chunk_pages, _split_text
from app.services.loader import _load_txt
import tempfile, os, pathlib


# ── Chunker Tests ─────────────────────────────────────────────────────────────

def test_split_text_short_text_is_not_split():
    """Text shorter than chunk_size should come back as a single chunk."""
    text = "Hello world"
    result = _split_text(text, chunk_size=100, chunk_overlap=10)
    assert len(result) == 1
    assert result[0] == "Hello world"


def test_split_text_long_text_is_split():
    """Text longer than chunk_size should be split into multiple chunks."""
    text = "word " * 200  # 1000 characters
    result = _split_text(text, chunk_size=100, chunk_overlap=10)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 110  # small tolerance for overlap


def test_chunk_pages_returns_correct_count():
    """chunk_pages should produce at least one chunk per non-empty page."""
    pages = [
        {"text": "Short text.", "page_number": 1, "source": "test.txt"},
        {"text": "Another short text.", "page_number": 2, "source": "test.txt"},
    ]
    chunks = chunk_pages(pages, chunk_size=512, chunk_overlap=64)
    assert len(chunks) >= 2


def test_chunk_index_is_sequential():
    """chunk_index values should be 0, 1, 2, ... across all pages."""
    pages = [{"text": "word " * 300, "page_number": 1, "source": "test.txt"}]
    chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=10)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_preserves_page_number():
    """Each chunk should carry the page_number of its source page."""
    pages = [{"text": "Some text here.", "page_number": 5, "source": "test.pdf"}]
    chunks = chunk_pages(pages, chunk_size=512, chunk_overlap=64)
    assert all(c.page_number == 5 for c in chunks)


# ── Loader Tests ──────────────────────────────────────────────────────────────

def test_load_txt_returns_content():
    """TXT loader should return the file content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello from a test file.")
        tmp_path = f.name

    try:
        pages = _load_txt(pathlib.Path(tmp_path))
        assert len(pages) == 1
        assert "Hello from a test file." in pages[0]["text"]
    finally:
        os.unlink(tmp_path)


def test_load_txt_page_number_is_none():
    """TXT files don't have page numbers — should be None."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Some content")
        tmp_path = f.name

    try:
        pages = _load_txt(pathlib.Path(tmp_path))
        assert pages[0]["page_number"] is None
    finally:
        os.unlink(tmp_path)

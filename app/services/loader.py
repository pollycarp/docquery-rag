"""
Document Loader Service
-----------------------
Reads a file from disk and returns a list of pages.
Each page is a dict with:
  - "text":        the raw text content
  - "page_number": 1-based page number (None for TXT files)
  - "source":      original filename

Supports: PDF, DOCX, TXT
"""

import pathlib
from typing import TypedDict


class Page(TypedDict):
    text: str
    page_number: int | None
    source: str


def load_document(file_path: str) -> list[Page]:
    """
    Load a document from disk. Returns a list of pages.
    Raises ValueError if the file type is not supported.
    """
    path = pathlib.Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(path)
    elif suffix == ".docx":
        return _load_docx(path)
    elif suffix == ".txt":
        return _load_txt(path)
    else:
        raise ValueError(f"Unsupported file type: '{suffix}'. Use .pdf, .docx, or .txt")


def _load_pdf(path: pathlib.Path) -> list[Page]:
    """Extract text page-by-page from a PDF."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[Page] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:  # skip blank pages
            pages.append({
                "text": text,
                "page_number": i + 1,  # 1-based
                "source": path.name,
            })

    return pages


def _load_docx(path: pathlib.Path) -> list[Page]:
    """
    Extract text from a Word document.
    DOCX files don't have strict page numbers, so we treat
    each paragraph group as a logical 'page'.
    """
    from docx import Document

    doc = Document(str(path))
    full_text = "\n".join(
        para.text for para in doc.paragraphs if para.text.strip()
    )

    return [{
        "text": full_text,
        "page_number": None,
        "source": path.name,
    }]


def _load_txt(path: pathlib.Path) -> list[Page]:
    """Load a plain text file as a single page."""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()

    return [{
        "text": text,
        "page_number": None,
        "source": path.name,
    }]

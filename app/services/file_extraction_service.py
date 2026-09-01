"""
Extracts raw text from an uploaded CDC file (PDF, DOCX, or plain text) so it
can be handed to the CDCAnalyzerAgent as a single string. This is a pure I/O
concern kept separate from the agent itself.
"""

from __future__ import annotations

import io
from typing import Optional

from fastapi import UploadFile
from pypdf import PdfReader
from docx import Document


class UnsupportedFileTypeError(Exception):
    pass


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages_text).strip()


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs).strip()


def _extract_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()


async def extract_text_from_upload(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".pdf"):
        text = _extract_pdf(content)
    elif filename.endswith(".docx"):
        text = _extract_docx(content)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        text = _extract_txt(content)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type for '{file.filename}'. Use .pdf, .docx, .txt or .md"
        )

    if not text:
        raise ValueError(f"No extractable text found in '{file.filename}'")

    return text

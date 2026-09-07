import pdfplumber
from docx import Document as DocxDocument
from pathlib import Path


class FileParser:
    def parse(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return self._parse_docx(file_path)
        else:
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")

    def _parse_pdf(self, path: str) -> str:
        with pdfplumber.open(path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages)

    def _parse_docx(self, path: str) -> str:
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
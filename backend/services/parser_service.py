from __future__ import annotations

import re
from pathlib import Path

import pdfplumber
from docx import Document


class ParserService:
    _section_pattern = re.compile(
        r"(?im)^(?P<label>(?:статья|пункт|подпункт)\s+\d+(?:\.\d+)*\.?|(?:\d+(?:\.\d+)*\.))\s*(?P<title>[^\n]*)$"
    )

    def parse_document(self, file_path: str | Path) -> list[dict[str, str]]:
        path = Path(file_path)
        text = self.extract_text(path)
        return self.split_into_sections(text)

    def extract_text(self, file_path: str | Path) -> str:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf_text(path)
        if suffix == ".docx":
            return self._extract_docx_text(path)
        raise ValueError(f"Unsupported document format: {suffix}")

    def split_into_sections(self, text: str) -> list[dict[str, str]]:
        normalized = self._normalize_text(text)
        matches = list(self._section_pattern.finditer(normalized))
        if not matches:
            paragraphs = [chunk.strip() for chunk in normalized.split("\n\n") if chunk.strip()]
            return [
                {
                    "article": f"section_{index + 1}",
                    "title": "",
                    "text": paragraph,
                }
                for index, paragraph in enumerate(paragraphs)
            ]

        sections: list[dict[str, str]] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
            body = normalized[start:end].strip()
            label = self._normalize_label(match.group("label"))
            title = match.group("title").strip()
            full_text = "\n".join(part for part in [title, body] if part).strip()
            sections.append(
                {
                    "article": label,
                    "title": title,
                    "text": full_text,
                }
            )
        return [section for section in sections if section["text"]]

    def _extract_pdf_text(self, path: Path) -> str:
        chunks: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)

    def _extract_docx_text(self, path: Path) -> str:
        document = Document(path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(paragraphs)

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _normalize_label(self, label: str) -> str:
        return re.sub(r"\s+", " ", label.strip().rstrip("."))

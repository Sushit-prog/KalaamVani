"""NCERT PDF extraction using pdfplumber."""

import re
from pathlib import Path

import pdfplumber

_CHAPTER_TITLES = [
    "Constitution: Why and How?",
    "Rights of the Citizen",
    "Election and Representation",
    "Executive",
    "Legislature",
    "Judiciary",
    "Federal System",
    "Local Government",
    "Constitution as a Living Document",
]

_CHAPTER_PATTERNS = [
    re.compile(rf"^{re.escape(t)}", re.IGNORECASE) for t in _CHAPTER_TITLES
]
_CHAPTER_NUMBER_RE = re.compile(r"^chapter\s+(\d+)", re.IGNORECASE)

_CONSTITUTIONAL_TERMS = [
    "fundamental rights",
    "directive principles",
    "parliament",
    "supreme court",
    "high court",
    "president",
    "governor",
    "prime minister",
    "council of ministers",
    "federalism",
    "amendment",
    "election",
    "judiciary",
    "legislature",
    "executive",
    "panchayat",
    "municipality",
    "secularism",
    "democracy",
    "sovereignty",
    "dignity",
    "equality",
    "liberty",
    "fraternity",
    "justice",
    "republic",
]


def detect_chapter(text: str) -> str | None:
    """Detect if text starts a new chapter."""
    lines = text.strip().split("\n")[:5]
    for line in lines:
        line = line.strip()
        for title, pattern in zip(_CHAPTER_TITLES, _CHAPTER_PATTERNS):
            if pattern.search(line):
                return title
        match = _CHAPTER_NUMBER_RE.match(line)
        if match:
            num = int(match.group(1))
            if 1 <= num <= len(_CHAPTER_TITLES):
                return _CHAPTER_TITLES[num - 1]
    return None


def extract_keywords(text: str, max_keywords: int = 6) -> list[str]:
    """Extract relevant keywords from text."""
    text_lower = text.lower()
    found = []
    for term in _CONSTITUTIONAL_TERMS:
        if term in text_lower and term not in found:
            found.append(term)
        if len(found) >= max_keywords:
            break
    return found


def process_ncert(pdf_path: Path) -> list[dict]:
    """Extract text from PDF, detect chapters, chunk by page runs."""
    chunks = []
    current_chapter = "Introduction"
    page_buffer = []
    page_start = 0
    buffer_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF has {total_pages} pages")

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = text.strip()

            if not text:
                continue

            chapter = detect_chapter(text)
            if chapter:
                if buffer_text.strip():
                    chunks.append(
                        {
                            "source_type": "ncert",
                            "chapter": current_chapter,
                            "text": buffer_text.strip(),
                            "page_start": page_start,
                            "page_end": i,
                            "keywords": extract_keywords(buffer_text),
                        }
                    )
                current_chapter = chapter
                buffer_text = text
                page_start = i
            else:
                buffer_text += "\n\n" + text

            if len(buffer_text) > 8000:
                chunks.append(
                    {
                        "source_type": "ncert",
                        "chapter": current_chapter,
                        "text": buffer_text.strip(),
                        "page_start": page_start,
                        "page_end": i + 1,
                        "keywords": extract_keywords(buffer_text),
                    }
                )
                buffer_text = ""
                page_start = i + 1

        if buffer_text.strip():
            chunks.append(
                {
                    "source_type": "ncert",
                    "chapter": current_chapter,
                    "text": buffer_text.strip(),
                    "page_start": page_start,
                    "page_end": total_pages,
                    "keywords": extract_keywords(buffer_text),
                }
            )

    return chunks

"""Corpus-grounded tools for the KalamVani tutoring agent.

All tools retrieve from the built ChromaDB + BM25 hybrid index. The
generate_mcq tool only ever grounds its correct answers on chunks whose
provenance is "fetched_from_wikisource" — curated_not_verified chunks are
NEVER eligible as source_chunk_id for a correct answer.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from src.rag.embeddings import EmbeddingModel
from src.rag.index import PolityIndex
from src.rag.retrieve import HybridRetriever

# Only these chunks may be used as ground truth for MCQ correct answers.
GROUND_TRUTH_PROVENANCE = "fetched_from_wikisource"


def _load_chunks() -> list[dict]:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "data"
        / "processed"
        / "chunks.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _get_retriever() -> HybridRetriever:
    chunks = _load_chunks()
    embedder = EmbeddingModel()
    index = PolityIndex()
    return HybridRetriever(index, chunks, embedder)


def _format_source(chunk: dict) -> str:
    source = chunk.get("source", "")
    provenance = chunk.get("provenance", "unknown")
    return f"[{source} | provenance: {provenance}]"


RETRIEVER = None


def get_retriever() -> HybridRetriever:
    global RETRIEVER
    if RETRIEVER is None:
        RETRIEVER = _get_retriever()
    return RETRIEVER


@tool
def query_constitution(question: str) -> list[dict]:
    """Retrieve relevant corpus chunks for a constitutional question.

    Use this when you need grounded source material to answer a student's
    question about the Indian Constitution. Returns up to 3 most relevant
    chunks (article text, NCERT, or PYQ model answers) with their sources.
    """
    retriever = get_retriever()
    results = retriever.retrieve(question, top_k=3)
    out = []
    for r in results:
        out.append(
            {
                "chunk_id": r["chunk_id"],
                "source": _format_source(r),
                "provenance": r.get("provenance", "unknown"),
                "text": r["text"][:1200],
            }
        )
    return out


@tool
def explain_concept(concept: str) -> dict:
    """Explain a constitutional concept using grounded corpus material.

    Retrieves chunks related to the concept and returns them along with the
    source(s) they were drawn from. Use this when a student asks 'what is X'
    or 'explain Y'.
    """
    retriever = get_retriever()
    results = retriever.retrieve(concept, top_k=3)
    return {
        "concept": concept,
        "sources": [_format_source(r) for r in results],
        "passages": [r["text"][:1500] for r in results],
    }


@tool
def get_article_detail(article_number: str) -> Optional[dict]:
    """Return the full detail for a specific Constitution article.

    Fetch the complete retrieved text for a specific article (e.g. "14", "21",
    "51A", "368"). Returns None if the article is not present in the corpus.
    """
    chunks = _load_chunks()
    matches = [
        c
        for c in chunks
        if c.get("source_type") == "article"
        and c["article_numbers"] == [article_number]
    ]
    if not matches:
        return None
    matches.sort(key=lambda c: c["chunk_id"])
    return {
        "article_number": article_number,
        "source": _format_source(matches[0]),
        "provenance": matches[0].get("provenance", "unknown"),
        "parts": [{"chunk_id": c["chunk_id"], "text": c["text"]} for c in matches],
    }


@tool
def generate_mcq(topic: str) -> dict:
    """Generate a multiple-choice question grounded on verified corpus text.

    Produces a question with 4 options and the correct answer index. The
    correct answer is ALWAYS grounded on a chunk whose provenance is
    'fetched_from_wikisource' — curated (non-verified) chunks are never used
    as the basis for a correct answer.
    """
    retriever = get_retriever()
    results = retriever.retrieve(topic, top_k=12)

    # Hard filter: eligible chunks must be fetched_from_wikisource.
    eligible = [r for r in results if r.get("provenance") == GROUND_TRUTH_PROVENANCE]
    if not eligible:
        return {
            "error": (
                f"No verified (fetched_from_wikisource) chunks found for topic "
                f"'{topic}'. MCQs can only be grounded on verified source text."
            )
        }

    seed = eligible[0]["text"]
    # Build distractors from other candidate passages (kept short).
    distractors = [
        r["text"][:300] for r in results if r["chunk_id"] != eligible[0]["chunk_id"]
    ][:3]
    while len(distractors) < 3:
        distractors.append("None of the above.")
    distractors = distractors[:3]

    options = [seed[:300], *distractors]
    correct_index = 0
    random.shuffle(options)
    correct_index = options.index(seed[:300])

    return {
        "topic": topic,
        "source_chunk_id": eligible[0]["chunk_id"],
        "source_provenance": GROUND_TRUTH_PROVENANCE,
        "question": f"Which of the following best describes {topic}?",
        "options": options,
        "correct_answer_index": correct_index,
        "explanation_source": _format_source(eligible[0]),
    }


def tool_registry() -> list:
    return [query_constitution, explain_concept, get_article_detail, generate_mcq]

"""Semantic chunking pipeline with chunk ID assignment."""

import json
import re
from collections import defaultdict
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

ARTICLE_PATTERN = re.compile(r"^art[\d]+[A-Z]?(_[\d]+[A-Z]?)*_chunk_\d{3}$")
NCERT_PATTERN = re.compile(r"^ncert_ch\d+_chunk_\d{3}$")
PYQ_PATTERN = re.compile(r"^pyq_\d{4}_\d{3}$")

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 500


def split_semantic(text: str) -> list[str]:
    """Split text into semantic chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\nArticle ", "\n\n## ", "\n\n### ", "\n\n", "\n", ". ", " "],
    )
    return splitter.split_text(text)


def estimate_chapter_number(chapter: str) -> int:
    """Map chapter title to a chapter number."""
    known = {
        "Constitution: Why and How?": 1,
        "Rights of the Citizen": 2,
        "Election and Representation": 3,
        "Executive": 4,
        "Legislature": 5,
        "Judiciary": 6,
        "Federal System": 7,
        "Local Government": 8,
        "Constitution as a Living Document": 9,
        "Introduction": 0,
    }
    return known.get(chapter, 99)


def assign_chunk_ids(chunks: list[dict]) -> list[dict]:
    """Assign deterministic chunk IDs based on source type and grouping key."""
    groups: dict[str, list[dict]] = defaultdict(list)

    for chunk in chunks:
        stype = chunk["source_type"]
        if stype == "article":
            key = "art_" + "_".join(chunk.get("article_numbers", ["0"]))
        elif stype == "ncert":
            ch_num = chunk.get("chapter_number", 99)
            key = f"ncert_ch{ch_num}"
        elif stype == "pyq":
            key = f"pyq_{chunk.get('year', 0)}"
        else:
            key = "misc"
        chunk["_group_key"] = key
        groups[key].append(chunk)

    result = []
    for key, group_chunks in sorted(groups.items()):
        for i, chunk in enumerate(group_chunks):
            seq = f"{i + 1:03d}"
            del chunk["_group_key"]
            if chunk["source_type"] == "article":
                art_tag = "_".join(chunk.get("article_numbers", ["0"]))
                chunk["chunk_id"] = f"art{art_tag}_chunk_{seq}"
            elif chunk["source_type"] == "ncert":
                ch_num = chunk.get("chapter_number", 99)
                chunk["chunk_id"] = f"ncert_ch{ch_num}_chunk_{seq}"
            elif chunk["source_type"] == "pyq":
                chunk["chunk_id"] = f"pyq_{chunk.get('year', 0)}_{seq}"
            else:
                chunk["chunk_id"] = f"misc_{seq}"
            result.append(chunk)
    return result


def validate_chunk_ids(chunks: list[dict]) -> None:
    """Validate unique and correctly formatted chunk IDs."""
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), (
        f"Duplicate chunk_ids found: {len(ids)} total, {len(set(ids))} unique"
    )
    for cid in ids:
        valid = (
            ARTICLE_PATTERN.match(cid)
            or NCERT_PATTERN.match(cid)
            or PYQ_PATTERN.match(cid)
        )
        if not valid:
            raise ValueError(f"Invalid chunk_id format: {cid}")


def process_all_sources(
    ncert_path: Path,
    articles_path: Path,
    pyqs_path: Path,
    output_dir: Path,
) -> list[dict]:
    """Process all sources, chunk, assign IDs, output chunks.json."""
    output_dir.mkdir(parents=True, exist_ok=True)

    from src.rag.extract_ncert_chunks import process_ncert

    chunks: list[dict] = []
    ncert_raw = process_ncert(ncert_path)
    for nc in ncert_raw:
        # Derive a topic from the chapter title for consistent metadata
        topic = nc.get("chapter", "Introduction").replace("Chapter", "").strip()
        nc_texts = split_semantic(nc["text"])
        for nct in nc_texts:
            chunks.append(
                {
                    "source_type": "ncert",
                    "chapter": nc.get("chapter", "Introduction"),
                    "chapter_number": None,
                    "topic": topic,
                    "source": f"NCERT Class XI - {nc.get('chapter', 'Introduction')}",
                    "text": nct,
                    "page_start": nc.get("page_start"),
                    "page_end": nc.get("page_end"),
                    "keywords": nc.get("keywords", []),
                }
            )

    articles = json.loads(articles_path.read_text(encoding="utf-8"))
    for article in articles:
        article_texts = split_semantic(article["text"])
        provenance = article.get("provenance", "curated_not_verified")
        for text in article_texts:
            meta = {
                "source_type": "article",
                "article_numbers": [article["article_number"]],
                "topic": article["subject"],
                "subtopic": article.get("title", ""),
                "keywords": article["keywords"],
                "chapter_number": None,
                "text": text,
                "source": f"Constitution Art. {article['article_number']}",
                "provenance": provenance,
            }
            if provenance == "fetched_from_wikisource":
                meta["current_as_of"] = article.get("current_as_of")
                meta["amendment_cutoff"] = article.get("amendment_cutoff")
            chunks.append(meta)

    pyqs = json.loads(pyqs_path.read_text(encoding="utf-8"))
    for q in pyqs:
        if not q.get("model_answer"):
            continue
        chunks.append(
            {
                "source_type": "pyq",
                "year": q["year"],
                "topic": q.get("topic", ""),
                "subtopic": "",
                "keywords": [
                    c["keyword"] for c in (q.get("must_mention_concepts") or [])
                ],
                "chapter_number": None,
                "text": f"Q: {q['question_text']}\n\nA: {q['model_answer']}",
                "source": f"UPSC Mains {q['year']} ({q['question_id']})",
            }
        )

    for chunk in chunks:
        if chunk["source_type"] == "ncert":
            chunk["chapter_number"] = estimate_chapter_number(
                chunk.get("chapter", "Introduction")
            )

    chunks = assign_chunk_ids(chunks)
    validate_chunk_ids(chunks)

    output_path = output_dir / "chunks.json"
    output_path.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(chunks)} chunks to {output_path}")
    return chunks


if __name__ == "__main__":
    process_all_sources(
        ncert_path=Path("data/raw/ncert_class_xi_polity.pdf"),
        articles_path=Path("data/processed/articles.json"),
        pyqs_path=Path("data/processed/pyqs.json"),
        output_dir=Path("data/processed"),
    )

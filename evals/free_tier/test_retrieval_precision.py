"""Retrieval precision tests for Indian Polity RAG."""

import json
from pathlib import Path

import pytest

FIXTURES = Path("evals/fixtures")
TOP_K = 3


@pytest.fixture(scope="module")
def retriever():
    """Load the built retriever. Requires prior index build."""
    from src.rag.index import PolityIndex
    from src.rag.retrieve import HybridRetriever
    from src.rag.embeddings import EmbeddingModel

    chunks = json.loads(Path("data/processed/chunks.json").read_text(encoding="utf-8"))
    embedder = EmbeddingModel()
    index = PolityIndex()
    return HybridRetriever(index, chunks, embedder)


@pytest.fixture(scope="module")
def gold_set():
    return json.loads((FIXTURES / "retrieval_gold.json").read_text(encoding="utf-8"))


def test_hits_at_3(retriever, gold_set):
    hits = 0
    for entry in gold_set:
        results = retriever.retrieve(entry["query"], top_k=TOP_K)
        chunk_ids = [r["chunk_id"] for r in results]
        if entry["expected_chunk_id"] in chunk_ids:
            hits += 1
    hits_at_3 = hits / len(gold_set)
    assert hits_at_3 >= 0.8, (
        f"Hits@3 too low: {hits}/{len(gold_set)} = {hits_at_3:.0%} (threshold: 80%)"
    )


def test_mrr_at_3(retriever, gold_set):
    rr_sum = 0
    for entry in gold_set:
        results = retriever.retrieve(entry["query"], top_k=TOP_K)
        chunk_ids = [r["chunk_id"] for r in results]
        if entry["expected_chunk_id"] in chunk_ids:
            rank = chunk_ids.index(entry["expected_chunk_id"]) + 1
            rr_sum += 1.0 / rank
    mrr = rr_sum / len(gold_set)
    assert mrr >= 0.7, f"MRR@3 too low: {mrr:.2f} (threshold: 0.70)"


def test_retrieval_metadata_completeness(retriever, gold_set):
    required = {"chunk_id", "source", "topic", "keywords", "text"}
    for entry in gold_set:
        results = retriever.retrieve(entry["query"], top_k=TOP_K)
        for r in results:
            missing = required - set(r.keys())
            assert not missing, f"Missing fields: {missing}"


def test_gold_ids_resolve(retriever, gold_set):
    """Every expected_chunk_id must exist in the retriever's chunk map."""
    for entry in gold_set:
        assert entry["expected_chunk_id"] in retriever.chunk_map, (
            f"Gold chunk_id '{entry['expected_chunk_id']}' not in index"
        )

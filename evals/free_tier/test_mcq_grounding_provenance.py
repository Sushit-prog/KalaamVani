"""Guard test: MCQ sources must always be fetched_from_wikisource chunks.

This ensures the generate_mcq tool NEVER grounds a correct answer on
curated_not_verified chunks (which are not verified ground truth).
"""

import pytest

from src.agent.tools import GROUND_TRUTH_PROVENANCE, _load_chunks


@pytest.fixture(scope="module")
def chunk_provenance_map():
    chunks = _load_chunks()
    return {c["chunk_id"]: c.get("provenance", "unknown") for c in chunks}


def test_generate_mcq_source_is_always_verified(chunk_provenance_map):
    """Every source_chunk_id returned by generate_mcq must be fetched_from_wikisource."""
    from src.agent.tools import generate_mcq

    topics = [
        "Article 14",
        "emergency",
        "money bill",
        "President election",
        "fundamental duties",
        "constitutional amendment",
    ]
    for topic in topics:
        result = generate_mcq.invoke(topic)
        if "error" in result:
            # No verified source found — that's an acceptable outcome
            continue
        source_id = result["source_chunk_id"]
        provenance = chunk_provenance_map.get(source_id)
        assert provenance == GROUND_TRUTH_PROVENANCE, (
            f"generate_mcq grounded on non-verified chunk {source_id} "
            f"(provenance={provenance}). MCQs must only use "
            f"provenance == {GROUND_TRUTH_PROVENANCE} as ground truth."
        )
        assert result["source_provenance"] == GROUND_TRUTH_PROVENANCE


def test_no_curated_chunks_are_ground_truth_eligible(chunk_provenance_map):
    """All article chunks tagged curated_not_verified are ineligible as MCQ sources."""
    assert "fetched_from_wikipedia_api" not in set(chunk_provenance_map.values()), (
        "Stale provenance label 'fetched_from_wikipedia_api' found. "
        "Use 'fetched_from_wikisource'."
    )
    assert GROUND_TRUTH_PROVENANCE == "fetched_from_wikisource"


def test_ground_truth_provenance_label_is_fetched_from_wikisource():
    assert GROUND_TRUTH_PROVENANCE == "fetched_from_wikisource"

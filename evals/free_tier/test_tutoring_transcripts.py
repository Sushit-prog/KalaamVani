"""Automated transcript evals for the KalamVani Socratic tutor.

These tests exercise the tutoring graph against curated student transcripts and
assert that the tutor stays grounded and Socratic. They are OPT-IN: they are
skipped unless GEMINI_API_KEY is set, to avoid burning API credits during
default CI/test runs.

To enable:
    set GEMINI_API_KEY=...
    python -m pytest evals/free_tier/test_tutoring_transcripts.py -v
"""

import os

import pytest

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


@pytest.fixture(scope="module")
def app():
    from src.agent.graph import get_app

    return get_app()


@pytest.fixture(scope="module")
def transcript_cases():
    """(name, student_prompt, expected_terms) tuples for grounding checks."""
    return [
        (
            "equality_art14",
            "What does Article 14 say about equality before the law?",
            ["equal protection", "person"],
        ),
        (
            "president_election",
            "How is the President of India elected?",
            ["proportional representation", "electoral", "vote"],
        ),
        (
            "emergency_conditions",
            "Under what conditions can an emergency be proclaimed?",
            ["war", "external aggression", "armed rebellion"],
        ),
        (
            "fundamental_duties",
            "What are the fundamental duties of citizens?",
            ["duty", "citizen", "Constitution"],
        ),
    ]


def _content_text(msg) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return " ".join(parts)


@pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not set (opt-in)")
def test_transcript_grounding(app, transcript_cases):
    """Tutor responses must reference grounded constitutional terms."""
    from langchain_core.messages import AIMessage, HumanMessage

    for name, prompt, expected_terms in transcript_cases:
        state = {"messages": [HumanMessage(content=prompt)]}
        final = app.invoke(state)
        msgs = final.get("messages", [])
        ai_text = " ".join(
            _content_text(m) for m in msgs if isinstance(m, AIMessage) and m.content
        ).lower()
        assert ai_text, f"Agent produced no text for '{name}'"
        # Confirm at least one grounded key term appears.
        found = [t for t in expected_terms if t in ai_text]
        assert found, (
            f"Transcript '{name}' had no expected grounding term in agent "
            f"reply: {expected_terms}"
        )


@pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not set (opt-in)")
def test_tutor_is_socratic(app, transcript_cases):
    """The tutor should guide with questions rather than just dump answers."""
    from langchain_core.messages import AIMessage

    socratic_markers = [
        "what do you think",
        "what about",
        "consider",
        "why",
        "how would you",
        "think about",
        "can you tell me",
    ]
    combined = []
    for _, prompt, _ in transcript_cases:
        state = {"messages": [AIMessage(content=f"The student asks: {prompt}")]}
        final = app.invoke(state)
        for m in final.get("messages", []):
            if isinstance(m, AIMessage):
                combined.append(_content_text(m).lower())
    joined = " ".join(combined)
    matched = [m for m in socratic_markers if m in joined]
    # We look for at least one Socratic marker across the session (lenient,
    # because per-turn behaviour varies); the assertion documents intent.
    assert matched, (
        "No Socratic guiding language detected across transcripts. "
        "Ensure the system prompt encourages questioning."
    )

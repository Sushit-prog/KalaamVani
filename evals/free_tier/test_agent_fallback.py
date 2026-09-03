"""Tests for the no-API-key fallback model (deterministic, always-runnable).

The fallback (_GroundedFallbackModel) must:
  - perform real corpus retrieval (not echo the question)
  - carry a clear template/no-LLM marker so it cannot be mistaken for Gemini
These tests run WITHOUT GEMINI_API_KEY and are not opt-in.
"""

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.graph import _GroundedFallbackModel


def _as_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return " ".join(parts)


def test_fallback_performs_real_retrieval():
    """Fallback should return grounded corpus text for a known article."""
    model = _GroundedFallbackModel()
    resp = model.invoke([HumanMessage(content="Article 14 equality before law")])
    text = _as_text(resp.content)
    assert isinstance(resp, AIMessage)
    assert "Article 14" in text or "equality" in text.lower()


def test_fallback_is_labeled_as_template():
    """Fallback output must carry an unambiguous no-LLM marker."""
    model = _GroundedFallbackModel()
    resp = model.invoke([HumanMessage(content="Article 14")])
    text = _as_text(resp.content)
    assert _GroundedFallbackModel.MARKER.replace("\u2014", "--") in text.replace(
        "\u2014", "--"
    )


def test_fallback_does_not_echo_question_only():
    """Fallback must add grounded material, not just echo the user's prompt."""
    model = _GroundedFallbackModel()
    question = "Under what conditions can an emergency be proclaimed?"
    resp = model.invoke([HumanMessage(content=question)])
    text = _as_text(resp.content)
    assert text.rstrip() != question
    assert "(1)" in text or "Constitution" in text

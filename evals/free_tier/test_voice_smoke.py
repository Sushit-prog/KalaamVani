"""Smoke tests for the voice module (STT / TTS).

Every test explicitly removes SARVAM_API_KEY from the environment so that
no real paid API call can ever be triggered by accident when running locally
with a key set.
"""

from __future__ import annotations

import pytest

from src.voice.errors import VoiceServiceError


# ---------------------------------------------------------------------------
# Fixture: guarantee no SARVAM_API_KEY in the process environment
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _no_sarvam_key(monkeypatch):
    """Strip SARVAM_API_KEY (and GEMINI_API_KEY) for every test in this module."""
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_voice_available_false_without_key():
    """voice_available() must return False when no key is set."""
    from src.voice.stt import voice_available

    assert voice_available() is False


def test_stt_raises_without_key():
    """speech_to_text must raise VoiceServiceError, not hit the network."""
    from src.voice.stt import speech_to_text

    with pytest.raises(VoiceServiceError, match="SARVAM_API_KEY"):
        speech_to_text(b"fake-audio-bytes")


def test_tts_raises_without_key():
    """text_to_speech must raise VoiceServiceError, not hit the network."""
    from src.voice.tts import text_to_speech

    with pytest.raises(VoiceServiceError, match="SARVAM_API_KEY"):
        text_to_speech("Hello, this is a test.")


def test_create_app_returns_gradio_blocks():
    """create_app() must return a gradio Blocks instance without errors."""
    gr = pytest.importorskip("gradio")
    from ui.app import create_app

    app = create_app()
    assert isinstance(app, gr.Blocks)

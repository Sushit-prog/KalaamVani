"""Text-to-speech via Sarvam AI (bulbul:v3).

Converts text to spoken WAV audio using the Sarvam text-to-speech REST API.
Requires the SARVAM_API_KEY environment variable.
"""

from __future__ import annotations

import base64
import os
import re

import httpx

from src.voice.errors import VoiceServiceError

_SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
_TTS_CHAR_LIMIT = 2400  # bulbul:v3 max is 2500; leave headroom


def text_to_speech(
    text: str,
    language_code: str = "en-IN",
    speaker: str = "shubh",
) -> bytes:
    """Convert text to WAV audio bytes using Sarvam AI.

    Parameters
    ----------
    text:
        The text to synthesize.  Longer texts are truncated at sentence
        boundaries to stay within the bulbul:v3 character limit.
    language_code:
        BCP-47 language code.  ``"en-IN"`` for English (default).
    speaker:
        Voice speaker name.  ``"shubh"`` is the bulbul:v3 default.

    Returns
    -------
    bytes
        WAV audio data.

    Raises
    ------
    VoiceServiceError
        If the API key is missing, the request fails, or the response
        cannot be parsed.
    """
    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key or not api_key.strip():
        raise VoiceServiceError(
            "SARVAM_API_KEY is not set.  "
            "Get a key at https://www.sarvam.ai/ and export it."
        )

    truncated = _truncate_to_limit(text, _TTS_CHAR_LIMIT)

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                _SARVAM_TTS_URL,
                headers={
                    "api-subscription-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": truncated,
                    "language_code": language_code,
                    "model": "bulbul:v3",
                    "speaker": speaker,
                    "output_audio_codec": "wav",
                    "speech_sample_rate": "24000",
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise VoiceServiceError(
            f"Sarvam TTS returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:300]}"
        ) from exc
    except httpx.RequestError as exc:
        raise VoiceServiceError(f"Network error calling Sarvam TTS: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise VoiceServiceError("Sarvam TTS returned non-JSON response.") from exc

    audios = payload.get("audios")
    if not audios or not isinstance(audios, list) or not audios[0]:
        raise VoiceServiceError(
            f"Sarvam TTS response missing or empty 'audios' field: "
            f"{list(payload.keys())}"
        )

    try:
        return base64.b64decode(audios[0])
    except Exception as exc:
        raise VoiceServiceError(
            "Failed to decode base64 audio from Sarvam TTS response."
        ) from exc


def _truncate_to_limit(text: str, limit: int) -> str:
    """Truncate text to *limit* characters, preferring sentence boundaries."""
    if len(text) <= limit:
        return text

    # Try to cut at the last sentence-ending punctuation within limit.
    cut = text[:limit]
    match = re.search(r"[.!?]\s", cut[::-1])
    if match:
        cut = cut[: limit - match.start()]

    return cut.rstrip() + " ..."

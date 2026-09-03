"""Speech-to-text via Sarvam AI (saaras:v3).

Transcribes audio bytes to text using the Sarvam speech-to-text REST API.
Requires the SARVAM_API_KEY environment variable.
"""

from __future__ import annotations

import os

import httpx

from src.voice.errors import VoiceServiceError

_SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


def voice_available() -> bool:
    """Return True if a Sarvam API key is configured."""
    key = os.environ.get("SARVAM_API_KEY", "")
    return bool(key and key.strip())


def speech_to_text(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language_code: str = "en-IN",
) -> str:
    """Transcribe audio to text using Sarvam AI.

    Parameters
    ----------
    audio_bytes:
        Raw audio file bytes (WAV, MP3, etc.).
    filename:
        Filename sent in the multipart form (used for codec detection).
    language_code:
        BCP-47 language code.  ``"en-IN"`` for English (default).

    Returns
    -------
    str
        The transcribed text.

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

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                _SARVAM_STT_URL,
                headers={"api-subscription-key": api_key},
                files={"file": (filename, audio_bytes, "audio/wav")},
                data={"language_code": language_code, "model": "saaras:v3"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise VoiceServiceError(
            f"Sarvam STT returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:300]}"
        ) from exc
    except httpx.RequestError as exc:
        raise VoiceServiceError(f"Network error calling Sarvam STT: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise VoiceServiceError("Sarvam STT returned non-JSON response.") from exc

    transcript = payload.get("transcript")
    if transcript is None:
        raise VoiceServiceError(
            f"Sarvam STT response missing 'transcript' field: {payload}"
        )

    return transcript

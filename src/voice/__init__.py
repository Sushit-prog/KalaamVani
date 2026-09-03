"""KalamVani voice module — Sarvam AI STT and TTS."""

from src.voice.errors import VoiceServiceError
from src.voice.stt import speech_to_text, voice_available
from src.voice.tts import text_to_speech

__all__ = [
    "VoiceServiceError",
    "speech_to_text",
    "text_to_speech",
    "voice_available",
]

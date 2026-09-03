"""Gradio dual-mode chat UI for KalamVani.

Supports text input and voice input (via Sarvam AI STT) with optional
voice output (via Sarvam AI TTS).  Falls back to text-only mode when
SARVAM_API_KEY is not set.

Usage:
    python -m ui.app
    kalamanvani            # after pip install -e .
"""

from __future__ import annotations

import tempfile

import gradio as gr

from src.agent.graph import get_app
from src.agent.run import run_once
from src.voice import VoiceServiceError, speech_to_text, text_to_speech, voice_available

# ---------------------------------------------------------------------------
# Lazy-loaded agent graph (built once on first use)
# ---------------------------------------------------------------------------
_AGENT_APP = None


def _get_agent():
    global _AGENT_APP
    if _AGENT_APP is None:
        _AGENT_APP = get_app()
    return _AGENT_APP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_last_ai_text(messages: list) -> str:
    """Return the plain-text content of the last AI message, or ''."""
    for msg in reversed(messages):
        role = getattr(msg, "role", getattr(msg, "type", ""))
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", "")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, str):
                        parts.append(block)
                    elif isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                text = " ".join(parts).strip()
                if text:
                    return text
    return ""


def _wav_bytes_to_filepath(wav_bytes: bytes) -> str:
    """Write WAV bytes to a named temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav", prefix="kalamvani_tts_", delete=False
    )
    tmp.write(wav_bytes)
    tmp.close()
    return tmp.name


def _status_text() -> str:
    if voice_available():
        return "Voice: available (Sarvam AI)"
    return "Voice: unavailable (set SARVAM_API_KEY for speech I/O)"


# ---------------------------------------------------------------------------
# Core submit logic
# ---------------------------------------------------------------------------


def _submit(
    user_text: str,
    audio_filepath: str | None,
    history: list,
    voice_output: bool,
):
    """Handle a text or voice submission and yield UI updates.

    Yields
    ------
    chatbot_update, audio_out, clear_text, updated_history
    """
    # --- Resolve the user's input text ---
    if audio_filepath and not user_text.strip():
        # Voice-only: transcribe the audio
        try:
            with open(audio_filepath, "rb") as f:
                audio_bytes = f.read()
            user_text = speech_to_text(audio_bytes)
        except VoiceServiceError as exc:
            error_msg = f"[Voice input error] {exc}"
            history = history + [
                {"role": "user", "content": "[voice]"},
                {"role": "assistant", "content": error_msg},
            ]
            yield history, None, "", history
            return

    if not user_text.strip():
        yield history, None, "", history
        return

    # --- Run the agent ---
    history = history + [{"role": "user", "content": user_text}]
    try:
        agent_messages = run_once(_get_agent(), user_text)
        ai_text = _extract_last_ai_text(agent_messages)
        if not ai_text:
            ai_text = "[No response from agent]"
    except Exception as exc:
        ai_text = f"[Agent error] {exc}"

    history = history + [{"role": "assistant", "content": ai_text}]

    # --- Optional TTS ---
    audio_out = None
    if voice_output and voice_available() and ai_text and not ai_text.startswith("["):
        try:
            wav_bytes = text_to_speech(ai_text)
            audio_out = _wav_bytes_to_filepath(wav_bytes)
        except VoiceServiceError:
            pass  # silently skip TTS on error

    yield history, audio_out, "", history


# ---------------------------------------------------------------------------
# Gradio app
# ---------------------------------------------------------------------------


def create_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app (does NOT launch)."""
    has_voice = voice_available()

    with gr.Blocks(
        title="KalamVani — Voice-First UPSC Tutor",
    ) as demo:
        gr.Markdown("# KalamVani — Voice-First UPSC Polity Tutor")
        gr.Markdown(_status_text())

        history_state = gr.State([])

        chatbot = gr.Chatbot(label="Tutor", height=420)

        with gr.Row():
            text_input = gr.Textbox(
                label="Ask a question",
                placeholder="e.g. Explain Article 14 equality before law",
                scale=4,
                show_label=False,
            )
            voice_toggle = gr.Checkbox(
                label="Voice output",
                value=False,
                interactive=has_voice,
                scale=1,
            )

        with gr.Row():
            send_btn = gr.Button("Send", variant="primary", scale=1)
            mic_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="Or speak your question",
                interactive=has_voice,
                scale=3,
            )

        audio_output = gr.Audio(label="Voice response", autoplay=True)

        # --- Event wiring ---
        # Text submit
        send_event_args = dict(
            fn=_submit,
            inputs=[text_input, mic_input, history_state, voice_toggle],
            outputs=[chatbot, audio_output, text_input, history_state],
        )

        send_btn.click(**send_event_args)
        text_input.submit(**send_event_args)

        # Voice submit (auto-send after recording stops)
        mic_input.stop_recording(**send_event_args)

    return demo


def main():
    """Launch the KalamVani Gradio UI."""
    demo = create_app()
    demo.launch(theme=gr.themes.Soft())


if __name__ == "__main__":
    main()

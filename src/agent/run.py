"""CLI entry point for the KalamVani text-only tutoring agent.

Usage:
    python -m src.agent.run --text "Explain Article 14"
    python -m src.agent.run --interactive
"""

from __future__ import annotations

import argparse

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.graph import get_app


def _render_message(msg) -> str:
    if isinstance(msg, AIMessage):
        if msg.tool_calls:
            call_names = ", ".join(tc.get("name", "") for tc in msg.tool_calls)
            return f"[agent → calling tool(s): {call_names}]"
        return f"KalamVani: {msg.content}"
    if isinstance(msg, HumanMessage):
        return f"You: {msg.content}"
    return str(getattr(msg, "content", msg))


def run_once(app, prompt: str, history: list | None = None) -> list:
    """Run the graph for a single user prompt, returning the resulting messages."""
    history = history or []
    state = {"messages": [*history, HumanMessage(content=prompt)]}
    final = app.invoke(state)
    return final.get("messages", [])


def interactive(app):
    history = []
    print("KalamVani text tutor. Type 'exit' or 'quit' to leave.\n")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if prompt.lower() in {"exit", "quit", "q"}:
            break
        if not prompt:
            continue
        history = run_once(app, prompt, history)
        for msg in history[-1:]:
            print(_render_message(msg))


def main():
    parser = argparse.ArgumentParser(description="KalamVani text-only tutor.")
    parser.add_argument("--text", type=str, help="Run a single prompt and exit.")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start an interactive REPL session.",
    )
    args = parser.parse_args()

    app = get_app()

    if args.text:
        messages = run_once(app, args.text)
        for msg in messages:
            render = _render_message(msg)
            if render:
                print(render)
    elif args.interactive or not args.text:
        interactive(app)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

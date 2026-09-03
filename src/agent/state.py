"""Tutor agent state for the KalamVani LangGraph tutoring agent."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class TutorState(TypedDict):
    """State passed between nodes of the tutoring graph.

    messages: conversation history (LangChain messages, annotated with the
        standard add_messages reducer so multiple sends are merged).
    context: retrieved corpus chunks for grounding the current turn.
    topic: the constitutional topic currently under discussion.
    structured_answer: optional structured output captured on the terminal
        node (e.g. a generated MCQ).
    """

    messages: Annotated[list, add_messages]
    context: list[dict]
    topic: str
    structured_answer: dict | None

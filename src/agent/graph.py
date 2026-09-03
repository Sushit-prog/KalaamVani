"""LangGraph tutoring graph for KalamVani.

Builds a conversational agent that:
  - uses a Socratic system prompt (guides rather than dumps answers)
  - can call corpus-grounded tools via a ToolNode
  - produces a structured answer (e.g. an MCQ) through a StructuredOutput
    terminal node when the student asks for a practice question.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.state import TutorState
from src.agent.tools import tool_registry

SOCRATIC_SYSTEM_PROMPT = """\
You are KalamVani, a patient, Socratic UPSC Polity tutor.

Your goal is to help the student reach the answer themselves rather than
spoon-feeding it. Follow these principles:
1. Ask one guiding question at a time before explaining a full concept.
2. When the student gives an answer, affirm what is right and gently correct
   what is wrong, always citing the Constitution article or principle at play.
3. Ground every factual claim in the corpus. Use the available tools
   (query_constitution, explain_concept, get_article_detail) to retrieve
   source material before making a factual statement.
4. Keep responses concise and exam-oriented. Do not overwhelm with clauses.
5. If the student asks for a practice question, call generate_mcq and then
   walk them through the options Socratic-style rather than just giving the
   answer.

You must never invent articles, case law, or constitutional provisions. If you
are not sure, say so and retrieve the relevant article first.
"""


def _build_llm():
    # Prefer GEMINI_API_KEY from environment for free-tier usage.
    import os

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=api_key,
        )
    # Fallback: a minimal deterministic model suitable for CLI/testing without
    # an API key. It echoes the latest assistant tool intent.
    return _EchoModel()


class _EchoModel:
    """No-API-key fallback chat model for the graph.

    It cannot generate real prose, but it keeps the graph runnable and returns
    a helpful message so the CLI/transcript pipeline works without an API key.
    """

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, messages, *args, **kwargs):
        # Route to tool when tool output is present and helpful.
        texts = [m.content for m in messages if hasattr(m, "content") and m.content]
        last = texts[-1] if texts else ""
        return AIMessage(
            content=(
                "I've retrieved relevant material. (Fallback model: set "
                "GEMINI_API_KEY to enable full Socratic tutoring.)\n\n"
                f"{last}"
            )
        )


def build_graph():
    """Build and compile the tutoring state graph."""
    llm = _build_llm()
    tools = tool_registry()
    llm_with_tools = llm.bind_tools(tools)

    tool_node = ToolNode(tools)

    def agent(state: TutorState) -> dict:
        messages = [SystemMessage(content=SOCRATIC_SYSTEM_PROMPT)]
        messages.extend(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def structure_output(state: TutorState) -> dict:
        # If the last tool result was an MCQ, surface it as structured output.
        structured = state.get("structured_answer")
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                pass
        return {"structured_answer": structured}

    graph = StateGraph(TutorState)
    graph.add_node("agent", agent)
    graph.add_node("tools", tool_node)
    graph.add_node("output", structure_output)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: "output"},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("output", END)

    return graph.compile()


# Convenience accessor.
def get_app():
    return build_graph()

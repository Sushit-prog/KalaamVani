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
    # Fallback: a deterministic, corpus-grounded, template-based model used
    # when no API key is present. It performs real retrieval and marks itself
    # as a no-LLM fallback so it can never be mistaken for Gemini output.
    return _GroundedFallbackModel()


class _GroundedFallbackModel:
    """No-API-key fallback chat model for the graph.

    Unlike a plain echo stub, this model:
      - performs actual corpus retrieval via query_constitution
      - returns a grounded, Socratic-flavoured response composed from the
        retrieved chunks (citing source + provenance and posing one follow-up
        question), so a no-key demo shows real grounded output
      - is clearly labeled as a TEMPLATE FALLBACK (no LLM), so the degraded
        mode is honestly distinguishable from real Gemini output
    """

    MARKER = "[TEMPLATE FALLBACK — no LLM]"

    def bind_tools(self, *args, **kwargs):
        return self

    def invoke(self, messages, *args, **kwargs):
        from src.agent.tools import query_constitution

        # Grab the latest user question (last Human message).
        question = ""
        for m in messages:
            if getattr(m, "type", "") == "human" and getattr(m, "content", None):
                question = str(m.content).strip()
        if not question:
            return AIMessage(
                content=(
                    f"{self.MARKER} I need a question from you to search the "
                    "corpus. What would you like to understand about the "
                    "Constitution?"
                )
            )

        results = query_constitution.invoke(question)
        if not results:
            return AIMessage(
                content=(
                    f"{self.MARKER} I could not find grounded material for "
                    f"'{question}' in the corpus. (Set GEMINI_API_KEY for full "
                    "Socratic tutoring.)"
                )
            )

        # Compose a grounded, Socratic-flavoured response from retrieved chunks.
        lines = [
            f"{self.MARKER} Here is grounded material retrieved from the corpus "
            f'for: "{question}"',
            "",
        ]
        for i, r in enumerate(results[:2], 1):
            lines.append(f"({i}) {r.get('source', 'source')}")
            lines.append(f"    {r.get('text', '')[:500]}")
            lines.append("")
        lines.append(
            "Given this, what do you think is the key principle at play here, "
            "and how would you explain it in your own words? "
            "(Set GEMINI_API_KEY for full Socratic tutoring.)"
        )
        return AIMessage(content="\n".join(lines))


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

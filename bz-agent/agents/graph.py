"""LangGraph orchestration: Retriever -> Reasoner -> Generator.

Linear pipeline for the vertical slice. The graph guarantees state flows in one
direction and each node persists its slice to the DynamoDB agent_scratchpad.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.generator import generator_node
from agents.reasoner import reasoner_node
from agents.retriever import retriever_node
from agents.state import AgentState
from shared.config import get_settings
from shared.dynamo import append_history, load_session


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("retriever", retriever_node)
    g.add_node("reasoner", reasoner_node)
    g.add_node("generator", generator_node)

    g.set_entry_point("retriever")
    g.add_edge("retriever", "reasoner")
    g.add_edge("reasoner", "generator")
    g.add_edge("generator", END)
    return g.compile()


_GRAPH = build_graph()


def run_plan(user_id: str, session_id: str, user_request: str,
             lat: float | None = None, lon: float | None = None) -> str:
    """One end-to-end planning request. Returns the final itinerary text."""
    s = get_settings()
    load_session(user_id, session_id)                      # ensure item exists
    append_history(user_id, session_id, "user", user_request)

    initial: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "user_request": user_request,
        "lat": lat if lat is not None else s.default_lat,
        "lon": lon if lon is not None else s.default_lon,
    }
    final = _GRAPH.invoke(initial)
    return final.get("final_answer", "(no itinerary produced)")

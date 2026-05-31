"""LangGraph orchestration: Retriever -> Reasoner -> Generator.

Linear pipeline for the vertical slice. The graph guarantees state flows in one
direction and each node persists its slice to the DynamoDB agent_scratchpad.
"""
from __future__ import annotations

from typing import Iterator

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


# Friendly progress messages shown to the user as each node finishes.
_STAGE_MESSAGES = {
    "retriever": "Fetched live data (places, parking, weather)",
    "reasoner": "Reasoned over constraints (proximity, weather, availability)",
    "generator": "Wrote your itinerary",
}


def run_plan_stream(user_id: str, session_id: str, user_request: str,
                    lat: float | None = None, lon: float | None = None
                    ) -> Iterator[dict]:
    """Generator yielding progress events, then the final itinerary.

    Each yielded dict is one of:
      {"type": "progress", "stage": <node>, "message": <text>}
      {"type": "done",     "itinerary": <text>}
    Powered by LangGraph's .stream(), which emits state after each node runs.
    """
    s = get_settings()
    load_session(user_id, session_id)
    append_history(user_id, session_id, "user", user_request)

    initial: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "user_request": user_request,
        "lat": lat if lat is not None else s.default_lat,
        "lon": lon if lon is not None else s.default_lon,
    }

    final_answer = "(no itinerary produced)"
    for update in _GRAPH.stream(initial):
        for node, state in update.items():
            if node in _STAGE_MESSAGES:
                yield {"type": "progress", "stage": node, "message": _STAGE_MESSAGES[node]}
            if isinstance(state, dict) and state.get("final_answer"):
                final_answer = state["final_answer"]
    yield {"type": "done", "itinerary": final_answer}

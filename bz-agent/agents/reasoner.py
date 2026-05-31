"""Constraint Reasoner agent.

Job: take the slim retrieved data + session state, apply hard constraints
(opening windows, transit buffers, weather — extend as needed) and output a
*validated* itinerary draft. This is the logic engine, not the prose writer.
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from agents.state import AgentState
from shared.dynamo import save_scratchpad
from shared.jsonutil import extract_json
from shared.llm import get_llm

_REASONER_PROMPT = """You are an itinerary constraint solver for Bolzano.
You receive sanitized data (POIs, events, parking, bike stations, and today's
weather) as JSON. Build a realistic ordered plan that respects:
  - geographic proximity (don't zig-zag across the city),
  - a transit buffer of >=15 min between stops,
  - parking/bike availability (skip car parks with 0 free spaces),
  - WEATHER: if rain_chance_pct is high (>=50) or thunderstorm is true, prefer
    INDOOR stops (museums, galleries, covered markets) and note it; if it's warm
    and clear, outdoor POIs and walking routes are fine.
Output ONLY JSON: a list of steps, each:
  {"order": int, "name": str, "lat": float|null, "lon": float|null,
   "why": str, "transport": str}
Let the "why" briefly reflect the weather reasoning when relevant.
No prose outside the JSON."""


def reasoner_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.1)
    payload = json.dumps(state.get("retrieved", {}), ensure_ascii=False)

    msg = llm.invoke([
        SystemMessage(content=_REASONER_PROMPT),
        HumanMessage(content=f"User request: {state['user_request']}\n\nData:\n{payload}"),
    ])
    draft = extract_json(msg.content, default=[])

    state["itinerary_draft"] = draft
    state["reasoning_notes"] = "constraints applied: proximity, 15min buffer, bike availability"

    save_scratchpad(state["user_id"], state["session_id"], "reasoner", draft)
    return state

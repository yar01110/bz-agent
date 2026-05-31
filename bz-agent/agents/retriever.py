"""Data Retriever agent.

Job: read the user's natural-language request, decide WHICH ODH tools to call,
call them, and store the (already-sanitized) results in state. It deliberately
returns slim data only — never raw ODH JSON — to protect the Reasoner's context.
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from agents.state import AgentState
from odh import content_api, mobility_api, weather_api
from shared.dynamo import save_scratchpad
from shared.jsonutil import extract_json
from shared.llm import get_llm

# The LLM only decides intent; the actual fetching is deterministic Python.
_ROUTER_PROMPT = """You map a user's request about Bolzano to data needs.
Respond ONLY with a compact JSON object with boolean keys:
  {"pois": bool, "events": bool, "mobility": bool, "category": string|null}
- "pois": they want places/sights/museums/restaurants.
- "events": they want things happening (concerts, markets, exhibitions).
- "mobility": they need transport (bus, bike, getting around).
- "category": an ODH POI category if obvious (e.g. "Museums"), else null.
No prose, JSON only."""


def retriever_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.0)
    msg = llm.invoke(
        [SystemMessage(content=_ROUTER_PROMPT),
         HumanMessage(content=state["user_request"])]
    )
    plan = extract_json(
        msg.content,
        default={"pois": True, "events": False, "mobility": True, "category": None},
    )

    lat, lon = state.get("lat"), state.get("lon")
    retrieved: dict = {}

    def _safe(label: str, fn):
        """Run one ODH fetch; never let a slow/failed endpoint abort the agent."""
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - degrade gracefully, log to scratchpad
            return {"error": f"{type(e).__name__}: {e}", "_label": label}

    # weather is always relevant — it drives the Reasoner's indoor/outdoor choices
    retrieved["weather"] = _safe("weather", weather_api.bolzano_weather)

    if plan.get("pois"):
        retrieved["pois"] = _safe(
            "pois", lambda: content_api.search_pois(
                category=plan.get("category"), lat=lat, lon=lon)
        )
    if plan.get("events"):
        retrieved["events"] = _safe(
            "events", lambda: content_api.search_events(lat=lat, lon=lon)
        )
    if plan.get("mobility"):
        retrieved["mobility"] = {
            "parking": _safe("parking", mobility_api.free_parking),
            "bike_stations": _safe("bike_stations", mobility_api.bike_stations),
        }

    state["retrieved"] = retrieved

    # persist this node's output to DynamoDB agent_scratchpad
    save_scratchpad(state["user_id"], state["session_id"], "retriever", retrieved)
    return state

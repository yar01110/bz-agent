"""Itinerary Generator agent.

Job: turn the validated draft into a friendly, human-readable itinerary.
No new facts — it only renders what the Reasoner already validated.
"""
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from agents.state import AgentState
from shared.dynamo import append_history, save_scratchpad
from shared.llm import get_llm

_GENERATOR_PROMPT = """You are a friendly Bolzano local guide.
Turn the validated itinerary JSON into a short, warm, well-structured plan.
Use the order given. Do NOT invent places, times, or facts not in the JSON.
Keep it concise and skimmable (numbered steps, one line of 'why' each)."""


def generator_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.4)
    draft = json.dumps(state.get("itinerary_draft", []), ensure_ascii=False)

    msg = llm.invoke([
        SystemMessage(content=_GENERATOR_PROMPT),
        HumanMessage(content=f"User asked: {state['user_request']}\n\nItinerary JSON:\n{draft}"),
    ])
    answer = msg.content if isinstance(msg.content, str) else str(msg.content)

    state["final_answer"] = answer
    save_scratchpad(state["user_id"], state["session_id"], "generator", answer)
    append_history(state["user_id"], state["session_id"], "assistant", answer)
    return state

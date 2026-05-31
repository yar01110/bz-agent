"""Shared graph state passed between the three agent nodes."""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # identity
    user_id: str
    session_id: str

    # input
    user_request: str          # raw natural-language request
    lat: float
    lon: float

    # Retriever output (already sanitized)
    retrieved: dict[str, Any]  # {"pois": [...], "events": [...], "mobility": [...]}

    # Reasoner output
    itinerary_draft: list[dict[str, Any]]
    reasoning_notes: str

    # Generator output
    final_answer: str

"""Open Data Hub — Tourism / Content API.

Public endpoints (no key needed) from NOI Techpark.
Docs: https://tourism.opendatahub.com/swagger/

We only expose the few calls the Retriever agent actually needs, and we hand
results straight to sanitize.py so the LLM never sees the raw multi-KB JSON.
"""
from __future__ import annotations

from typing import Any

import httpx

from odh.sanitize import slim_poi, slim_event
from shared.config import get_settings

_TIMEOUT = httpx.Timeout(30.0)


def search_pois(
    category: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: int = 3000,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find points of interest (museums, sights, ...) near a location."""
    s = get_settings()
    params: dict[str, Any] = {
        "pagesize": limit,
        "removenullvalues": "true",
    }
    if category:
        params["tagfilter"] = category  # e.g. "Museums" (verified to narrow results)
    if lat is not None and lon is not None:
        params["latitude"] = lat
        params["longitude"] = lon
        params["radius"] = radius_m

    url = f"{s.odh_content_base}/v1/ODHActivityPoi"
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        raw = r.json().get("Items", [])
    return [slim_poi(item) for item in raw]


def search_events(
    lat: float | None = None,
    lon: float | None = None,
    radius_m: int = 5000,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find events near a location."""
    s = get_settings()
    params: dict[str, Any] = {"pagesize": limit, "removenullvalues": "true"}
    if lat is not None and lon is not None:
        params["latitude"] = lat
        params["longitude"] = lon
        params["radius"] = radius_m

    url = f"{s.odh_content_base}/v1/Event"
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        raw = r.json().get("Items", [])
    return [slim_event(item) for item in raw]

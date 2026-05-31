"""Sanitization layer — THE most important file for cost & correctness.

ODH responses are large, deeply-nested, multilingual JSON. Passing them raw to
the LLM (a) blows up the context window / token bill and (b) causes the model to
hallucinate on noise. These functions strip each record down to the handful of
flat, relevant fields the Reasoner actually needs: name, coords, time, category.
Everything else is dropped.

Field shapes below were verified against the live ODH API:
  POI/Event:  Detail = {"en": {"Title": ...}, "it": {...}, "de": {...}}
              GpsPoints.position.{Latitude,Longitude}   (Event.GpsPoints may be null)
              Shortname  (often the cleanest name; may be null)
              ODHTags = [{"Id": "...", ...}]
  Mobility:   flat v2 record with sname / stype / mvalue / mvalidtime / scoordinate
"""
from __future__ import annotations

from typing import Any


def _title(detail: Any, lang: str = "en") -> str | None:
    """Detail is {lang: {"Title": str, "Language": str}}; prefer en, then any."""
    if not isinstance(detail, dict):
        return None
    chosen = detail.get(lang) or detail.get("en") or next(iter(detail.values()), {})
    if isinstance(chosen, dict):
        return chosen.get("Title")
    return None


def _coords(item: dict[str, Any]) -> tuple[float | None, float | None]:
    """GpsPoints.position.{Latitude,Longitude}; tolerant of null/missing."""
    gps = item.get("GpsPoints") or {}
    pos = (gps.get("position") if isinstance(gps, dict) else None) or {}
    return pos.get("Latitude"), pos.get("Longitude")


def slim_poi(item: dict[str, Any]) -> dict[str, Any]:
    lat, lon = _coords(item)
    tags = item.get("ODHTags") or []
    return {
        "id": item.get("Id"),
        "name": item.get("Shortname") or _title(item.get("Detail")),
        "category": tags[0].get("Id") if tags and isinstance(tags[0], dict) else None,
        "lat": lat,
        "lon": lon,
    }


def slim_event(item: dict[str, Any]) -> dict[str, Any]:
    lat, lon = _coords(item)
    return {
        "id": item.get("Id"),
        "name": item.get("Shortname") or _title(item.get("Detail")),
        "start": item.get("DateBegin"),
        "end": item.get("DateEnd"),
        "lat": lat,
        "lon": lon,
    }


def slim_station(item: dict[str, Any]) -> dict[str, Any]:
    """Mobility v2 flat records: name + live measurement (+ coords if present).

    The flat endpoint omits coordinates unless requested; `scoordinate` is
    {"x": lon, "y": lat} when present. We keep value+time so the Reasoner can
    skip empty bike stations.
    """
    coord = item.get("scoordinate") or {}
    return {
        "name": item.get("sname"),
        "type": item.get("stype"),
        "lat": coord.get("y"),
        "lon": coord.get("x"),
        "value": item.get("mvalue"),        # e.g. free bikes
        "measured_at": item.get("mvalidtime"),
    }

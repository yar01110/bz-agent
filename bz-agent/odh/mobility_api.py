"""Open Data Hub — Mobility API.

Public endpoints from NOI Techpark covering parking, bike-sharing stations, etc.
Docs: https://mobility.api.opendatahub.com  (v2 flat API)

Dataset-freshness note (verified live): the old `Bicycle/availability` feed is
dead (2016 records, value 0, no coords). `ParkingStation` and `BikesharingStation`
return real Bolzano stations WITH coordinates, so the Reasoner can do proximity.
Freshness still varies per station — surface `measured_at` so stale rows are visible.

Same rule as content_api: results go through sanitize.py before the LLM sees them.
"""
from __future__ import annotations

from typing import Any

import httpx

from odh.sanitize import slim_station
from shared.config import get_settings

_TIMEOUT = httpx.Timeout(30.0)

# Rough bounding box around Bolzano so we drop stray stations (e.g. Tarvisio).
_BZ_LAT_MIN, _BZ_LAT_MAX = 46.40, 46.60
_BZ_LON_MIN, _BZ_LON_MAX = 11.25, 11.45


def _near_bolzano(station: dict) -> bool:
    lat, lon = station.get("lat"), station.get("lon")
    if lat is None or lon is None:
        return True  # keep if we can't tell
    return _BZ_LAT_MIN <= lat <= _BZ_LAT_MAX and _BZ_LON_MIN <= lon <= _BZ_LON_MAX


def free_parking(limit: int = 15) -> list[dict[str, Any]]:
    """Live free-parking spaces per car park in Bolzano (has coords + value)."""
    s = get_settings()
    url = f"{s.odh_mobility_base}/v2/flat/ParkingStation/free/latest"
    with httpx.Client(timeout=_TIMEOUT) as client:
        # fetch extra, then geo-filter to Bolzano and trim to `limit`
        r = client.get(url, params={"limit": limit * 4})
        r.raise_for_status()
        raw = r.json().get("data", [])
    stations = [slim_station(item) for item in raw]
    return [st for st in stations if _near_bolzano(st)][:limit]


def bike_stations(limit: int = 15) -> list[dict[str, Any]]:
    """Bike-sharing station positions in Bolzano (coords; pair with live feed)."""
    s = get_settings()
    url = f"{s.odh_mobility_base}/v2/flat/BikesharingStation"
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, params={"limit": limit * 4})
        r.raise_for_status()
        raw = r.json().get("data", [])
    stations = [slim_station(item) for item in raw]
    return [st for st in stations if _near_bolzano(st)][:limit]

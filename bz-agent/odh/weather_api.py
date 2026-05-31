"""Open Data Hub — Weather API (district forecast).

District Id=1 is "Bolzano, Überetsch and Unterland". We return a slim, today
forecast the Constraint Reasoner can act on (e.g. rain/thunderstorm -> prefer
indoor museums; warm & clear -> outdoor POIs are fine).
Docs: https://tourism.opendatahub.com/swagger/  (Weather/District)
"""
from __future__ import annotations

from typing import Any

import httpx

from shared.config import get_settings

_TIMEOUT = httpx.Timeout(30.0)
_BOLZANO_DISTRICT_ID = 1


def bolzano_weather() -> dict[str, Any]:
    """Today's slim forecast for the Bolzano district, or an empty dict on error."""
    s = get_settings()
    url = f"{s.odh_content_base}/v1/Weather/District"
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, params={"language": "en"})
        r.raise_for_status()
        districts = r.json()

    bz = next((d for d in districts if d.get("Id") == _BOLZANO_DISTRICT_ID), None)
    if not bz:
        return {}
    forecast = bz.get("BezirksForecast") or []
    if not forecast:
        return {}

    today = forecast[0]
    rain = max(today.get("RainFrom") or 0, today.get("RainTo") or 0)
    return {
        "district": bz.get("DistrictName"),
        "date": today.get("date"),
        "summary": today.get("WeatherDesc"),
        "max_temp_c": today.get("MaxTemp"),
        "min_temp_c": today.get("MinTemp"),
        "rain_chance_pct": rain,
        "thunderstorm": bool(today.get("Thunderstorm")),
    }

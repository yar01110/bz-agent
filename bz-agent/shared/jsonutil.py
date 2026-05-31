"""Robust JSON extraction from LLM output.

LLMs (Claude included) often wrap JSON in ```json ... ``` fences or add a line
of prose, which breaks a naive json.loads(). This helper tolerates fences,
content returned as a list of blocks, and surrounding text.
"""
from __future__ import annotations

import json
import re
from typing import Any


def _to_text(content: Any) -> str:
    # ChatBedrockConverse may return a string OR a list of content blocks.
    if isinstance(content, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    return str(content)


def extract_json(content: Any, default: Any = None) -> Any:
    """Return the first JSON value found in the model output, or `default`."""
    text = _to_text(content).strip()

    # strip a leading/trailing markdown code fence if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # fall back: grab the widest {...} or [...] span and try that
    match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return default

"""DynamoDB single-table state store.

Single-Table Design (as in the roadmap):
    PK = "USER#<user_id>"
    SK = "SESSION#<session_id>"
Each item holds the session's conversation + the agent_scratchpad that the
LangGraph nodes read/write as they pass state Retriever -> Reasoner -> Generator.
"""
from __future__ import annotations

import json
import time
from decimal import Decimal
from typing import Any

import boto3

from shared.config import get_settings


def _to_ddb(data: Any) -> Any:
    """DynamoDB rejects Python floats — round-trip through JSON so every float
    (e.g. lat/lon coordinates) becomes a Decimal, which boto3 accepts."""
    return json.loads(json.dumps(data, default=str), parse_float=Decimal)


def _table():
    s = get_settings()
    kwargs: dict[str, Any] = {"region_name": s.aws_region}
    if s.ddb_endpoint_url:  # local DynamoDB for dev
        kwargs["endpoint_url"] = s.ddb_endpoint_url
    return boto3.resource("dynamodb", **kwargs).Table(s.ddb_table_name)


def _pk(user_id: str) -> str:
    return f"USER#{user_id}"


def _sk(session_id: str) -> str:
    return f"SESSION#{session_id}"


def load_session(user_id: str, session_id: str) -> dict[str, Any]:
    """Return the stored session item, creating the skeleton if it's new.

    We PUT the skeleton (with an empty agent_scratchpad map) so later
    `SET agent_scratchpad.<node>` updates have a valid document path to write to.
    """
    table = _table()
    resp = table.get_item(Key={"PK": _pk(user_id), "SK": _sk(session_id)})
    item = resp.get("Item")
    if item:
        return item

    skeleton = {
        "PK": _pk(user_id),
        "SK": _sk(session_id),
        "user_id": user_id,
        "session_id": session_id,
        "agent_scratchpad": {},
        "history": [],
        "created_at": int(time.time()),
    }
    # only create if it still doesn't exist (avoid clobbering a concurrent writer)
    table.put_item(
        Item=skeleton,
        ConditionExpression="attribute_not_exists(PK)",
    )
    return skeleton


def save_scratchpad(
    user_id: str, session_id: str, node: str, data: Any
) -> None:
    """Persist one node's output into agent_scratchpad.<node> atomically.

    Defensive: first ensure the agent_scratchpad map exists (older items created
    before this attribute was added wouldn't have it), then set the node key.
    """
    table = _table()
    key = {"PK": _pk(user_id), "SK": _sk(session_id)}

    table.update_item(
        Key=key,
        UpdateExpression="SET agent_scratchpad = if_not_exists(agent_scratchpad, :empty)",
        ExpressionAttributeValues={":empty": {}},
    )
    table.update_item(
        Key=key,
        UpdateExpression="SET agent_scratchpad.#n = :d, updated_at = :t",
        ExpressionAttributeNames={"#n": node},
        ExpressionAttributeValues={":d": _to_ddb(data), ":t": int(time.time())},
    )


def append_history(user_id: str, session_id: str, role: str, content: str) -> None:
    """Append a turn to the session history (list_append, creating if absent)."""
    _table().update_item(
        Key={"PK": _pk(user_id), "SK": _sk(session_id)},
        UpdateExpression=(
            "SET history = list_append(if_not_exists(history, :empty), :msg)"
        ),
        ExpressionAttributeValues={
            ":empty": [],
            ":msg": [{"role": role, "content": content, "ts": int(time.time())}],
        },
    )

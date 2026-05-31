"""AWS Lambda entrypoint  (Architecture A — serverless).

Wire to API Gateway as a proxy integration for  POST /plan-itinerary.
Body: {"user_id": "...", "session_id": "...", "request": "...", "lat": .., "lon": ..}

Caveat for the report: Lambda caps at a 15-min timeout and cold-starts the
LangGraph + boto3 imports. Fine for a single planning request; if you later add
long multi-agent loops, that's the argument for EC2/ECS instead.
"""
from __future__ import annotations

import json

from agents.graph import run_plan


def handler(event, context):
    try:
        body = event.get("body")
        data = json.loads(body) if isinstance(body, str) else (body or {})

        answer = run_plan(
            user_id=data.get("user_id", "anonymous"),
            session_id=data.get("session_id", "default"),
            user_request=data["request"],
            lat=data.get("lat"),
            lon=data.get("lon"),
        )
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"itinerary": answer}),
        }
    except KeyError as e:
        return {"statusCode": 400, "body": json.dumps({"error": f"missing field {e}"})}
    except Exception as e:  # noqa: BLE001 - surface error to caller in dev
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

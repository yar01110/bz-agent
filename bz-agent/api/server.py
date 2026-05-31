"""HTTP server entrypoint  (Architecture B — EC2 / container / ECS).

Same business logic as the Lambda handler, exposed as a long-running web server.
This is the build you put on an EC2 instance (or in the Docker image) when you
want to compare it against the serverless path. Run:

    pip install "fastapi[standard]" uvicorn
    uvicorn api.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from agents.graph import run_plan, run_plan_stream
from api.webui import INDEX_HTML

app = FastAPI(title="BZ-Agent", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Browser demo page (text box -> itinerary)."""
    return INDEX_HTML


class PlanRequest(BaseModel):
    user_id: str = "anonymous"
    session_id: str = "default"
    request: str
    lat: float | None = None
    lon: float | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/plan-itinerary")
def plan(req: PlanRequest) -> dict[str, str]:
    answer = run_plan(
        user_id=req.user_id,
        session_id=req.session_id,
        user_request=req.request,
        lat=req.lat,
        lon=req.lon,
    )
    return {"itinerary": answer}


@app.post("/plan-itinerary/stream")
def plan_stream(req: PlanRequest) -> StreamingResponse:
    """Server-Sent Events: emits progress as each agent finishes, then the result."""
    def event_source():
        for event in run_plan_stream(
            user_id=req.user_id, session_id=req.session_id,
            user_request=req.request, lat=req.lat, lon=req.lon,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")

"""Local smoke test — run the whole pipeline from the command line.

    python run_local.py "I want to visit a museum and get around by bike"

Requires either AWS creds (for Bedrock + DynamoDB) or local DynamoDB +
LLM_PROVIDER set. See README.md.
"""
from __future__ import annotations

import sys

from agents.graph import run_plan


def main() -> None:
    request = " ".join(sys.argv[1:]) or "I want to visit a museum near the centre"
    answer = run_plan(
        user_id="demo-user",
        session_id="demo-session",
        user_request=request,
    )
    print("\n=== BZ-Agent itinerary ===\n")
    print(answer)


if __name__ == "__main__":
    main()

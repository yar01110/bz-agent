"""Central configuration. Reads from environment (.env locally, real env in AWS)."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()  # no-op in AWS where vars come from the task/function environment


class Settings(BaseModel):
    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "bedrock")
    aws_region: str = os.getenv("AWS_REGION", "eu-central-1")
    bedrock_model_id: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None

    # DynamoDB
    ddb_table_name: str = os.getenv("DDB_TABLE_NAME", "bz-agent-state")
    ddb_endpoint_url: str | None = os.getenv("DDB_ENDPOINT_URL") or None

    # Open Data Hub
    odh_content_base: str = os.getenv("ODH_CONTENT_BASE", "https://tourism.opendatahub.com")
    odh_mobility_base: str = os.getenv(
        "ODH_MOBILITY_BASE", "https://mobility.api.opendatahub.com"
    )

    default_lat: float = float(os.getenv("DEFAULT_LAT", "46.4983"))
    default_lon: float = float(os.getenv("DEFAULT_LON", "11.3548"))


@lru_cache
def get_settings() -> Settings:
    return Settings()

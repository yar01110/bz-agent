"""LLM factory. One switch in config decides Bedrock vs Anthropic API.

Why a factory: the course architecture is AWS-centric, so Bedrock (IAM auth,
one AWS bill, stays in-VPC) is the default. But we keep the Anthropic API path
so the code also runs for anyone who only has a console.anthropic.com key.
"""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from shared.config import get_settings


def get_llm(temperature: float = 0.2) -> BaseChatModel:
    s = get_settings()

    if s.llm_provider == "bedrock":
        # Auth comes from the IAM role (in AWS) or your `aws configure` creds (local).
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(
            model=s.bedrock_model_id,
            region_name=s.aws_region,
            temperature=temperature,
        )

    if s.llm_provider == "anthropic":
        if not s.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is empty. "
                "Note: a Claude Pro subscription does NOT give an API key — "
                "create one at console.anthropic.com (separate billing), or "
                "switch LLM_PROVIDER=bedrock to use your AWS account."
            )
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=s.anthropic_api_key,
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {s.llm_provider!r}")

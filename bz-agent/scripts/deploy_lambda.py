"""Deploy Architecture A: Lambda from the ECR container image, with a Function URL.

Idempotent: creates the function if missing, otherwise updates its image.
Prints a public Function URL you can curl to test.  (API Gateway can be added
in front later; the Function URL is the quickest way to prove the Lambda works.)
"""
from __future__ import annotations

import time

import boto3

REGION = "eu-central-1"
FN = "bz-agent"
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
IMAGE = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/bz-agent:lambda"
ROLE = f"arn:aws:iam::{ACCOUNT}:role/bz-agent-lambda-role"

ENV = {
    "LLM_PROVIDER": "bedrock",
    "BEDROCK_MODEL_ID": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "DDB_TABLE_NAME": "bz-agent-state",
    # AWS_REGION is reserved & auto-set by Lambda — do not include it here.
}

lam = boto3.client("lambda", region_name=REGION)


def create_or_update() -> None:
    try:
        lam.get_function(FunctionName=FN)
        print("updating function code + config...")
        lam.update_function_code(FunctionName=FN, ImageUri=IMAGE, Publish=True)
        _wait_updated()
        lam.update_function_configuration(
            FunctionName=FN, Timeout=120, MemorySize=2048, Environment={"Variables": ENV}
        )
    except lam.exceptions.ResourceNotFoundException:
        print("creating function...")
        lam.create_function(
            FunctionName=FN,
            PackageType="Image",
            Code={"ImageUri": IMAGE},
            Role=ROLE,
            Timeout=120,
            MemorySize=2048,
            Environment={"Variables": ENV},
        )
    _wait_active()


def _wait_active() -> None:
    for _ in range(60):
        st = lam.get_function(FunctionName=FN)["Configuration"]["State"]
        if st == "Active":
            return
        time.sleep(3)


def _wait_updated() -> None:
    for _ in range(60):
        st = lam.get_function(FunctionName=FN)["Configuration"]["LastUpdateStatus"]
        if st == "Successful":
            return
        time.sleep(3)


def ensure_function_url() -> str:
    try:
        url = lam.create_function_url_config(FunctionName=FN, AuthType="NONE")["FunctionUrl"]
    except lam.exceptions.ResourceConflictException:
        url = lam.get_function_url_config(FunctionName=FN)["FunctionUrl"]
    # allow public invoke of the URL
    try:
        lam.add_permission(
            FunctionName=FN, StatementId="public-url",
            Action="lambda:InvokeFunctionUrl", Principal="*",
            FunctionUrlAuthType="NONE",
        )
    except lam.exceptions.ResourceConflictException:
        pass
    return url


def main() -> None:
    create_or_update()
    url = ensure_function_url()
    print("LAMBDA_READY")
    print("FUNCTION_URL =", url)


if __name__ == "__main__":
    main()

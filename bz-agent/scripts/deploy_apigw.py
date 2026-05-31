"""Deploy roadmap Step 5: API Gateway (HTTP API) in front of the Lambda.

Creates an HTTP API with a single  POST /plan-itinerary  route, proxied to the
bz-agent Lambda (payload format 2.0), grants API Gateway permission to invoke
the function, and auto-deploys the $default stage. Prints the public endpoint.

Idempotent: reuses an existing 'bz-agent-api' if present.
"""
from __future__ import annotations

import boto3

REGION = "eu-central-1"
API_NAME = "bz-agent-api"
FN = "bz-agent"
ROUTE = "POST /plan-itinerary"

ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
FN_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT}:function:{FN}"

apigw = boto3.client("apigatewayv2", region_name=REGION)
lam = boto3.client("lambda", region_name=REGION)


def find_api() -> str | None:
    for a in apigw.get_apis()["Items"]:
        if a["Name"] == API_NAME:
            return a["ApiId"]
    return None


def main() -> None:
    api_id = find_api()
    if api_id is None:
        api = apigw.create_api(Name=API_NAME, ProtocolType="HTTP")
        api_id = api["ApiId"]
        endpoint = api["ApiEndpoint"]
    else:
        endpoint = apigw.get_api(ApiId=api_id)["ApiEndpoint"]

    integration = apigw.create_integration(
        ApiId=api_id,
        IntegrationType="AWS_PROXY",
        IntegrationUri=FN_ARN,
        IntegrationMethod="POST",
        PayloadFormatVersion="2.0",
    )["IntegrationId"]

    # (re)create the route pointing at the integration
    existing = {r["RouteKey"]: r["RouteId"] for r in apigw.get_routes(ApiId=api_id)["Items"]}
    target = f"integrations/{integration}"
    if ROUTE in existing:
        apigw.update_route(ApiId=api_id, RouteId=existing[ROUTE], Target=target)
    else:
        apigw.create_route(ApiId=api_id, RouteKey=ROUTE, Target=target)

    # auto-deploying $default stage
    try:
        apigw.create_stage(ApiId=api_id, StageName="$default", AutoDeploy=True)
    except apigw.exceptions.ConflictException:
        pass

    # allow API Gateway to invoke the Lambda
    try:
        lam.add_permission(
            FunctionName=FN,
            StatementId="apigw-invoke",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{ACCOUNT}:{api_id}/*/*/plan-itinerary",
        )
    except lam.exceptions.ResourceConflictException:
        pass

    print("APIGW_READY")
    print("API_ID   =", api_id)
    print("ENDPOINT =", f"{endpoint}/plan-itinerary")


if __name__ == "__main__":
    main()

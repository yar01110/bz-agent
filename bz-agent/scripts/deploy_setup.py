"""Idempotent AWS scaffolding for deployment: ECR repo + IAM roles.

Creates (or reuses):
  - ECR repository  'bz-agent'           (holds both image tags: lambda, server)
  - IAM role        'bz-agent-lambda-role'  (Lambda execution + Bedrock + DynamoDB)
  - IAM role        'bz-agent-ec2-role'     (EC2: Bedrock + DynamoDB + ECR pull + SSM)
  - Instance profile 'bz-agent-ec2-profile' wrapping the EC2 role

Prints the identifiers the build/deploy steps need.
"""
from __future__ import annotations

import json

import boto3

REGION = "eu-central-1"
REPO = "bz-agent"

TRUST = {
    "lambda": {"Service": "lambda.amazonaws.com"},
    "ec2": {"Service": "ec2.amazonaws.com"},
}

MANAGED = {
    "lambda": [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    ],
    "ec2": [
        "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
        "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    ],
}


def _trust_doc(principal: dict) -> str:
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": principal, "Action": "sts:AssumeRole"}],
    })


def ensure_repo(ecr) -> str:
    try:
        r = ecr.describe_repositories(repositoryNames=[REPO])
        uri = r["repositories"][0]["repositoryUri"]
    except ecr.exceptions.RepositoryNotFoundException:
        r = ecr.create_repository(repositoryName=REPO, imageScanningConfiguration={"scanOnPush": True})
        uri = r["repository"]["repositoryUri"]
    return uri


def ensure_role(iam, name: str, kind: str) -> str:
    try:
        iam.create_role(RoleName=name, AssumeRolePolicyDocument=_trust_doc(TRUST[kind]))
    except iam.exceptions.EntityAlreadyExistsException:
        pass
    for arn in MANAGED[kind]:
        iam.attach_role_policy(RoleName=name, PolicyArn=arn)
    return iam.get_role(RoleName=name)["Role"]["Arn"]


def ensure_instance_profile(iam, profile: str, role: str) -> None:
    try:
        iam.create_instance_profile(InstanceProfileName=profile)
    except iam.exceptions.EntityAlreadyExistsException:
        pass
    try:
        iam.add_role_to_instance_profile(InstanceProfileName=profile, RoleName=role)
    except iam.exceptions.LimitExceededException:
        pass  # role already attached


def main() -> None:
    ecr = boto3.client("ecr", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)
    acct = boto3.client("sts").get_caller_identity()["Account"]

    repo_uri = ensure_repo(ecr)
    lambda_role = ensure_role(iam, "bz-agent-lambda-role", "lambda")
    ec2_role = ensure_role(iam, "bz-agent-ec2-role", "ec2")
    ensure_instance_profile(iam, "bz-agent-ec2-profile", "bz-agent-ec2-role")

    print("ACCOUNT_ID   =", acct)
    print("REGION       =", REGION)
    print("ECR_REPO_URI =", repo_uri)
    print("LAMBDA_ROLE  =", lambda_role)
    print("EC2_ROLE     =", ec2_role)
    print("EC2_PROFILE  = bz-agent-ec2-profile")


if __name__ == "__main__":
    main()

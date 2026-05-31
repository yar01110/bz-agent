# BZ-Agent — Infrastructure as Code (Terraform)

This module declares the entire BZ-Agent AWS stack in one place: ECR, DynamoDB,
IAM roles, a custom VPC (subnet, internet gateway, routing, DynamoDB endpoint,
security group), the Lambda + API Gateway (Architecture A), and the EC2 instance
(Architecture B). It is the declarative equivalent of the imperative boto3
scripts in `bz-agent/scripts/`.

## Why both Terraform and boto3 scripts?
The boto3 scripts were used for the live, step-by-step build during development.
This Terraform codifies the result as reproducible Infrastructure as Code — a
cloud-native principle: the whole environment can be recreated from version
control with one command.

## Usage
```bash
# 1. Build and push the two container images first (Terraform references them):
#    docker build -f bz-agent/Dockerfile        -t <ecr>:server .
#    docker build -f bz-agent/Dockerfile.lambda -t <ecr>:lambda .
#    docker push <ecr>:server && docker push <ecr>:lambda

# 2. Provision everything:
terraform init
terraform plan
terraform apply

# 3. Read the endpoints:
terraform output
```

## Notes
- Region defaults to `eu-central-1`; override in `variables.tf` or `-var`.
- Bedrock model access (Anthropic Claude) must be enabled in the account once,
  via the Bedrock console — that is an account setting, not a Terraform resource.
- The container images are built outside Terraform (Dockerfiles); apply order is
  build → push → `terraform apply`.

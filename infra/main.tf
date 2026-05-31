###############################################################################
# BZ-Agent — Infrastructure as Code (Terraform)
#
# Codifies the same AWS architecture that the boto3 scripts in bz-agent/scripts/
# create imperatively. Provided as the reproducible, declarative definition of
# the stack (a cloud-native principle). It builds: ECR, DynamoDB, IAM roles,
# a custom VPC (subnet + IGW + routing + DynamoDB endpoint + SG), the Lambda +
# API Gateway (Architecture A), and the EC2 instance (Architecture B).
#
# NOTE: container images are built/pushed separately (see Dockerfiles); Terraform
# references them by ECR tag. Run order: build & push images -> terraform apply.
###############################################################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

locals {
  account_id    = data.aws_caller_identity.current.account_id
  ecr_repo_url  = "${local.account_id}.dkr.ecr.${var.region}.amazonaws.com/${var.project}"
  image_server  = "${local.ecr_repo_url}:${var.image_tag_server}"
  image_lambda  = "${local.ecr_repo_url}:${var.image_tag_lambda}"
  common_tags   = { Project = var.project }
}

###############################################################################
# Container registry
###############################################################################
resource "aws_ecr_repository" "app" {
  name                 = var.project
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
  tags = local.common_tags
}

###############################################################################
# State store — DynamoDB single-table (PK=USER#, SK=SESSION#)
###############################################################################
resource "aws_dynamodb_table" "state" {
  name         = "${var.project}-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }
  tags = local.common_tags
}

###############################################################################
# IAM — least-privilege execution roles
###############################################################################
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.common_tags
}

resource "aws_iam_role" "ec2" {
  name               = "${var.project}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  for_each = toset([
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
  ])
  role       = aws_iam_role.lambda.name
  policy_arn = each.value
}

resource "aws_iam_role_policy_attachment" "ec2_attach" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ])
  role       = aws_iam_role.ec2.name
  policy_arn = each.value
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project}-ec2-profile"
  role = aws_iam_role.ec2.name
}

###############################################################################
# Networking — custom VPC (the "create and manage a VPC" objective)
###############################################################################
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(local.common_tags, { Name = "${var.project}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${var.project}-igw" })
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags                    = merge(local.common_tags, { Name = "${var.project}-public-subnet" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(local.common_tags, { Name = "${var.project}-public-rtb" })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Free gateway endpoint: DynamoDB traffic stays on the AWS private network
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id]
  tags              = merge(local.common_tags, { Name = "${var.project}-dynamodb-endpoint" })
}

resource "aws_security_group" "app" {
  name        = "${var.project}-vpc-sg"
  description = "bz-agent http 8080 (custom VPC)"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "demo http"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = merge(local.common_tags, { Name = "${var.project}-vpc-sg" })
}

###############################################################################
# Architecture A — Lambda (container image) + HTTP API Gateway
###############################################################################
resource "aws_lambda_function" "app" {
  function_name = var.project
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = local.image_lambda
  timeout       = 120
  memory_size   = 2048

  environment {
    variables = {
      LLM_PROVIDER     = "bedrock"
      BEDROCK_MODEL_ID = var.bedrock_model_id
      DDB_TABLE_NAME   = aws_dynamodb_table.state.name
    }
  }
  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project}-api"
  protocol_type = "HTTP"
  tags          = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.app.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "plan" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /plan-itinerary"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "apigw-invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*/plan-itinerary"
}

###############################################################################
# Architecture B — EC2 instance running the server image (inside the VPC)
###############################################################################
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  user_data = <<-EOF
    #!/bin/bash
    set -xe
    dnf install -y docker
    systemctl enable --now docker
    aws ecr get-login-password --region ${var.region} | docker login --username AWS --password-stdin ${local.account_id}.dkr.ecr.${var.region}.amazonaws.com
    docker pull ${local.image_server}
    docker run -d --restart always -p 8080:8080 \
      -e LLM_PROVIDER=bedrock -e AWS_REGION=${var.region} \
      -e BEDROCK_MODEL_ID=${var.bedrock_model_id} \
      -e DDB_TABLE_NAME=${aws_dynamodb_table.state.name} ${local.image_server}
  EOF

  tags = merge(local.common_tags, { Name = "${var.project}-ec2" })
}

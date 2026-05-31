variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "project" {
  description = "Project tag / name prefix"
  type        = string
  default     = "bz-agent"
}

variable "bedrock_model_id" {
  description = "Bedrock inference profile for Claude"
  type        = string
  default     = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
}

variable "image_tag_server" {
  description = "ECR image tag for the EC2/server build"
  type        = string
  default     = "server"
}

variable "image_tag_lambda" {
  description = "ECR image tag for the Lambda build"
  type        = string
  default     = "lambda"
}

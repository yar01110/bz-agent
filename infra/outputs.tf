output "ecr_repository_url" {
  description = "ECR repository to push the two image tags to"
  value       = aws_ecr_repository.app.repository_url
}

output "dynamodb_table" {
  value = aws_dynamodb_table.state.name
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "lambda_api_endpoint" {
  description = "Public POST endpoint (Architecture A)"
  value       = "${aws_apigatewayv2_api.http.api_endpoint}/plan-itinerary"
}

output "ec2_endpoint" {
  description = "Public endpoint (Architecture B)"
  value       = "http://${aws_instance.app.public_ip}:8080"
}

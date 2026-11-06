output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "chat_endpoint" {
  description = "Full URL for the POST /chat troubleshooting endpoint"
  value       = module.api_gateway.chat_endpoint
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = module.lambda.function_name
}

output "lambda_role_arn" {
  description = "ARN of the least-privilege IAM execution role"
  value       = module.iam.lambda_role_arn
}

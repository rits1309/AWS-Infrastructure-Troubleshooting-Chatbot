output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.chat_api.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.chat_api.arn
}

output "invoke_arn" {
  description = "API Gateway invocation ARN of the Lambda function"
  value       = aws_lambda_function.chat_api.invoke_arn
}
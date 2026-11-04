output "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  value       = aws_iam_role.lambda_exec.arn
}

output "lambda_role_name" {
  description = "Name of the IAM role for Lambda execution"
  value       = aws_iam_role.lambda_exec.name
}
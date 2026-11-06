variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "cloudops-ai-assistant"
}

variable "environment" {
  description = "Deployment environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "lambda_function_name" {
  description = "Name of the backend Lambda function"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN of the backend Lambda function"
  type        = string
}

variable "rate_limit" {
  description = "Throttling steady-state request rate limit (requests/sec)"
  type        = number
  default     = 5
}

variable "burst_limit" {
  description = "Throttling burst request limit"
  type        = number
  default     = 10
}
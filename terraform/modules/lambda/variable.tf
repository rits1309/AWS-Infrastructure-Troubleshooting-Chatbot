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

variable "lambda_role_arn" {
  description = "IAM Role ARN from IAM module"
  type        = string
}

variable "source_dir" {
  description = "Path to backend/src directory"
  type        = string
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  type        = string
}

variable "bedrock_model_arn" {
  description = "Bedrock Foundation Model or Inference Profile ARN"
  type        = string
}

variable "aws_region" {
  description = "AWS region for Bedrock"
  type        = string
  default     = "ap-south-1"
}

variable "timeout_seconds" {
  description = "Lambda execution timeout in seconds (Bedrock queries can take 5-15s)"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Memory size for Lambda in MB"
  type        = number
  default     = 256
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}
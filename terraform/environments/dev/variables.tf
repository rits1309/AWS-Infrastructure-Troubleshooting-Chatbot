variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "cloudops-ai-assistant"
}

variable "environment" {
  description = "Environment name (e.g. dev, prod)"
  type        = string
  default     = "dev"
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  type        = string
  default     = "IZBE4IPYRY"
}

variable "bedrock_model_arn" {
  description = "Bedrock Foundation Model or Inference Profile ARN"
  type        = string
  default     = "arn:aws:bedrock:ap-south-1:713881796636:inference-profile/apac.amazon.nova-lite-v1:0"
}

variable "rate_limit" {
  description = "API Gateway throttling rate limit (req/s)"
  type        = number
  default     = 5
}

variable "burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 10
}

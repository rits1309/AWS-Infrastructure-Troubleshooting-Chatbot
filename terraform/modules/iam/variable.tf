variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "cloudops-ai-assistant"
}

variable "environment" {
  description = "Deployment environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "knowledge_base_arn" {
  description = "ARN of the Bedrock Knowledge Base (or wildcard if managed outside)"
  type        = string
  default     = "*"
}
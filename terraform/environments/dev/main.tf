terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. IAM Execution Role Module
module "iam" {
  source = "../../modules/iam"

  project_name       = var.project_name
  environment        = var.environment
  knowledge_base_arn = "arn:aws:bedrock:${var.aws_region}:*:knowledge-base/${var.knowledge_base_id}"
}

# 2. Lambda Function & Packaging Module
module "lambda" {
  source = "../../modules/lambda"

  project_name      = var.project_name
  environment       = var.environment
  lambda_role_arn   = module.iam.lambda_role_arn
  source_dir        = "${path.root}/../../../backend/src"
  knowledge_base_id = var.knowledge_base_id
  bedrock_model_arn = var.bedrock_model_arn
  aws_region        = var.aws_region

  depends_on = [module.iam]
}

# 3. API Gateway HTTP API Module
module "api_gateway" {
  source = "../../modules/api_gateway"

  project_name         = var.project_name
  environment          = var.environment
  lambda_function_name = module.lambda.function_name
  lambda_invoke_arn    = module.lambda.invoke_arn
  rate_limit           = var.rate_limit
  burst_limit          = var.burst_limit

  depends_on = [module.lambda]
}

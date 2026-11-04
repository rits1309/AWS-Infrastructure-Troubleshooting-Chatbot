# 1. Automatically zip the backend/src/ directory
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.root}/dist/lambda.zip"
}

# 2. Manage CloudWatch Log Group with retention policy
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-api"
  retention_in_days = var.log_retention_in_days

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 3. AWS Lambda Function definition
resource "aws_lambda_function" "chat_api" {
  function_name    = "${var.project_name}-${var.environment}-api"
  description      = "CloudOps AI Assistant Bedrock Query Handler"
  role             = var.lambda_role_arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout     = var.timeout_seconds
  memory_size = var.memory_size

  environment {
    variables = {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
      BEDROCK_MODEL_ARN = var.bedrock_model_arn
      AWS_REGION        = var.aws_region
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
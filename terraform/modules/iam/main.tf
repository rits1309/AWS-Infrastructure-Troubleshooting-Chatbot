# 1. Trust policy: allows AWS Lambda service to assume this role
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# 2. IAM Role for Lambda execution
resource "aws_iam_role" "lambda_exec" {
  name               = "${var.project_name}-${var.environment}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 3. Least-privilege policy document
data "aws_iam_policy_document" "lambda_permissions" {
  # Logging permissions to CloudWatch
  statement {
    sid    = "AllowCloudWatchLogging"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # Bedrock Knowledge Base query permissions ONLY
  statement {
    sid    = "AllowBedrockRetrieveAndGenerate"
    effect = "Allow"
    actions = [
      "bedrock:RetrieveAndGenerate",
      "bedrock:Retrieve"
    ]
    resources = [var.knowledge_base_arn]
  }

  # Model invocation permission via inference profile
  statement {
    sid    = "AllowBedrockModelInvoke"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = ["*"]
  }
}

# 4. Attach inline policy to the role
resource "aws_iam_role_policy" "lambda_policy" {
  name   = "${var.project_name}-${var.environment}-lambda-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}
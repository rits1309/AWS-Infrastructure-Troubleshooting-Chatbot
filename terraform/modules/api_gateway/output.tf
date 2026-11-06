output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "chat_endpoint" {
  description = "Full URL for the chat POST route"
  value       = "${aws_apigatewayv2_api.http_api.api_endpoint}/chat"
}

output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.http_api.id
}
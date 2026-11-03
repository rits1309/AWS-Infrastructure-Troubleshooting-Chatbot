"""
backend/tests/test_handler.py - End-to-end unit tests for Lambda handler
"""

import json
from unittest.mock import patch
from src.handler import lambda_handler


def test_cors_preflight_options_rest_api():
    """Verify REST API v1 OPTIONS preflight."""
    event = {"httpMethod": "OPTIONS"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_cors_preflight_options_http_api_v2():
    """Verify HTTP API v2 OPTIONS preflight."""
    event = {"requestContext": {"http": {"method": "OPTIONS"}}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_missing_body():
    """Verify 400 when body is None."""
    event = {"httpMethod": "POST", "body": None}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "ValidationError"
    assert "Missing request body" in body["message"]


def test_malformed_json_body():
    """Verify 400 when body is not valid JSON."""
    event = {"httpMethod": "POST", "body": "{this is not valid json}"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "ValidationError"
    assert "Invalid JSON format" in body["message"]


def test_validation_error_short_message():
    """Verify validator error propagates as 400."""
    event = {"httpMethod": "POST", "body": json.dumps({"message": "ab"})}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "ValidationError"
    assert "at least 3 characters" in body["message"]


@patch("src.handler.kb_service.query")
def test_bedrock_runtime_error_returns_502(mock_query):
    """Verify Bedrock outage / throttling returns 502 Bad Gateway."""
    mock_query.side_effect = RuntimeError("Bedrock API error [ThrottlingException]: Rate exceeded")

    event = {
        "httpMethod": "POST",
        "body": json.dumps({"message": "Why are my EKS pods in Pending?"})
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 502
    body = json.loads(response["body"])
    assert body["error"] == "BedrockError"
    assert "ThrottlingException" in body["message"]


@patch("src.handler.kb_service.query")
def test_successful_query_flow(mock_query):
    """Verify complete end-to-end success returns 200 and formatted payload."""
    mock_query.return_value = {
        "answer": "Check scheduler events using kubectl describe pod.",
        "sessionId": "sess-test-456",
        "citations": [
            {
                "retrievedReferences": [
                    {
                        "location": {"s3Location": {"uri": "s3://cloudops-runbooks-713881796636/docs/eks/pod-pending.md"}},
                        "content": {"text": "A Kubernetes Pod remains in the Pending phase when resources are missing."}
                    }
                ]
            }
        ]
    }

    event = {
        "httpMethod": "POST",
        "body": json.dumps({"message": "Why are my EKS pods in Pending?"})
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert "Check scheduler events" in body["answer"]
    assert body["sessionId"] == "sess-test-456"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["title"] == "Pod Pending"
    assert body["sources"][0]["location"] == "s3://cloudops-runbooks-713881796636/docs/eks/pod-pending.md"
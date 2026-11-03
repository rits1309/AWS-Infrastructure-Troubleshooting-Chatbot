"""
backend/test_local_lambda.py - Test lambda_handler with simulated API Gateway events
"""

import json
from unittest.mock import patch
from src.handler import lambda_handler


def simulate_request(question: str, session_id: str = None):
    print("=" * 70)
    print(f"Simulating API Gateway Event for: '{question}'")
    print("=" * 70)

    payload = {"message": question}
    if session_id:
        payload["sessionId"] = session_id

    event = {
        "version": "2.0",
        "routeKey": "POST /chat",
        "rawPath": "/chat",
        "headers": {
            "content-type": "application/json",
            "user-agent": "CloudOpsChatClient/1.0"
        },
        "requestContext": {
            "http": {
                "method": "POST",
                "path": "/chat",
                "protocol": "HTTP/1.1"
            }
        },
        "body": json.dumps(payload)
    }

    # Mock the Bedrock service for safe offline simulation
    with patch("src.handler.kb_service.query") as mock_query:
        mock_query.return_value = {
            "answer": (
                "Based on the EKS Pod Pending Runbook, pods remain in Pending due to:\n"
                "1. Insufficient CPU or Memory on nodes.\n"
                "2. Node selector or affinity mismatch.\n"
                "3. Untolerated node taints or PVC binding issues.\n\n"
                "Diagnostic commands:\n"
                "- kubectl describe pod <pod-name> -n <namespace>\n"
                "- kubectl get nodes -o wide"
            ),
            "sessionId": session_id or "simulated-session-42",
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "location": {
                                "s3Location": {
                                    "uri": "s3://cloudops-runbooks-713881796636/docs/eks/pod-pending.md"
                                }
                            },
                            "content": {
                                "text": "A Kubernetes Pod remains in the Pending phase when it has been accepted by the API server..."
                            }
                        }
                    ]
                }
            ]
        }

        response = lambda_handler(event, None)

    print(f"HTTP Status Code : {response['statusCode']}")
    print(f"CORS Origin      : {response['headers'].get('Access-Control-Allow-Origin')}")
    print("-" * 70)
    parsed_body = json.loads(response["body"])
    print("RESPONSE BODY:")
    print(json.dumps(parsed_body, indent=2))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test 1: Normal valid question
    simulate_request("Why are my EKS pods stuck in Pending?")

    # Test 2: Validation test - empty body / short question
    print("=" * 70)
    print("Testing Validation Failure (Overshort message 'hi'):")
    print("=" * 70)
    invalid_event = {
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"message": "hi"})
    }
    invalid_resp = lambda_handler(invalid_event, None)
    print(f"Status Code: {invalid_resp['statusCode']}")
    print(f"Body: {invalid_resp['body']}")
    print("=" * 70)

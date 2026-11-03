"""
backend/tests/test_response_formatter.py - Unit tests for response formatter
"""

import json
from src.response_formatter import build_http_response, format_citations, CORS_HEADERS


def test_build_http_response_structure():
    """Verify standard Lambda proxy response format."""
    payload = {"message": "Success", "code": 200}
    response = build_http_response(200, payload)

    assert response["statusCode"] == 200
    assert response["headers"] == CORS_HEADERS
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    
    # Body must be a stringified JSON
    assert isinstance(response["body"], str)
    parsed_body = json.loads(response["body"])
    assert parsed_body["message"] == "Success"


def test_build_http_error_response():
    """Verify error responses follow same contract."""
    error_payload = {"error": "ValidationError", "message": "Field required"}
    response = build_http_response(400, error_payload)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "ValidationError"


def test_format_citations_empty():
    """Empty raw citations should return empty list."""
    assert format_citations([]) == []


def test_format_citations_extraction_and_deduplication():
    """Verify title generation, snippet truncation, and deduplication."""
    raw_citations = [
        {
            "retrievedReferences": [
                {
                    "location": {"s3Location": {"uri": "s3://my-bucket/docs/eks/pod-pending.md"}},
                    "content": {"text": "A Kubernetes pod remains in Pending when resources are unavailable."}
                },
                # Duplicate reference that should be filtered out
                {
                    "location": {"s3Location": {"uri": "s3://my-bucket/docs/eks/pod-pending.md"}},
                    "content": {"text": "A Kubernetes pod remains in Pending when resources are unavailable."}
                },
                # Distinct reference
                {
                    "location": {"s3Location": {"uri": "s3://my-bucket/docs/eks/crashloopbackoff.md"}},
                    "content": {"text": "A" * 300}  # Tests truncation (>250 chars)
                }
            ]
        }
    ]

    sources = format_citations(raw_citations)

    # 3 incoming references, but 1 was duplicate -> exactly 2 should remain
    assert len(sources) == 2

    # Verify first source
    assert sources[0]["title"] == "Pod Pending"
    assert sources[0]["location"] == "s3://my-bucket/docs/eks/pod-pending.md"
    assert "pod remains in Pending" in sources[0]["snippet"]

    # Verify second source title and truncation
    assert sources[1]["title"] == "Crashloopbackoff"
    assert sources[1]["snippet"].endswith("...")
    assert len(sources[1]["snippet"]) <= 253  # 250 chars + "..."
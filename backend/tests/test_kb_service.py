"""
backend/tests/test_kb_service.py - Unit tests for BedrockKBService using mocks
"""

import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from src.kb_service import BedrockKBService


def test_missing_kb_id_raises_value_error():
    """Verify service raises error if KB ID is empty."""
    service = BedrockKBService(kb_id="")
    with pytest.raises(ValueError, match="KNOWLEDGE_BASE_ID is not configured"):
        service.query("Why are my pods stuck in Pending?")


def test_successful_query_mock():
    """Verify successful retrieve_and_generate response extraction."""
    service = BedrockKBService(kb_id="TEST_KB_123")

    # Mock the internal boto3 client
    mock_boto = MagicMock()
    mock_boto.retrieve_and_generate.return_value = {
        "output": {"text": "To fix Pending pods, inspect node capacity."},
        "sessionId": "sess-xyz",
        "citations": [{"retrievedReferences": []}]
    }
    service._client = mock_boto

    result = service.query("Why are my pods stuck in Pending?", session_id="sess-xyz")

    assert result["answer"] == "To fix Pending pods, inspect node capacity."
    assert result["sessionId"] == "sess-xyz"
    assert len(result["citations"]) == 1

    # Verify that the boto3 client was called with correct parameters
    call_args = mock_boto.retrieve_and_generate.call_args[1]
    assert call_args["input"]["text"] == "Why are my pods stuck in Pending?"
    assert call_args["sessionId"] == "sess-xyz"
    assert call_args["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"]["knowledgeBaseId"] == "TEST_KB_123"


def test_client_error_handling():
    """Verify ClientError is wrapped into a clean RuntimeError."""
    service = BedrockKBService(kb_id="TEST_KB_123")

    mock_boto = MagicMock()
    mock_boto.retrieve_and_generate.side_effect = ClientError(
        error_response={"Error": {"Code": "ResourceNotFoundException", "Message": "KB not found"}},
        operation_name="RetrieveAndGenerate"
    )
    service._client = mock_boto

    with pytest.raises(RuntimeError, match="Bedrock API error \\[ResourceNotFoundException\\]"):
        service.query("Any question")
"""
backend/src/handler.py - AWS Lambda main handler for API Gateway integration
"""

import json
import logging
import os
from typing import Dict, Any

from src.validator import validate_chat_request
from src.response_formatter import build_http_response, format_citations
from src.kb_service import BedrockKBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialized once during cold start so subsequent invocations reuse the connection
kb_service = BedrockKBService(
    region=os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION", "ap-south-1"),
    kb_id=os.environ.get("KNOWLEDGE_BASE_ID", ""),
    model_arn=os.environ.get(
        "BEDROCK_MODEL_ARN",
        "arn:aws:bedrock:ap-south-1:713881796636:inference-profile/apac.amazon.nova-lite-v1:0"
    )
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entrypoint. Supports both API Gateway v1 (REST) and v2 (HTTP API) formats.
    """
    logger.info("Received event: %s", json.dumps(event.get("requestContext", {})))

    # 1. Handle CORS preflight (OPTIONS)
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    if http_method == "OPTIONS":
        return build_http_response(200, {"status": "ok"})

    # 2. Parse request body
    body_raw = event.get("body")
    if not body_raw:
        return build_http_response(400, {"error": "ValidationError", "message": "Missing request body."})

    try:
        body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw
    except (json.JSONDecodeError, TypeError):
        return build_http_response(400, {"error": "ValidationError", "message": "Invalid JSON format in body."})

    # 3. Validate input
    is_valid, error_msg, validated_data = validate_chat_request(body)
    if not is_valid:
        return build_http_response(400, {"error": "ValidationError", "message": error_msg})

    question = validated_data["message"]
    session_id = validated_data.get("sessionId")

    # 4. Invoke Bedrock Knowledge Base
    try:
        logger.info("Querying Knowledge Base for message length %d", len(question))
        kb_result = kb_service.query(question=question, session_id=session_id)

        answer = kb_result.get("answer", "")
        raw_citations = kb_result.get("citations", [])
        returned_session_id = kb_result.get("sessionId")

        formatted_sources = format_citations(raw_citations)

        return build_http_response(200, {
            "answer": answer,
            "sessionId": returned_session_id,
            "sources": formatted_sources
        })

    except ValueError as ve:
        logger.error("Configuration error: %s", str(ve))
        return build_http_response(500, {"error": "ConfigError", "message": str(ve)})

    except RuntimeError as re_err:
        logger.error("Bedrock service failure: %s", str(re_err))
        return build_http_response(502, {"error": "BedrockError", "message": str(re_err)})

    except Exception as e:
        logger.exception("Unexpected unhandled exception: %s", str(e))
        return build_http_response(500, {"error": "InternalServerError", "message": "An internal error occurred."})
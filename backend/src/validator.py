"""
backend/src/validator.py - Request validation and prompt sanitization
"""

import re
from typing import Dict, Any, Tuple, Optional

MAX_QUESTION_LENGTH = 1000
MIN_QUESTION_LENGTH = 3

# Patterns commonly associated with prompt injection or system override attempts
SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous\s+prompts",
    r"system\s*:\s*you\s+are\s+now",
    r"reveal\s+(your\s+)?system\s+prompt",
]


def validate_chat_request(body: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates the incoming API Gateway body payload.
    Returns: (is_valid, error_message, sanitized_data)
    """
    if not body or not isinstance(body, dict):
        return False, "Request body must be a valid JSON object.", None

    message = body.get("message")
    if not message or not isinstance(message, str):
        return False, "Field 'message' is required and must be a non-empty string.", None

    cleaned_message = message.strip()

    if len(cleaned_message) < MIN_QUESTION_LENGTH:
        return False, f"Message must be at least {MIN_QUESTION_LENGTH} characters long.", None

    if len(cleaned_message) > MAX_QUESTION_LENGTH:
        return False, f"Message exceeds maximum allowed length of {MAX_QUESTION_LENGTH} characters.", None

    # Check for prompt injection patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, cleaned_message, re.IGNORECASE):
            return False, "Request rejected: potential prompt injection pattern detected.", None

    session_id = body.get("sessionId")
    if session_id is not None:
        if not isinstance(session_id, str) or len(session_id) > 128:
            return False, "Field 'sessionId' must be a string up to 128 characters.", None

    return True, None, {"message": cleaned_message, "sessionId": session_id}
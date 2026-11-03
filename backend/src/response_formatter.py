"""
backend/src/response_formatter.py - Citation extraction and HTTP response formatting
Why do we need this file?

When your Lambda is called by Amazon API Gateway and Amazon Bedrock returns a raw result, two formatting tasks must happen:

CORS & HTTP Standard Framing (build_http_response):

Web browsers enforce Cross-Origin Resource Sharing (CORS). If your Lambda doesn't return headers like Access-Control-Allow-Origin: *, the browser will block the frontend from reading the answer.
API Gateway expects Lambda to return a Python dictionary with statusCode, headers, and a stringified JSON body.

Citation Cleaning & Deduplication (format_citations):

In Milestone 1, you saw that Bedrock returned 8 separate citation chunks, and many pointed to the exact same file (crashloopbackoff.md) with overlapping sentences.
The frontend shouldn't show 8 redundant duplicate links. format_citations:
Parses the raw Bedrock JSON tree (location.s3Location.uri and content.text).
Deduplicates citations so the user sees clean, distinct references.
Derives a human-friendly document title from the S3 file path (e.g. s3://.../pod-pending.md 
→
→ "Pod Pending").
Truncates long text snippets cleanly with an ellipsis (...) for display in UI cards.
"""

import json
from typing import Dict, Any, List

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key",
}


def build_http_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Wraps body and headers into standard API Gateway Lambda proxy response format."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body)
    }


def format_citations(raw_citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract clean, deduplicated source references and snippets from Bedrock citations."""
    formatted_sources = []
    seen_locations = set()

    for citation in raw_citations:
        for ref in citation.get("retrievedReferences", []):
            location_info = ref.get("location", {})
            s3_uri = location_info.get("s3Location", {}).get("uri", "internal-doc")
            content = ref.get("content", {}).get("text", "").strip()

            # Deduplicate references pointing to same snippet/file
            dedup_key = (s3_uri, content[:80])
            if dedup_key in seen_locations:
                continue
            seen_locations.add(dedup_key)

            # Derive title from filename (e.g., pod-pending.md -> Pod Pending)
            filename = s3_uri.split("/")[-1] if "/" in s3_uri else s3_uri
            title = filename.replace(".md", "").replace("-", " ").title()

            formatted_sources.append({
                "title": title,
                "location": s3_uri,
                "snippet": content[:250] + ("..." if len(content) > 250 else "")
            })

    return formatted_sources
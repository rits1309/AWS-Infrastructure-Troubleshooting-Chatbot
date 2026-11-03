"""
backend/src/kb_service.py - Bedrock Agent Runtime client for Knowledge Base queries
we tested Bedrock using a simple script. In a production Lambda backend, we encapsulate the Bedrock communication into a dedicated service class (BedrockKBService).

This gives us 3 major architectural advantages:

Separation of Concerns: The Lambda handler doesn't need to know boto3 API details or request payload shapes; it just calls service.query(question, session_id).
Lazy Client Initialization & Warm Starts: Instead of creating a new boto3 client on every incoming HTTP request, we initialize the client once during Lambda "cold start". Subsequent requests reuse the open connection, significantly reducing latency.
Structured AWS Error Translation: If Bedrock throws an error (e.g., ThrottlingException, ResourceNotFoundException, or bad permissions), this service catches the AWS ClientError and turns it into clean, descriptive exceptions instead of crashing silently.
"""

import os
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_REGION = os.environ.get("AWS_REGION", "ap-south-1")
DEFAULT_MODEL_ARN = os.environ.get(
    "BEDROCK_MODEL_ARN",
    "arn:aws:bedrock:ap-south-1:713881796636:inference-profile/apac.amazon.nova-lite-v1:0"
)
DEFAULT_KB_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")


class BedrockKBService:
    def __init__(
        self,
        region: str = DEFAULT_REGION,
        kb_id: str = DEFAULT_KB_ID,
        model_arn: str = DEFAULT_MODEL_ARN
    ):
        self.region = region
        self.kb_id = kb_id
        self.model_arn = model_arn
        self._client = None

    @property
    def client(self):
        """Lazy-loaded boto3 bedrock-agent-runtime client."""
        if self._client is None:
            self._client = boto3.client("bedrock-agent-runtime", region_name=self.region)
        return self._client

    def query(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calls retrieve_and_generate on Amazon Bedrock Knowledge Base.
        Returns: {"answer": str, "sessionId": str, "citations": list}
        """
        if not self.kb_id:
            raise ValueError("KNOWLEDGE_BASE_ID is not configured.")

        req_args = {
            "input": {"text": question},
            "retrieveAndGenerateConfiguration": {
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": self.kb_id,
                    "modelArn": self.model_arn
                }
            }
        }

        if session_id:
            req_args["sessionId"] = session_id

        try:
            response = self.client.retrieve_and_generate(**req_args)
            return {
                "answer": response.get("output", {}).get("text", ""),
                "sessionId": response.get("sessionId"),
                "citations": response.get("citations", [])
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "ClientError")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            raise RuntimeError(f"Bedrock API error [{error_code}]: {error_msg}")
        except BotoCoreError as e:
            raise RuntimeError(f"AWS Network/Core error: {str(e)}")
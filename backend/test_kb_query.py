import os
import sys
import argparse
import boto3
from botocore.exceptions import BotoCoreError, ClientError
DEFAULT_KB_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
DEFAULT_MODEL_ARN = os.environ.get(
    "BEDROCK_MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
)
DEFAULT_REGION = os.environ.get("AWS_REGION", "us-east-1")
def query_knowledge_base(question: str, kb_id: str, model_arn: str, region: str):
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    req_args = {
        "input": {"text": question},
        "retrieveAndGenerateConfiguration": {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn
            }
        }
    }
    response = client.retrieve_and_generate(**req_args)
    answer = response.get("output", {}).get("text", "")
    citations = response.get("citations", [])
    sources = []
    for citation in citations:
        for ref in citation.get("retrievedReferences", []):
            uri = ref.get("location", {}).get("s3Location", {}).get("uri", "unknown")
            snippet = ref.get("content", {}).get("text", "")[:180]
            sources.append({"uri": uri, "snippet": snippet})
    return {"answer": answer, "sources": sources}
def main():
    parser = argparse.ArgumentParser(description="Query Bedrock CloudOps KB")
    parser.add_argument("--question", "-q", default="Why are my EKS pods stuck in Pending?")
    parser.add_argument("--kb-id", default=DEFAULT_KB_ID, help="Bedrock Knowledge Base ID")
    parser.add_argument("--model-arn", default=DEFAULT_MODEL_ARN)
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args()
    if not args.kb_id:
        print("[ERROR] Please provide --kb-id <ID> or set $env:KNOWLEDGE_BASE_ID")
        sys.exit(1)
    print(f"\nQuerying Bedrock Knowledge Base ({args.kb_id})...")
    print(f"Question: {args.question}\n")
    try:
        res = query_knowledge_base(args.question, args.kb_id, args.model_arn, args.region)
        print("="*60)
        print("ANSWER:")
        print("="*60)
        print(res["answer"])
        print("\n" + "="*60)
        print("SOURCES / CITATIONS:")
        print("="*60)
        for i, src in enumerate(res["sources"], 1):
            print(f"{i}. Location: {src['uri']}")
            print(f"   Snippet : {src['snippet']}...\n")
    except (BotoCoreError, ClientError) as e:
        print(f"[API ERROR] {e}")
if __name__ == "__main__":
    main()
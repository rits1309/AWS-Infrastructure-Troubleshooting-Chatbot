# Troubleshooting Amazon API Gateway HTTP 503 Service Unavailable

## Overview
Amazon API Gateway returns `HTTP 503 Service Unavailable` when the API Gateway service itself or the upstream integration backend cannot process the incoming HTTP request.

## Symptoms
- Clients receive `HTTP 503 Service Unavailable` or `Endpoint request timed out`.
- CloudWatch metrics `5XXError` spike on the API Gateway stage.

## Possible Causes
1. **Lambda Concurrency Exhaustion:** The AWS account or function has reached its concurrent execution limit (`ConcurrentExecutions` quota exceeded), leading to throttling or 503.
2. **Backend Timeout:** The integration backend exceeded the 29 seconds hard timeout limit on API Gateway.
3. **API Gateway Throttling:** Route or stage steady-state and burst request rate limits exceeded.
4. **VPC Link Integration Failure:** Upstream Network Load Balancer (NLB) or target group is unhealthy.

## Diagnostic Steps

### Step 1: Query API Gateway Logs in CloudWatch
```
fields @timestamp, @message, status, responseLatency, integrationLatency
| filter status = 503
| sort @timestamp desc
| limit 50
```

### Step 2: Check Lambda Concurrency and Throttling Metrics
```bash
aws cloudwatch get-metric-data --metric-data-queries '[
  {"Id": "m1", "MetricStat": {"Metric": {"Namespace": "AWS/Lambda", "MetricName": "Throttles"}}, "Period": 300, "Stat": "Sum"},
  {"Id": "m2", "MetricStat": {"Metric": {"Namespace": "AWS/Lambda", "MetricName": "ConcurrentExecutions"}}, "Period": 300, "Stat": "Maximum"}
]'
```

### Step 3: Check Account Service Quotas
```bash
aws service-quotas get-service-quota --service-code apigateway --quota-code L-CD8A4A0A
```

## Resolution Guidance
- Request a quota increase for AWS Lambda Concurrent Executions in AWS Service Quotas.
- Optimize backend processing time to complete well under 29 seconds.
- Implement exponential backoff with jitter on clients.

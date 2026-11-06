# Troubleshooting AWS IAM AccessDenied Errors

## Overview
AWS Identity and Access Management (IAM) returns `AccessDenied` (HTTP 403) when an explicit or implicit denial occurs in the IAM evaluation logic for an API action requested by an IAM principal.

## Symptoms
- AWS CLI or SDK returns `ClientError: An error occurred (AccessDenied) when calling the <Action> operation`.
- Terraform plan/apply fails with `User: arn:aws:iam::... is not authorized to perform: ... on resource: ...`.
- Encoded authorization failure message in JSON response.

## Possible Causes
1. **Missing Identity-Based Policy:** The IAM User or Role has no policy allowing the specific action and resource.
2. **Explicit Deny Policy:** A matching policy contains `Effect: Deny`, which always overrides any `Allow`.
3. **Permissions Boundary:** A permission boundary attached to the role does not permit the action.
4. **AWS Organizations Service Control Policy (SCP):** The account is under an AWS Organization with an SCP that blocks the action or service in the target AWS Region.
5. **KMS Key Decryption Denial:** Caller can access the S3 object or EBS volume, but lacks `kms:Decrypt` and `kms:GenerateDataKey` permission on the KMS key.

## Diagnostic Steps

### Step 1: Decode Authorization Failure Message
```bash
aws sts decode-authorization-message --encoded-message <encoded-message-string>
```

### Step 2: Verify Active Identity
```bash
aws sts get-caller-identity
```

### Step 3: Check KMS Key Policy
```bash
aws kms get-key-policy --key-id <key-id> --policy-name default
```

### Step 4: Check Organization SCPs
```bash
aws organizations list-policies-for-target --target-id <account-id> --filter SERVICE_CONTROL_POLICY
```

## Resolution Guidance
- Update IAM policy with required action and resource ARN.
- For KMS encrypted S3 buckets, grant `kms:Decrypt` and `kms:GenerateDataKey`.
- Contact Organization administrators if blocked by SCPs.

\# Troubleshooting EKS Pods in ImagePullBackOff or ErrImagePull



\## Overview

`ImagePullBackOff` and `ErrImagePull` mean the `kubelet` failed to pull the specified container image from the container registry (e.g., Amazon ECR, Docker Hub, or GitHub Packages).



\## Symptoms

\- Pod status shows `ImagePullBackOff` or `ErrImagePull`.

\- The Pod never transitions to `Running`.

\- Container status shows `Waiting` with reason `ImagePullBackOff`.



\## Possible Causes

1\. \*\*Invalid Image Tag or Repository Name:\*\* Typo in image repository name or tag does not exist.

2\. \*\*Missing ECR IAM Permissions:\*\* EKS Node IAM role or Pod IRSA role lacks `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, or `ecr:BatchGetImage`.

3\. \*\*Cross-Account ECR Permissions:\*\* Image is stored in another AWS account without an ECR repository policy allowing cross-account pulls.

4\. \*\*VPC Endpoint / Routing Missing:\*\* Worker nodes in private subnets cannot reach the public internet (NAT Gateway down) and ECR Interface VPC Endpoints (`ecr.api`, `ecr.dkr`, and S3 Gateway Endpoint) are missing.

5\. \*\*Private Registry Credentials Missing:\*\* Pulling from Docker Hub or a private registry without `imagePullSecrets` configured.

6\. \*\*Docker Hub Rate Limiting:\*\* Anonymous pull rate limits exceeded (HTTP 429 Too Many Requests).



\## Diagnostic Steps



\### Step 1: Inspect Kubelet Error in Pod Events

```bash

kubectl describe pod <pod-name> -n <namespace>

```

Look at the `Events` section:

\- `repository ... not found` -> Typo or image tag does not exist.

\- `401 Unauthorized` or `403 Forbidden` -> IAM permission issue or missing secret.

\- `dial tcp ... i/o timeout` -> VPC routing, NAT Gateway, or missing VPC endpoints.

\- `toomanyrequests: You have reached your pull rate limit` -> Docker Hub rate limit.



\### Step 2: Verify Image Tag in ECR via AWS CLI

```bash

aws ecr describe-images --repository-name <repo-name> --image-ids imageTag=<tag> --region us-east-1

```



\### Step 3: Check Worker Node IAM Role Permissions

Check that the EKS Node Instance Role has the managed policy attached:

```bash

aws iam list-attached-role-policies --role-name <eks-node-instance-role>

```

Ensure `AmazonEC2ContainerRegistryReadOnly` is attached.



\### Step 4: Verify VPC Endpoints (Private Subnets)

```bash

aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<vpc-id>" --query "VpcEndpoints\[\*].\[ServiceName,State]" --output table

```



\## Safe Diagnostic Commands

```bash

\# List all pods with image pull failures cluster-wide

kubectl get pods -A -o jsonpath='{range .items\[\*]}{.metadata.namespace}{"/"}{.metadata.name}{": "}{.status.containerStatuses\[\*].state.waiting.reason}{"\\n"}{end}' | grep -E "ImagePullBackOff|ErrImagePull"

```



\## Resolution Guidance

\- \*\*Typo/Non-Existent Tag:\*\* Correct image tag in the deployment manifest.

\- \*\*Missing ECR Permissions:\*\* Attach `AmazonEC2ContainerRegistryReadOnly` to the node instance role.

\- \*\*Private Subnets:\*\* Add AWS VPC Endpoints for ECR (`com.amazonaws.us-east-1.ecr.api`, `ecr.dkr`, and S3 Gateway).

\- \*\*External Private Registry:\*\* Create a secret via `kubectl create secret docker-registry` and reference it under `imagePullSecrets`.



\## Escalation

\- Escalate to CI/CD Team if the image build/push pipeline failed.

\- Escalate to Cloud Networking Team if VPC routes or NAT gateways block outbound connectivity.


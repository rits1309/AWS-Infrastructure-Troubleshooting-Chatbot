\# Troubleshooting EKS AWS Load Balancer Controller and Ingress 504 Gateway Timeout



\## Overview

An HTTP 504 Gateway Timeout from an AWS Application Load Balancer (ALB) indicates that the ALB attempted to forward a request to target pods in EKS, but the target pod did not respond within the idle timeout period.



\## Symptoms

\- Ingress URLs return `HTTP 504 Gateway Time-out`.

\- CloudWatch metric `HTTPCode\_ELB\_5XX\_Count` or `TargetResponseTime` spikes.

\- Target group shows target health as `Unhealthy` or requests timing out.



\## Possible Causes

1\. \*\*Pod Response Time Exceeds ALB Timeout:\*\* Backend application takes longer to process requests than the ALB idle timeout (default 60 seconds).

2\. \*\*Security Group Misconfiguration:\*\* The node or pod security group blocks inbound traffic from the ALB security group on the container port.

3\. \*\*Application Thread / Connection Pool Exhaustion:\*\* Backend is deadlocked or blocked on a slow database query.

4\. \*\*AWS Load Balancer Controller Pod Crash:\*\* Controller is not syncing target group registrations.

5\. \*\*Readiness Probe or Pod Readiness Gate Failure:\*\* In IP-target mode, target pods are not marked ready in the ALB target group because readiness gates fail.



\## Diagnostic Steps



\### Step 1: Check Target Group Health in AWS ELB

```bash

aws elbv2 describe-target-health --target-group-arn <target-group-arn>

```

Look for target state `unhealthy` (`Target.Timeout`, `Target.FailedHealthChecks`).



\### Step 2: Check AWS Load Balancer Controller Logs

```bash

kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=100

```



\### Step 3: Verify Security Groups

Ensure worker node / pod security group allows inbound traffic from the ALB security group on the target container port:

```bash

aws ec2 describe-security-groups --group-ids <node-or-pod-sg-id> --query "SecurityGroups\[\*].IpPermissions"

```



\### Step 4: Check Backend Pod Metrics

```bash

kubectl top pods -n <namespace> -l app=<app-name>

kubectl logs -n <namespace> -l app=<app-name> --tail=100

```



\## Safe Diagnostic Commands

```bash

\# Check pod readiness gate status

kubectl get pods -n <namespace> -o jsonpath='{range .items\[\*]}{.metadata.name}{"\\t"}{.status.conditions\[?(@.type=="target-health.elbv2.k8s.aws")].status}{"\\n"}{end}'



\# Test pod response directly from cluster

kubectl run debug-curl --rm -i --tty --image=curlimages/curl -- curl -Iv http://<pod-ip>:<container-port>/healthz

```



\## Resolution Guidance

\- \*\*Increase ALB Idle Timeout:\*\* Add annotation:

&#x20; `alb.ingress.kubernetes.io/load-balancer-attributes: idle\_timeout.timeout\_seconds=120`

\- \*\*Fix Security Groups:\*\* Allow ingress TCP from ALB security group to node/pod port.

\- \*\*Tune Health Checks:\*\* Update `alb.ingress.kubernetes.io/healthcheck-path` to a lightweight endpoint.

\- \*\*Backend Scaling:\*\* Scale pod replicas with Horizontal Pod Autoscaler (HPA) or optimize database query bottlenecks.



\## Escalation

\- Escalate to Backend Development Team if application thread deadlocks or database locks cause latency spikes.

\- Escalate to Network Engineering if VPC transit gateway or route table anomalies are detected.


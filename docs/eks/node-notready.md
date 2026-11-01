\# Troubleshooting EKS Worker Nodes in NotReady State



\## Overview

An EKS worker node enters `NotReady` when the Kubernetes control plane stops receiving heartbeats from the node's `kubelet` daemon past the grace period.



\## Symptoms

\- `kubectl get nodes` shows `STATUS: NotReady`.

\- Pods on the node are marked `Terminating` or evicted after the eviction timeout.

\- New pods fail to schedule on the node.



\## Possible Causes

1\. \*\*Kubelet Stopped or Crashed:\*\* The `kubelet` service crashed due to configuration issues or node OOM.

2\. \*\*Container Runtime Failure (containerd):\*\* `containerd` is stopped or unresponsive.

3\. \*\*Node Resource Pressure:\*\* Extreme MemoryPressure, DiskPressure, or PIDPressure.

4\. \*\*AWS VPC CNI Failure (`aws-node`):\*\* CNI daemonset crashed or ran out of allocatable IP addresses (ENI exhaustion).

5\. \*\*EC2 Instance Status Check Failure:\*\* Hardware impairment or AWS hypervisor issues.

6\. \*\*API Server Communication Loss:\*\* Security group or routing issues between node and EKS control plane (port 443 / 10250).



\## Diagnostic Steps



\### Step 1: Describe Node Conditions

```bash

kubectl describe node <node-name>

```

Look at `Conditions`:

\- `Ready: False` or `Ready: Unknown`

\- `MemoryPressure: True`, `DiskPressure: True`



\### Step 2: Check EC2 Status via AWS CLI

```bash

aws ec2 describe-instance-status --instance-ids <instance-id>

```



\### Step 3: Inspect Kubelet Logs via SSM Session Manager

```bash

aws ssm start-session --target <instance-id>

\# Inside the node:

sudo systemctl status kubelet

sudo journalctl -u kubelet --no-pager -n 100

sudo systemctl status containerd

sudo df -h

```



\### Step 4: Check VPC CNI DaemonSet Logs

```bash

kubectl logs -n kube-system -l k8s-app=aws-node --tail=100

```



\## Safe Diagnostic Commands

```bash

\# List all NotReady nodes

kubectl get nodes --no-headers | grep NotReady



\# Extract node condition messages

kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions\[-1].type,REASON:.status.conditions\[-1].reason,MESSAGE:.status.conditions\[-1].message

```



\## Resolution Guidance

\- \*\*DiskPressure:\*\* Clear unused images (`crictl rmi --prune`) or expand EBS root volume.

\- \*\*Kubelet Crash:\*\* Restart kubelet (`sudo systemctl restart kubelet`).

\- \*\*EC2 Hardware Issue:\*\* Stop and Start the EC2 instance or allow the Auto Scaling Group to replace it.

\- \*\*IP / ENI Exhaustion:\*\* Enable CNI prefix delegation (`ENABLE\_PREFIX\_DELEGATION=true`) on the AWS VPC CNI.



\## Escalation

\- Escalate to AWS Support if EC2 reports hardware impairment (`StatusCheckFailed\_System`).

\- Escalate to Cloud Infrastructure Team if multiple nodes across zones become NotReady simultaneously.


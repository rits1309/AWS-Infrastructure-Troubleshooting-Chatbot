\# EKS Runbook: Pod Stuck in Pending



\## Symptom

An Amazon EKS pod remains in Pending state and does not start.



\## Possible causes

1\. Insufficient CPU or memory on available nodes.

2\. Node selectors or node affinity cannot be satisfied.

3\. Taints and tolerations prevent scheduling.

4\. PersistentVolumeClaim is not bound.

5\. Node provisioning is delayed or failing.

6\. Namespace quota or scheduling constraints.



\## Diagnostic steps



\### 1. Check pod status

```bash

kubectl get pods -n <namespace> -o wide

```



\### 2. Inspect the pod

```bash

kubectl describe pod <pod-name> -n <namespace>

```



Check:

\- Events

\- FailedScheduling

\- Resource requests

\- Node selectors

\- Affinity and tolerations

\- PVC status



\### 3. Review namespace events

```bash

kubectl get events -n <namespace> --sort-by=.lastTimestamp

```



\### 4. Check node capacity and health

```bash

kubectl get nodes

kubectl describe nodes

kubectl top nodes

```



Note: kubectl top requires working metrics support.



\### 5. Check storage

```bash

kubectl get pvc -n <namespace>

```



\## Resolution guidance

\- If CPU or memory is insufficient, inspect requests, allocatable capacity and scaling configuration.

\- If affinity or selectors cannot be satisfied, validate the intended node labels and scheduling rules.

\- If taints block scheduling, verify the intended tolerations.

\- If a PVC is pending, investigate storage class, provisioner and volume events.

\- If autoscaling is expected, investigate the node provisioner's events and logs.



Do not reduce resource requests or change scheduling rules without validating workload requirements.



\## Escalation

Escalate to the EKS/platform owner if the pod remains Pending after diagnostics or if cluster capacity, permissions or provisioning failures require privileged investigation.



\## Evidence to collect

\- Pod description

\- Relevant namespace events

\- Node status

\- PVC status, if applicable

\- Timestamp and namespace




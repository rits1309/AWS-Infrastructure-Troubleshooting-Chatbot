\# Troubleshooting EKS Pods in CrashLoopBackOff



\## Overview

`CrashLoopBackOff` indicates that a container in a Pod starts, fails or crashes, and is repeatedly restarted by the kubelet with an exponential back-off delay.



\## Symptoms

\- `kubectl get pods` displays status `CrashLoopBackOff` or `Error`.

\- Pod `RESTARTS` count increases rapidly.

\- Application endpoints return HTTP 502/503.



\## Possible Causes

1\. \*\*Application Runtime Crash (Exit Code 1 / Non-Zero):\*\* Unhandled exception, syntax error, missing environment variable, or database connection failure.

2\. \*\*Out of Memory - OOMKilled (Exit Code 137):\*\* Container memory usage exceeded `resources.limits.memory`.

3\. \*\*Misconfigured Liveness / Startup Probes:\*\* The liveness probe fails repeatedly before the app finishes initializing, causing kubelet to kill the container.

4\. \*\*Missing Environment Variables, ConfigMaps, or Secrets:\*\* Missing configuration bindings required during container boot.

5\. \*\*Permission Denied (Exit Code 126 / 127):\*\* Executable lacks execute permission (`chmod +x`) or the binary/entrypoint does not exist.



\## Diagnostic Steps



\### Step 1: Check Previous Container Logs

```bash

kubectl logs <pod-name> -n <namespace> --previous

```

If it is a multi-container pod:

```bash

kubectl logs <pod-name> -c <container-name> -n <namespace> --previous

```



\### Step 2: Check Exit Code and Last State

```bash

kubectl describe pod <pod-name> -n <namespace>

```

Look for `Last State` under `Containers`:

\- `Exit Code: 137` -> `Reason: OOMKilled` (Memory limit exceeded).

\- `Exit Code: 1` -> Application runtime exception.

\- `Exit Code: 143` -> SIGTERM (probe failure or graceful shutdown).

\- `Exit Code: 127` -> Command not found.



\### Step 3: Verify ConfigMaps and Secrets

```bash

kubectl get configmap,secret -n <namespace>

```



\## Safe Diagnostic Commands

```bash

\# Extract termination state and exit code directly

kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses\[\*].lastState.terminated}'



\# View last 50 lines of crash logs

kubectl logs <pod-name> -n <namespace> --previous --tail=50

```



\## Resolution Guidance

\- \*\*Exit Code 137 (OOMKilled):\*\* Increase `resources.limits.memory` in the deployment manifest or profile application memory leaks.

\- \*\*Probe Failure:\*\* Increase `initialDelaySeconds` or add a `startupProbe` to accommodate slow app boot times.

\- \*\*Application Crash:\*\* Resolve database credentials, connection strings, or code errors revealed in `--previous` logs.



\## Escalation

\- Escalate to Service Developer if logs point to application code bugs or missing environment configs.

\- Escalate to Platform Lead if system-level OOM killing occurs across multiple unrelated workloads.


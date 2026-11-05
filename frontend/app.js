/**
 * frontend/app.js - CloudOps AI Assistant Client Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatViewport = document.getElementById("chat-viewport");
    const userInput = document.getElementById("user-input");
    const btnSend = document.getElementById("btn-send");
    const btnNewChat = document.getElementById("btn-new-chat");
    const charCounter = document.getElementById("char-counter");
    const promptChips = document.querySelectorAll(".prompt-chip");
    const connectionStatus = document.getElementById("connection-status");

    // Session State
    let currentSessionId = generateSessionId();

    // --------------------------------------------------------------------------
    // Event Listeners
    // --------------------------------------------------------------------------

    // Auto-expand textarea and update char counter
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
        const len = userInput.value.length;
        charCounter.textContent = `${len} / ${CONFIG.MAX_MESSAGE_LENGTH}`;
        charCounter.style.color = len > 950 ? "var(--status-red)" : "var(--text-muted)";
    });

    // Handle Enter to send (Shift + Enter for newline)
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send button click
    btnSend.addEventListener("click", sendMessage);

    // New chat button
    btnNewChat.addEventListener("click", () => {
        currentSessionId = generateSessionId();
        chatViewport.innerHTML = "";
        appendAssistantMessage(
            "New session started. How can I help you troubleshoot your AWS or Kubernetes infrastructure?",
            []
        );
        userInput.value = "";
        charCounter.textContent = `0 / ${CONFIG.MAX_MESSAGE_LENGTH}`;
    });

    // Quick prompt chips
    promptChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            userInput.value = chip.getAttribute("data-prompt");
            userInput.dispatchEvent(new Event("input"));
            userInput.focus();
            sendMessage();
        });
    });

    // --------------------------------------------------------------------------
    // Message Dispatcher
    // --------------------------------------------------------------------------
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Append user bubble
        appendUserMessage(text);
        userInput.value = "";
        userInput.style.height = "auto";
        charCounter.textContent = `0 / ${CONFIG.MAX_MESSAGE_LENGTH}`;
        btnSend.disabled = true;

        // 1. Client-side Validation (matches backend/src/validator.py)
        if (text.length < 3) {
            appendErrorMessage("Message must be at least 3 characters long.");
            btnSend.disabled = false;
            userInput.focus();
            return;
        }

        if (text.length > CONFIG.MAX_MESSAGE_LENGTH) {
            appendErrorMessage(`Message exceeds maximum allowed length of ${CONFIG.MAX_MESSAGE_LENGTH} characters.`);
            btnSend.disabled = false;
            userInput.focus();
            return;
        }

        // Check for prompt injection patterns
        const suspiciousPatterns = [
            /ignore\s+(all\s+)?prior\s+instructions/i,
            /disregard\s+(all\s+)?previous\s+prompts/i,
            /system\s*:\s*you\s+are\s+now/i,
            /reveal\s+(your\s+)?system\s+prompt/i,
            /output\s+(the\s+)?aws\s+root\s+account/i
        ];

        for (const pattern of suspiciousPatterns) {
            if (pattern.test(text)) {
                appendErrorMessage("Request rejected: potential prompt injection pattern detected.");
                btnSend.disabled = false;
                userInput.focus();
                return;
            }
        }

        // Show typing indicator
        const typingElem = showTypingIndicator();
        scrollToBottom();

        try {
            const response = await fetch(CONFIG.API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: jsonStringifySafe({
                    message: text,
                    sessionId: currentSessionId
                })
            });

            removeTypingIndicator(typingElem);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errMessage = errorData.message || `Server returned status ${response.status}`;
                appendErrorMessage(`API Error: ${errMessage}`);
                return;
            }

            const data = await response.json();
            if (data.sessionId) {
                currentSessionId = data.sessionId;
            }

            appendAssistantMessage(data.answer, data.sources || []);

        } catch (networkError) {
            removeTypingIndicator(typingElem);

            if (CONFIG.ENABLE_OFFLINE_FALLBACK) {
                // If API Gateway is not deployed yet or offline, provide simulated grounded response
                const fallback = getSimulatedResponse(text);
                appendAssistantMessage(fallback.answer, fallback.sources);
            } else {
                appendErrorMessage(`Network Error: Could not connect to API Gateway endpoint (${CONFIG.API_URL}).`);
            }
        } finally {
            btnSend.disabled = false;
            scrollToBottom();
            userInput.focus();
        }
    }

    // --------------------------------------------------------------------------
    // Message Rendering & Markdown Parsing
    // --------------------------------------------------------------------------
    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user";
        row.innerHTML = `
            <div class="avatar user-avatar">You</div>
            <div class="message-bubble">${escapeHtml(text)}</div>
        `;
        chatViewport.appendChild(row);
        scrollToBottom();
    }

    function appendAssistantMessage(markdownText, sources = []) {
        const row = document.createElement("div");
        row.className = "message-row assistant";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.innerHTML = renderMarkdown(markdownText);

        // Add citation pills if sources are present
        if (sources && sources.length > 0) {
            const citationsBox = document.createElement("div");
            citationsBox.className = "citations-box";

            const title = document.createElement("div");
            title.className = "citations-title";
            title.textContent = "Verified Source Runbooks";
            citationsBox.appendChild(title);

            const list = document.createElement("div");
            list.className = "citations-list";

            sources.forEach((src) => {
                const pill = document.createElement("span");
                pill.className = "citation-pill";
                pill.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                    <span>${escapeHtml(src.title || "Runbook")}</span>
                `;
                pill.title = `Location: ${src.location}\n\nSnippet:\n${src.snippet}`;
                pill.addEventListener("click", () => {
                    alert(`Runbook Source:\n${src.location}\n\nRetrieved Context:\n${src.snippet}`);
                });
                list.appendChild(pill);
            });

            citationsBox.appendChild(list);
            bubble.appendChild(citationsBox);
        }

        row.innerHTML = `<div class="avatar bot-avatar">AI</div>`;
        row.appendChild(bubble);
        chatViewport.appendChild(row);

        // Attach copy buttons to rendered code blocks
        attachCopyButtons(bubble);
        scrollToBottom();
    }

    function appendErrorMessage(message) {
        const row = document.createElement("div");
        row.className = "message-row assistant";
        row.innerHTML = `
            <div class="avatar bot-avatar" style="border-color: var(--status-red); color: var(--status-red);">!</div>
            <div class="message-bubble" style="border-color: var(--status-red); background-color: rgba(239, 68, 68, 0.1);">
                <p><strong>Incident Investigation Error</strong></p>
                <p style="color: #fca5a5;">${escapeHtml(message)}</p>
            </div>
        `;
        chatViewport.appendChild(row);
        scrollToBottom();
    }

    // --------------------------------------------------------------------------
    // Markdown & Code Block Formatter
    // --------------------------------------------------------------------------
    function renderMarkdown(md) {
        if (!md) return "";

        // 1. Format code blocks (```bash ... ```)
        let html = md.replace(/```([a-zA-Z0-9_\-]+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || "bash";
            return `
                <div class="code-container">
                    <div class="code-header">
                        <span class="code-lang">${language}</span>
                        <button class="btn-copy">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                            <span>Copy</span>
                        </button>
                    </div>
                    <pre><code class="language-${language}">${escapeHtml(code.trim())}</code></pre>
                </div>
            `;
        });

        // 2. Bold text **text**
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // 3. Inline code `text`
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

        // 4. Bullet lists
        html = html.replace(/^\s*[-•]\s+(.*)$/gm, "<li>$1</li>");
        html = html.replace(/(<li>[\s\S]*?<\/li>)/g, "<ul>$1</ul>");

        // 5. Paragraphs
        const paragraphs = html.split(/\n{2,}/);
        return paragraphs.map(p => {
            p = p.trim();
            if (p.startsWith("<div") || p.startsWith("<ul") || p.startsWith("<ol")) {
                return p;
            }
            return `<p>${p.replace(/\n/g, "<br>")}</p>`;
        }).join("");
    }

    function attachCopyButtons(container) {
        container.querySelectorAll(".btn-copy").forEach((btn) => {
            btn.addEventListener("click", () => {
                const codeElem = btn.closest(".code-container").querySelector("code");
                if (codeElem) {
                    navigator.clipboard.writeText(codeElem.textContent).then(() => {
                        const originalHTML = btn.innerHTML;
                        btn.innerHTML = `<span style="color: var(--status-green);">✓ Copied!</span>`;
                        setTimeout(() => {
                            btn.innerHTML = originalHTML;
                        }, 2000);
                    });
                }
            });
        });
    }

    // --------------------------------------------------------------------------
    // Helpers
    // --------------------------------------------------------------------------
    function showTypingIndicator() {
        const row = document.createElement("div");
        row.className = "message-row assistant typing-row";
        row.innerHTML = `
            <div class="avatar bot-avatar">AI</div>
            <div class="message-bubble typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        chatViewport.appendChild(row);
        return row;
    }

    function removeTypingIndicator(elem) {
        if (elem && elem.parentNode) {
            elem.parentNode.removeChild(elem);
        }
    }

    function scrollToBottom() {
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    function generateSessionId() {
        return "session-" + Math.random().toString(36).substring(2, 11) + "-" + Date.now();
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function jsonStringifySafe(obj) {
        return JSON.stringify(obj);
    }

    // Offline simulation for local verification
    function getSimulatedResponse(question) {
        const q = question.toLowerCase();
        
        if (q.includes("pending")) {
            return {
                answer: "Based on the **EKS Pod Pending Runbook**, pods remain in Pending due to:\n\n1. **Insufficient Compute Resources:** Available nodes lack allocatable CPU or Memory to satisfy requests.\n2. **Taints and Tolerations:** Nodes have taints applied that the pod manifest does not tolerate.\n3. **PVC Storage Binding:** PersistentVolumeClaim cannot bind or EBS volume is in a different Availability Zone.\n4. **Provisioner Delay:** Karpenter or Cluster Autoscaler has not yet provisioned a node.\n\nRecommended diagnostic commands:\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl get nodes -o wide\nkubectl get events -n <namespace> --sort-by=.lastTimestamp\n```",
                sources: [
                    {
                        title: "Pod Pending",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/pod-pending.md",
                        snippet: "A Kubernetes Pod remains in the Pending phase when it has been accepted by the API server but one or more containers have not been scheduled."
                    }
                ]
            };
        } else if (q.includes("crash") || q.includes("137") || q.includes("oom")) {
            return {
                answer: "Based on the **EKS CrashLoopBackOff Runbook**:\n\n- **Exit Code 137 (OOMKilled):** The container exceeded its `resources.limits.memory` limit.\n- **Exit Code 1:** Unhandled application runtime exception, syntax error, or database connection failure.\n- **Exit Code 143:** SIGTERM sent by kubelet (often due to failed liveness probe).\n- **Exit Code 127:** Entrypoint binary or executable not found in image.\n\nRecommended diagnostic commands:\n```bash\nkubectl logs <pod-name> -n <namespace> --previous --tail=50\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated}'\n```\nTo resolve OOMKilled, increase `resources.limits.memory` in your deployment manifest.",
                sources: [
                    {
                        title: "Crashloopbackoff",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/crashloopbackoff.md",
                        snippet: "CrashLoopBackOff indicates that a container inside a Kubernetes Pod repeatedly crashes and is restarted with back-off delay."
                    }
                ]
            };
        } else if (q.includes("pull") || q.includes("ecr") || q.includes("image")) {
            return {
                answer: "Based on the **EKS ImagePullBackOff Runbook**, failure to pull container images is typically caused by:\n\n1. **Typo in Image Tag:** The image tag does not exist in Amazon ECR.\n2. **Missing IAM Permissions:** Node instance role or IRSA role lacks `AmazonEC2ContainerRegistryReadOnly`.\n3. **Private Subnet Missing VPC Endpoints:** Worker nodes in private subnets cannot reach ECR without NAT Gateway or ECR VPC Endpoints (`ecr.api`, `ecr.dkr`, and S3 Gateway Endpoint).\n4. **Docker Hub Rate Limits:** Anonymous pull limit exceeded (HTTP 429).\n\nRecommended diagnostic commands:\n```bash\nkubectl describe pod <pod-name> -n <namespace>\naws ecr describe-images --repository-name <repo-name> --image-ids imageTag=<tag>\naws ec2 describe-vpc-endpoints\n```",
                sources: [
                    {
                        title: "Imagepullbackoff",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/imagepullbackoff.md",
                        snippet: "ImagePullBackOff indicates that kubelet failed to pull the specified container image from the container registry."
                    }
                ]
            };
        } else if (q.includes("notready") || q.includes("node") || q.includes("diskpressure")) {
            return {
                answer: "Based on the **EKS Worker Node NotReady Runbook**:\n\n- **Kubelet Crash:** The `kubelet` service stopped posting status heartbeats to the control plane.\n- **Node Resource Pressure:** `DiskPressure: True` or `MemoryPressure: True` on the node.\n- **VPC CNI IP Exhaustion:** The `aws-node` daemonset ran out of allocatable ENI IP addresses.\n\nRecommended diagnostic commands:\n```bash\nkubectl describe node <node-name>\nkubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason\nsudo systemctl status kubelet\n```",
                sources: [
                    {
                        title: "Node Notready",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/node-notready.md",
                        snippet: "An EKS worker node enters NotReady when the control plane stops receiving heartbeats from the kubelet daemon."
                    }
                ]
            };
        } else if (q.includes("504") || q.includes("alb") || q.includes("ingress") || q.includes("timeout")) {
            return {
                answer: "Based on the **EKS ALB Ingress 504 Timeout Runbook**:\n\n1. **Target Response Exceeds Idle Timeout:** Backend application takes longer than ALB idle timeout (default 60s).\n2. **Security Group Misconfiguration:** Node or pod security group does not permit inbound traffic from the ALB security group on container port.\n3. **Failing Target Health Checks:** Pods are failing health checks or pod readiness gates (`target-health.elbv2.k8s.aws`).\n\nRecommended diagnostic commands:\n```bash\naws elbv2 describe-target-health --target-group-arn <target-group-arn>\nkubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=50\n```",
                sources: [
                    {
                        title: "Alb Ingress 504",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/alb-ingress-504.md",
                        snippet: "An HTTP 504 Gateway Timeout from an ALB indicates that the target pod did not respond within the idle timeout period."
                    }
                ]
            };
        } else if (q.includes("accessdenied") || q.includes("iam") || q.includes("403") || q.includes("sts") || q.includes("kms")) {
            return {
                answer: "Based on the **AWS IAM AccessDenied Runbook**:\n\n1. **Missing Identity Policy:** The calling IAM role/user lacks explicit permission for the requested action.\n2. **Explicit Deny or SCP:** An AWS Organizations Service Control Policy (SCP) or permissions boundary blocks the action.\n3. **KMS Decryption Denial:** Caller can access the S3 object/EBS volume, but lacks `kms:Decrypt` and `kms:GenerateDataKey` permissions on the Customer Managed Key (CMK).\n\nRecommended diagnostic commands:\n```bash\naws sts decode-authorization-message --encoded-message <encoded-message-string>\naws sts get-caller-identity\naws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <action>\n```",
                sources: [
                    {
                        title: "Access Denied",
                        location: "s3://cloudops-runbooks-713881796636/docs/iam/access-denied.md",
                        snippet: "AWS IAM returns AccessDenied (HTTP 403) when an explicit or implicit denial occurs in IAM evaluation logic."
                    }
                ]
            };
        } else if (q.includes("503") || q.includes("service unavailable") || q.includes("apigateway")) {
            return {
                answer: "Based on the **API Gateway HTTP 503 Runbook**:\n\n1. **Lambda Concurrency Exhaustion:** Account or function reached `ConcurrentExecutions` quota limit.\n2. **Integration Timeout:** Backend execution exceeded the 29-second hard timeout limit.\n3. **Throttling Quotas:** Steady-state or burst rate limit exceeded on stage or route.\n\nRecommended diagnostic commands:\n```bash\naws cloudwatch get-metric-data --metric-data-queries '[{\"Id\":\"m1\",\"MetricStat\":{\"Metric\":{\"Namespace\":\"AWS/Lambda\",\"MetricName\":\"Throttles\"}},\"Period\":300,\"Stat\":\"Sum\"}]'\naws service-quotas get-service-quota --service-code apigateway --quota-code L-CD8A4A0A\n```",
                sources: [
                    {
                        title: "Http 503",
                        location: "s3://cloudops-runbooks-713881796636/docs/api-gateway/http-503.md",
                        snippet: "Amazon API Gateway returns HTTP 503 when the service or upstream backend cannot process the incoming request."
                    }
                ]
            };
        } else {
            return {
                answer: `I reviewed the operational knowledge base regarding "${question}".\n\nThis assistant is specialized strictly for AWS and Kubernetes infrastructure incident troubleshooting. If this question is out of scope or unrelated to operational runbooks, please consult team documentation.\n\nFor cluster troubleshooting, check recent events:\n\`\`\`bash\nkubectl get events --sort-by=.lastTimestamp\n\`\`\``,
                sources: [
                    {
                        title: "EKS Troubleshooting Guide",
                        location: "s3://cloudops-runbooks-713881796636/docs/eks/",
                        snippet: "General Kubernetes troubleshooting and AWS infrastructure diagnostic steps."
                    }
                ]
            };
        }
    }
});

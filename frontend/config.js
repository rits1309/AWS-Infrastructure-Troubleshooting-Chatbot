/**
 * frontend/config.js - Application Configuration
 *
 * When API Gateway is deployed via Terraform, replace API_BASE_URL with the
 * output `chat_endpoint` value (e.g. https://<api-id>.execute-api.ap-south-1.amazonaws.com/chat)
 */
const CONFIG = {
    // API Gateway /chat endpoint URL
    API_URL: window.API_URL || "https://api.cloudops-assistant.internal/chat",

    // Enable offline simulated responses if API Gateway is not currently reachable
    ENABLE_OFFLINE_FALLBACK: true,

    // Maximum input length enforced by backend validator
    MAX_MESSAGE_LENGTH: 1000
};

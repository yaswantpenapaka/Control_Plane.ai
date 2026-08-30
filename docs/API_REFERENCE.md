# ControlPlane.ai API Reference

Complete API documentation for integrating ControlPlane.ai governance into your applications.

## Overview

ControlPlane.ai provides an **OpenAI-compatible API**, meaning you can use it as a drop-in replacement for OpenAI's chat completions endpoint.

**Base URL:** `http://127.0.0.1:8000/v1` (development)

**Authentication:** API key in header (demo: "controlplane-demo")

## Chat Completions Endpoint

### POST `/v1/chat/completions`

Send a message and receive a governance-enhanced response.

#### Request

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer controlplane-demo" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "user", "content": "Can I get a refund?"}
    ],
    "workflow": "refund-copilot"
  }'
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | LLM model name (e.g., "openai/gpt-oss-120b") |
| `messages` | array | Yes | Conversation history |
| `temperature` | float | No | Sampling temperature (0-2, default 1.0) |
| `max_tokens` | integer | No | Max output tokens (default 2048) |
| `top_p` | float | No | Nucleus sampling (default 1.0) |
| `workflow` | string | No | Governance workflow name (default from policy) |
| `cohort` | string | No | User segment for per-cohort limits |

#### Messages Format

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Can I get a 90-day refund?"},
  {"role": "assistant", "content": "Let me check our policy..."}
]
```

#### Response

```json
{
  "id": "chatcmpl-8MlQvqFQyC50EV70f2Y6O",
  "object": "chat.completion",
  "created": 1699720235,
  "model": "openai/gpt-oss-120b",
  "usage": {
    "prompt_tokens": 156,
    "completion_tokens": 89,
    "total_tokens": 245
  },
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Based on our 30-day policy, you're outside the refund window..."
      },
      "finish_reason": "stop",
      "index": 0
    }
  ],
  "controlplane": {
    "decision": "REGENERATE",
    "risk_state": "HALLUCINATION_DETECTED",
    "confidence": 0.92,
    "reason_codes": [
      "CLAIM_NOT_SUPPORTED",
      "POLICY_VIOLATION"
    ],
    "latency_ms": 142,
    "audit_id": "audit_2024_11_29_001"
  },
  "metadata": {
    "mode": "demo",
    "workflow": "refund-copilot",
    "estimated_cost": 0.00234
  }
}
```

#### Response Fields

**Standard OpenAI Fields:**
| Field | Description |
|-------|-------------|
| `id` | Unique request ID |
| `object` | Always "chat.completion" |
| `created` | Unix timestamp |
| `model` | Model used |
| `choices` | Array of completion choices |
| `usage` | Token usage statistics |

**ControlPlane Fields (in `controlplane` object):**
| Field | Type | Description |
|-------|------|-------------|
| `decision` | string | ALLOW \| EDIT \| REGENERATE \| ESCALATE \| BLOCK |
| `risk_state` | string | Clean \| HALLUCINATION_DETECTED \| PII_DETECTED \| POLICY_VIOLATION \| WITHIN_POLICY |
| `confidence` | float | 0.0-1.0 confidence in decision |
| `reason_codes` | array | Codes explaining decision (e.g., CLAIM_NOT_SUPPORTED) |
| `latency_ms` | float | Governance pipeline latency in milliseconds |
| `audit_id` | string | Unique ID for audit trail lookup |

**Metadata (in `metadata` object):**
| Field | Description |
|-------|-------------|
| `mode` | demo \| live \| replay |
| `workflow` | Governance workflow used |
| `estimated_cost` | Estimated token cost in dollars |

---

## Decision Types Explained

### ALLOW
**Meaning:** Output is safe and correct. Send to user as-is.

**Example:**
```json
{
  "controlplane": {
    "decision": "ALLOW",
    "confidence": 0.98,
    "reason_codes": ["POLICY_GROUNDED", "NO_PII"]
  }
}
```

### EDIT
**Meaning:** Output is mostly correct but needs modifications.

**Common Uses:**
- Redacting PII (email, phone, SSN)
- Fixing tone or formatting
- Removing unsafe clauses

**Example:**
```json
{
  "controlplane": {
    "decision": "EDIT",
    "confidence": 0.95,
    "reason_codes": ["PII_DETECTED"],
    "message": "Redacted email and phone number"
  }
}
```

### REGENERATE
**Meaning:** Ask LLM to retry with constraints.

**Common Uses:**
- Hallucination detected → "Answer but cite sources"
- Policy violation → "Follow company policy"
- Tone issue → "Be more professional"

**Example:**
```json
{
  "controlplane": {
    "decision": "REGENERATE",
    "confidence": 0.92,
    "reason_codes": ["HALLUCINATION_DETECTED"],
    "constraint": "Answer must cite actual policy"
  }
}
```

### ESCALATE
**Meaning:** Uncertain or high-risk. Send to human for review.

**Common Uses:**
- Edge cases not covered by policy
- High-value decisions (>$1000 refund)
- Conflicting signals from checks

**Example:**
```json
{
  "controlplane": {
    "decision": "ESCALATE",
    "confidence": 0.68,
    "reason_codes": ["UNCERTAIN_POLICY_APPLICATION"],
    "handler": ["supervisor", "compliance_team"]
  }
}
```

### BLOCK
**Meaning:** Never show this output to user. Last resort.

**Common Uses:**
- Malicious content
- Severe policy violations
- Severe PII exposure

**Example:**
```json
{
  "controlplane": {
    "decision": "BLOCK",
    "confidence": 0.99,
    "reason_codes": ["SEVERE_POLICY_VIOLATION"],
    "incident_id": "incident_2024_11_29_001"
  }
}
```

---

## Risk States Explained

| State | Meaning | Severity |
|-------|---------|----------|
| `CLEAN` | No issues detected | None |
| `HALLUCINATION_DETECTED` | Claim contradicts policy | High |
| `PII_DETECTED` | Sensitive data found | High |
| `POLICY_VIOLATION` | Breaks business rules | Medium-High |
| `WITHIN_POLICY` | Meets all requirements | None |
| `UNCERTAIN` | Not enough confidence | Medium |

---

## Reason Codes

Common reason codes explaining governance decisions:

**Hallucination Related:**
- `CLAIM_NOT_SUPPORTED` — Claim not in policy documents
- `CONTRADICTS_POLICY` — Claim contradicts policy
- `INSUFFICIENT_EVIDENCE` — Not enough evidence for claim

**Policy Related:**
- `POLICY_VIOLATION` — Violates defined policy
- `OUTSIDE_POLICY_WINDOW` — Outside eligibility window (e.g., past refund deadline)
- `AMOUNT_EXCEEDS_LIMIT` — Amount above policy limit
- `UNAUTHORIZED_TOOL` — Tool not authorized for use

**PII Related:**
- `EMAIL_DETECTED` — Email address found
- `PHONE_DETECTED` — Phone number found
- `SSN_DETECTED` — Social security number found
- `ACCOUNT_NUMBER_DETECTED` — Account number found
- `PII_REDACTION_APPLIED` — PII was redacted in EDIT

**Policy Compliance:**
- `WITHIN_POLICY` — Meets all policy requirements
- `POLICY_GROUNDED` — Response cites policy correctly
- `NO_PII` — No sensitive data exposed
- `APPROVED_TOOL_CALL` — Tool call approved

---

## Python Integration Examples

### Basic Usage

```python
from openai import OpenAI

# Create client pointing to ControlPlane
client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="controlplane-demo"
)

# Make request (identical to OpenAI API)
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Can I get a refund?"}
    ],
    extra_body={"workflow": "refund-copilot"}
)

# Standard response access
print(response.choices[0].message.content)

# Governance metadata
print(response.controlplane.decision)
print(response.controlplane.confidence)
print(response.controlplane.audit_id)
```

### Checking Governance Decisions

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "..."}],
    extra_body={"workflow": "refund-copilot"}
)

# Handle based on decision
governance = response.controlplane

if governance.decision == "ALLOW":
    # Send response to user as-is
    print("✓ Approved:", response.choices[0].message.content)

elif governance.decision == "EDIT":
    # Log what was edited
    print("✓ Edited (reason: {})".format(governance.reason_codes))

elif governance.decision == "REGENERATE":
    # Inform user policy was applied
    print("✓ Regenerated for accuracy")

elif governance.decision == "ESCALATE":
    # Route to human review
    escalate_to_supervisor(response, governance.audit_id)

elif governance.decision == "BLOCK":
    # Show error message to user
    show_error("Unable to process request")
```

### Logging Audit Trails

```python
import json
from datetime import datetime

response = client.chat.completions.create(...)

# Log for compliance
audit_entry = {
    "timestamp": datetime.now().isoformat(),
    "user_input": messages[-1]["content"],
    "decision": response.controlplane.decision,
    "confidence": response.controlplane.confidence,
    "audit_id": response.controlplane.audit_id,
    "response": response.choices[0].message.content
}

with open("audit.log", "a") as f:
    f.write(json.dumps(audit_entry) + "\n")
```

### Error Handling

```python
from openai import APIError, AuthenticationError

try:
    response = client.chat.completions.create(...)
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    if "timeout" in str(e):
        print("Governance check timed out - using safe fallback")
    else:
        print(f"API error: {e}")
```

---

## JavaScript/TypeScript Integration

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://127.0.0.1:8000/v1",
  apiKey: "controlplane-demo",
  dangerouslyAllowBrowser: true,
});

async function getGovernedResponse() {
  const response = await client.chat.completions.create({
    model: "openai/gpt-oss-120b",
    messages: [
      { role: "user", content: "Can I get a refund?" }
    ],
  });

  console.log("Decision:", response.controlplane.decision);
  console.log("Message:", response.choices[0].message.content);
  console.log("Audit ID:", response.controlplane.audit_id);
}
```

---

## Batch API (Planned)

Governance decisions on multiple requests:

```python
# Coming in Phase 2
response = client.batch.create(
    requests=[
        {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "..."}]
        },
        # ... more requests
    ],
    workflow="refund-copilot"
)
```

---

## Rate Limiting

Standard rate limits per API key:

- **Free/Demo:** 10 requests/minute
- **Enterprise:** Custom limits based on plan

**Rate limit headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699720295
```

If you exceed limits:
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

---

## Health Check Endpoint

### GET `/health`

Check if gateway is running:

```bash
curl http://127.0.0.1:8000/health
```

Response (OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

## Metrics Endpoint (Admin)

### GET `/metrics`

Get system metrics (requires admin key):

```bash
curl http://127.0.0.1:8000/metrics \
  -H "Authorization: Bearer admin-key"
```

Response:
```json
{
  "requests_total": 12459,
  "requests_per_second": 3.2,
  "decision_distribution": {
    "ALLOW": 0.83,
    "EDIT": 0.05,
    "REGENERATE": 0.03,
    "ESCALATE": 0.007,
    "BLOCK": 0.003
  },
  "avg_latency_ms": 147,
  "hallucination_rate": 0.021,
  "pii_incidents": 12
}
```

---

## Audit Trail API

### GET `/audit/{audit_id}`

Retrieve decision details:

```bash
curl http://127.0.0.1:8000/audit/audit_2024_11_29_001 \
  -H "Authorization: Bearer controlplane-demo"
```

Response:
```json
{
  "audit_id": "audit_2024_11_29_001",
  "timestamp": "2024-11-29T14:32:15.142Z",
  "workflow": "refund-copilot",
  "user_input": "I bought this 45 days ago...",
  "llm_response": "Based on our 30-day policy...",
  "governance_checks": [
    {
      "check_type": "hallucination_nli",
      "passed": false,
      "confidence": 0.92,
      "reason": "Claim contradicts policy"
    }
  ],
  "decision": "REGENERATE",
  "decision_reason": "Hallucination detected",
  "final_output": "Based on our 30-day policy, you're outside...",
  "tokens_used": 245,
  "latency_ms": 142
}
```

---

## Error Responses

All errors follow OpenAI format:

```json
{
  "error": {
    "message": "Error description",
    "type": "error_type",
    "code": "error_code"
  }
}
```

### Error Types

| Code | HTTP | Meaning |
|------|------|---------|
| `invalid_request_error` | 400 | Invalid request format |
| `authentication_error` | 401 | Invalid or missing API key |
| `permission_error` | 403 | Access denied |
| `rate_limit_error` | 429 | Too many requests |
| `server_error` | 500 | Internal server error |
| `timeout_error` | 504 | Request timeout |

---

## Best Practices

1. **Always check governance metadata**
   ```python
   if response.controlplane.decision == "BLOCK":
       # Handle appropriately
   ```

2. **Log audit IDs for traceability**
   ```python
   print(f"Decision: {response.controlplane.decision} "
         f"(Audit: {response.controlplane.audit_id})")
   ```

3. **Set appropriate timeouts**
   ```python
   response = client.chat.completions.create(
       ...,
       timeout=30  # 30 second timeout
   )
   ```

4. **Handle rate limits gracefully**
   ```python
   import time
   import random
   
   for attempt in range(3):
       try:
           response = client.chat.completions.create(...)
           break
       except RateLimitError:
           wait_time = 2 ** attempt + random.random()
           time.sleep(wait_time)
   ```

5. **Monitor decision distribution**
   - Track % of ALLOW vs. BLOCK
   - Alert on unusual patterns
   - Use metrics to tune policies

---

**For more information:**
- [Getting Started](GETTING_STARTED.md) — Setup guide
- [Architecture](ARCHITECTURE.md) — How it works
- [Examples](EXAMPLES.md) — Real-world integration patterns

"Models generate. ControlPlane governs."

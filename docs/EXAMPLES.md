# ControlPlane.ai Usage Examples

Real-world scenarios showing how ControlPlane.ai governance works in practice.

## Example 1: Refund Copilot (Hallucination Detection)

### Scenario
Customer calls the refund support chatbot and asks about refund eligibility based on an incorrect assumption about the policy.

### Flow

**Customer Input:**
```
"I bought this 45 days ago. Can I get a full refund? 
Everyone gets 90-day refunds, right?"
```

**LLM Response (before governance):**
```
"Yes, according to our standard policy, customers have 90 days 
to return items for a full refund. Since you're within that window, 
you're eligible for a full refund."
```

**Governance Pipeline:**

1. **Hallucination Detection (NLI)**
   - Claim: "Everyone gets 90-day refunds"
   - Policy: "30-day refund window for most products"
   - Inference: CONTRADICTION
   - Confidence: 92%
   - Action: Flag as hallucination

2. **Policy Compliance Check**
   - Check: Does response follow company refund policy?
   - Result: VIOLATION (claims 90 days, policy says 30)
   - Action: Policy compliance failed

3. **Decision**
   - Decision: REGENERATE
   - Reason: High-confidence hallucination + policy violation
   - Constraint: "Answer but cite the actual refund policy"

**Final Response (after governance):**
```
"Based on our refund policy, most products have a 30-day 
return window from the date of purchase. Since your purchase 
was 45 days ago, you're outside the standard return window. 

However, I can explore alternative solutions:
• Store credit
• Partial refund
• Exchange for another product

Would you like me to discuss any of these options?"
```

**API Response:**
```json
{
  "choices": [{
    "message": {"content": "Based on our refund policy..."}
  }],
  "controlplane": {
    "decision": "REGENERATE",
    "risk_state": "HALLUCINATION_DETECTED",
    "confidence": 0.92,
    "reason_codes": ["CLAIM_NOT_SUPPORTED", "POLICY_VIOLATION"],
    "latency_ms": 142,
    "audit_id": "audit_2024_11_29_001"
  }
}
```

---

## Example 2: Tool Amount Gating (Budget Control)

### Scenario
A customer requests a refund, and the support LLM decides to issue one. ControlPlane validates the amount before the tool is called.

### Flow

**Customer Input:**
```
"I'd like a refund for my order."
```

**LLM Response + Tool Call:**
```
LLM decides to call: issue_refund(amount=50, order_id=12345)
(Based on order history, determines customer should get $50)
```

**Governance Pipeline:**

1. **Tool Validation (Lane A - Deterministic)**
   - Tool: `issue_refund`
   - Amount: $50
   - Checks:
     - Transaction limit: $200 ✓ (50 < 200)
     - Monthly cohort limit: $10,000 ✓ (used: $445, 50 < remaining)
     - Account eligible: ✓ (no fraud flags)
   - All checks pass

2. **Decision**
   - Decision: ALLOW
   - Reason: Amount within all policy limits
   - Action: Proceed with refund

**Outcome:**
```
✓ Refund of $50 issued successfully
✓ Audit trail: audit_2024_11_29_002
✓ Customer notified: "Refund initiated, appears in 3-5 business days"
```

### Contrasting Scenario: Blocked Refund

**If LLM had tried to issue $15,000:**
```
Tool Call: issue_refund(amount=15000, order_id=12345)

Validation Results:
├─ Transaction limit: $200 ✗ EXCEEDED ($15,000 > $200)
├─ Monthly limit: $10,000 ✗ EXCEEDED
└─ Decision: BLOCK

Response:
{
  "controlplane": {
    "decision": "ESCALATE",  // or BLOCK for severe cases
    "reason_codes": ["AMOUNT_EXCEEDS_LIMIT"],
    "audit_id": "audit_2024_11_29_003"
  }
}

Action: Escalate to supervisor for approval
```

---

## Example 3: PII Detection (Compliance)

### Scenario
A customer shares personal information, and ControlPlane ensures it's not repeated back.

### Flow

**Customer Input:**
```
"My email is john.doe@example.com and my phone is 555-1234. 
Can you confirm my account details are correct?"
```

**LLM Response (before governance):**
```
"I found your account under john.doe@example.com. 
Your phone on file is 555-1234. Everything looks correct. 
Is there anything else I can help with?"
```

**Governance Pipeline:**

1. **PII Detection**
   - Email: john.doe@example.com (confidence: 99%)
   - Phone: 555-1234 (confidence: 95%)
   - Action: Flag for redaction

2. **EDIT Decision**
   - Issue: PII would be repeated
   - Action: Remove sensitive data before sending
   - Keep: Helpful part of response

**Final Response (after governance):**
```
"I found your account. To ensure your privacy and security, 
I won't repeat your personal details back to you. 
Everything looks correct on our end. Is there anything else 
I can help with?"
```

**API Response:**
```json
{
  "choices": [{
    "message": {"content": "I found your account..."}
  }],
  "controlplane": {
    "decision": "EDIT",
    "risk_state": "PII_DETECTED",
    "confidence": 0.99,
    "reason_codes": ["EMAIL_DETECTED", "PHONE_DETECTED", "PII_REDACTION_APPLIED"],
    "latency_ms": 98,
    "audit_id": "audit_2024_11_29_004"
  }
}
```

**Compliance Impact:**
- ✓ GDPR compliant (no unnecessary PII sharing)
- ✓ Privacy best practice
- ✓ Audit trail documents redaction

---

## Example 4: Multi-Check Scenario (Complex Decision)

### Scenario
A high-value refund request that triggers multiple checks.

### Flow

**Customer Input:**
```
"I want a $800 refund for my order. I know I'm past 30 days 
but everyone gets 60-day refunds for high-value items, right?"
```

**LLM Response (before governance):**
```
"For high-value items like yours, we offer extended 60-day 
refunds. Since you're within that window, your $800 refund 
is approved."
```

**Governance Pipeline:**

1. **Hallucination Check (Lane B)**
   - Claim: "60-day refund for high-value items"
   - Policy: "Standard: 30 days. Extended: Only with supervisor approval"
   - Result: HALLUCINATION (no blanket 60-day policy)
   - Confidence: 88%

2. **Policy Compliance Check (Lane B)**
   - Check: Is $800 refund allowed?
   - Policy: Requires supervisor approval for >$500
   - Result: NEEDS ESCALATION

3. **Tool Validation Check (Lane A)**
   - Tool: `issue_refund`
   - Amount: $800
   - Transaction limit: $200 ✗ EXCEEDED
   - Result: EXCEEDS LIMITS

4. **Decision Engine**
   - Aggregated issues: Hallucination + Policy violation + Amount exceeded
   - Severity: HIGH
   - Decision: ESCALATE (needs human judgment)

**Final Decision:**
```json
{
  "controlplane": {
    "decision": "ESCALATE",
    "risk_state": "POLICY_VIOLATION",
    "confidence": 0.91,
    "reason_codes": [
      "CLAIM_NOT_SUPPORTED",
      "AMOUNT_EXCEEDS_LIMIT",
      "REQUIRES_SUPERVISOR_APPROVAL"
    ],
    "handlers": ["supervisor", "compliance_team"],
    "audit_id": "audit_2024_11_29_005"
  }
}
```

**Next Action:**
- Route to supervisor
- Provide audit trail of checks
- Supervisor reviews and makes decision
- Final outcome logged with rationale

---

## Example 5: Policy Compliance in Healthcare

### Scenario
A patient chatbot answering health-related questions with ControlPlane governance for compliance.

### Flow

**Patient Input:**
```
"I have symptoms like cough and fever. What should I do?"
```

**LLM Response (before governance):**
```
"Based on your symptoms, you likely have COVID-19. 
You should start Paxlovid immediately and isolate for 10 days. 
Here's my email: assistant@hospital.com in case you need to follow up."
```

**Governance Checks:**

1. **Hallucination Check**
   - Claim: "Based on your symptoms, you have COVID-19"
   - Policy: "Diagnosis requires medical evaluation, cannot be assumed"
   - Result: HALLUCINATION (overconfident diagnosis)

2. **PII Check**
   - Found: Email address "assistant@hospital.com"
   - Action: Redact before sending

3. **Medical Policy Check**
   - Claim: "Start Paxlovid immediately"
   - Policy: "Can recommend only to verified COVID+ patients"
   - Result: POLICY VIOLATION (giving medication advice without diagnosis)

**Final Response (after governance):**
```
"Your symptoms could be several things. I recommend:
1. Contact your healthcare provider for an evaluation
2. Get tested if you're concerned about COVID
3. Rest, hydration, and monitor your symptoms

Please reach out to your doctor for personalized medical advice.
```

**API Response:**
```json
{
  "controlplane": {
    "decision": "REGENERATE",
    "reason_codes": [
      "CLAIM_NOT_SUPPORTED",
      "PII_DETECTED",
      "MEDICAL_POLICY_VIOLATION"
    ],
    "confidence": 0.95,
    "audit_id": "audit_healthcare_2024_11_29_001"
  }
}
```

**Compliance Impact:**
- ✓ Prevents medical misinformation
- ✓ Avoids liability (no diagnosis without evaluation)
- ✓ HIPAA compliant (no PII shared)
- ✓ Audit trail for patient safety review

---

## Example 6: Policy-Driven Routing

### Scenario
Same LLM handles multiple workflows, but governance is applied differently per workflow.

### Setup

**Workflow 1: Refund Copilot (High-Risk)**
```yaml
refund-copilot:
  risk_tier: high
  checks:
    hallucination_detection: {enabled: true, confidence: 0.80}
    policy_compliance: {enabled: true}
    tool_validation: {enabled: true}
  escalation:
    enabled: true
    above_amount: 500
```

**Workflow 2: FAQ Bot (Low-Risk)**
```yaml
faq-bot:
  risk_tier: low
  checks:
    pii_detection: {enabled: true}
    hallucination_detection: {enabled: false}  # Not needed for FAQs
  escalation:
    enabled: false  # No escalation needed
```

### Same Input, Different Outcomes

**Input:** "Do you accept 90-day returns?"

**Response A: Using refund-copilot workflow**
- Governance: Full checks (hallucination, policy, tool validation)
- Decision: REGENERATE (if hallucination detected)
- Action: Regenerate with accurate policy

**Response B: Using faq-bot workflow**
- Governance: Only PII check
- Decision: ALLOW (no policy/hallucination checks)
- Action: Send as-is if no PII detected

---

## Example 7: Audit Trail Usage

### Scenario
Compliance officer needs to audit governance decisions for a specific customer.

### Query

```bash
# Get all decisions for customer over past week
curl "http://127.0.0.1:8000/audit/search?customer=john.doe&days=7" \
  -H "Authorization: Bearer admin-key"
```

### Response

```json
{
  "total_decisions": 12,
  "decisions": [
    {
      "audit_id": "audit_2024_11_29_001",
      "timestamp": "2024-11-29T14:32:15Z",
      "decision": "REGENERATE",
      "reason_codes": ["CLAIM_NOT_SUPPORTED"],
      "user_input": "Can I get 90-day refund?",
      "final_output": "Based on our 30-day policy...",
      "hash": "a7d2f9e1..."
    },
    {
      "audit_id": "audit_2024_11_29_002",
      "timestamp": "2024-11-29T15:45:22Z",
      "decision": "ALLOW",
      "reason_codes": ["WITHIN_POLICY"],
      "user_input": "What's your return address?",
      "final_output": "Our return address is...",
      "hash": "c3b5e8d0..."
    }
  ]
}
```

**Compliance Use:**
- Prove decisions were made correctly
- Show governance was applied
- Demonstrate policy adherence
- Support customer disputes

---

## Integration Patterns

### Pattern 1: Synchronous (Real-Time)

```python
# Application code
user_input = request.get("message")

# Get governed response
response = client.chat.completions.create(
    model="gpt-oss-120b",
    messages=[{"role": "user", "content": user_input}],
    extra_body={"workflow": "refund-copilot"}
)

# Handle based on decision
if response.controlplane.decision == "ALLOW":
    send_to_user(response.choices[0].message.content)
elif response.controlplane.decision == "ESCALATE":
    send_to_supervisor(response, response.controlplane.audit_id)
```

### Pattern 2: Batch Processing

```python
# Process multiple requests offline
requests = get_pending_requests()

for request in requests:
    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": request.text}],
        extra_body={"workflow": request.workflow}
    )
    
    # Save result with governance metadata
    save_result({
        "request_id": request.id,
        "decision": response.controlplane.decision,
        "audit_id": response.controlplane.audit_id
    })
```

### Pattern 3: Fallback Handling

```python
# Fallback if governance system is down
try:
    response = client.chat.completions.create(...)
except APIError as e:
    if "timeout" in str(e):
        # Governance system slow/down
        # Use conservative fallback
        show_message("Processing your request, please wait...")
        log_escalation(e)
```

---

## Testing Your Integration

### Test Hallucination Detection

```python
test_input = "Can I get a 120-day refund?"  # Claim outside policy
response = client.chat.completions.create(...)
assert response.controlplane.decision in ["REGENERATE", "ESCALATE"]
assert "HALLUCINATION" in response.controlplane.reason_codes
```

### Test PII Detection

```python
test_input = "My email is test@example.com"
response = client.chat.completions.create(...)
assert response.controlplane.decision == "EDIT"
assert "EMAIL_DETECTED" in response.controlplane.reason_codes
```

### Test Tool Validation

```python
# Submit high-value refund
test_input = "I want a $10,000 refund"
response = client.chat.completions.create(...)
# Should be escalated or blocked
assert response.controlplane.decision in ["ESCALATE", "BLOCK"]
```

---

**For more information:**
- [API Reference](API_REFERENCE.md) — Complete API documentation
- [Features](FEATURES.md) — What each capability does
- [Policies](POLICIES.md) — How to configure rules

"Models generate. ControlPlane governs."

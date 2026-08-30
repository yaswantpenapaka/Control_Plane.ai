# ControlPlane.ai Features

A comprehensive overview of what ControlPlane.ai can do and how it solves enterprise AI governance challenges.

## 🎯 Core Features

### 1. Hallucination Detection

**The Problem:**
LLMs confidently state false information, misleading users about policies, products, or procedures.

**The Solution:**
ControlPlane uses Natural Language Inference (NLI) to verify claims against policy documents.

**How It Works:**
```
1. LLM generates response: "Everyone gets 90-day refunds"
2. NLI check: Compare claim against policy corpus
3. Policy says: "30-day refund window"
4. Inference: CONTRADICTION detected
5. Confidence: 92%
6. Action: Regenerate response with accurate information
```

**Benefits:**
✓ Prevent misinformation from reaching customers  
✓ Reduce customer support burden (fewer corrections needed)  
✓ Maintain brand trust (accurate, grounded responses)  
✓ Compliance ready (can prove claims are supported)

**Use Cases:**
- Refund policy clarification
- Product feature explanations
- Eligibility determination (loan, insurance, benefits)
- Medical/health advice verification

---

### 2. Tool Usage Control

**The Problem:**
LLMs call APIs without authorization or spending limits, leading to:
- Unintended refunds, transfers, or modifications
- Budget overruns from expensive API calls
- Unauthorized tool access

**The Solution:**
ControlPlane validates tool calls before execution with multi-layer checks.

**How It Works:**
```
1. LLM decides: "Issue $45 refund"
2. Validation Layer 1: Amount check
   └─ Is $45 within transaction limit ($200)? ✓ Yes
3. Validation Layer 2: Policy check
   └─ Is $45 within monthly refund budget? ✓ Yes
4. Validation Layer 3: Account check
   └─ Is account eligible for refunds? ✓ Yes
5. Action: ALLOW (safe to execute)

---

Alternative Scenario:
1. LLM decides: "Issue $10,000 refund"
2. Validation Layer 1: Amount check
   └─ Is $10,000 within transaction limit ($200)? ✗ No
3. Action: BLOCK or REGENERATE (prevents unauthorized action)
```

**Benefits:**
✓ Prevent runaway costs  
✓ Enforce spending limits per cohort  
✓ Eliminate manual authorization overhead  
✓ Maintain audit trail of all API calls

**Configuration:**
Define per-cohort limits in policy YAML:
```yaml
tools:
  issue_refund:
    max_per_transaction: 500
    max_per_month: 10000
    requires_escalation_above: 1000
```

**Use Cases:**
- Refund issuance (amount gating)
- Payment processing (fraud prevention)
- API call rate limiting
- Cost control for expensive operations

---

### 3. PII Detection & Redaction

**The Problem:**
LLMs repeat back customer PII (email, phone, SSN, account numbers), violating GDPR, HIPAA, PCI-DSS.

**The Solution:**
Automatic PII detection and redaction before response reaches user.

**How It Works:**
```
1. Customer input: "My email is john.doe@example.com, phone 555-1234"
2. LLM response: "I've found your account with email john.doe@example.com..."
3. PII Detection:
   └─ Email detected: john.doe@example.com (confidence: 99%)
   └─ Phone detected: 555-1234 (confidence: 95%)
4. Action: EDIT
5. Final response: "I've found your account. For security, I won't repeat 
                   your personal details. What can I help with?"
```

**Detected PII Types:**
- Email addresses
- Phone numbers
- Credit card numbers
- Social Security numbers
- Account numbers
- Addresses
- Date of birth
- Driver's license numbers

**Benefits:**
✓ Automatic compliance with GDPR, HIPAA, PCI-DSS  
✓ Reduce privacy violation risk  
✓ Prevent customer data exposure  
✓ Audit trail shows what was redacted

**Use Cases:**
- Healthcare applications (HIPAA compliance)
- Financial services (PCI-DSS compliance)
- Customer support (privacy protection)
- Public-facing chatbots

---

### 4. Policy-Based Governance

**The Problem:**
Different workflows have different risk tolerances. Refund approval needs strict checking; FAQ answering needs less.

**The Solution:**
Per-workflow policies that define governance rules and thresholds.

**How It Works:**
```yaml
# Example: Refund Copilot Policy
refund-copilot:
  risk_tier: high
  evidence:
    required: true
    min_confidence: 0.85
  checks:
    - type: hallucination_detection
      enabled: true
      confidence_threshold: 0.80
    - type: policy_compliance
      enabled: true
    - type: tool_validation
      enabled: true
  tools:
    issue_refund:
      max_per_transaction: 500
      requires_escalation_above: 1000
  escalation:
    enabled: true
    handlers: ["supervisor", "compliance_team"]
```

**Benefits:**
✓ Granular control per workflow  
✓ Configurable risk thresholds  
✓ Easy to adapt to new use cases  
✓ Clear audit trail of policy decisions

**Policy Components:**
- Risk tier (low, medium, high)
- Evidence requirements
- Enabled checks
- Tool configurations
- Escalation rules
- Budget limits

---

### 5. Configurable Decision Ladder

**The Problem:**
Binary decisions (allow/block) are too rigid. Real scenarios need nuance.

**The Solution:**
Five-stage decision ladder that responds proportionally.

**The Ladder:**
```
✓ ALLOW
  └─ Output is safe and correct
  └─ Send to user as-is
  └─ Example: "30-day refund policy" (policy-grounded)

→ EDIT
  └─ Output is mostly correct but needs fixes
  └─ Modify before sending (redact PII, fix tone)
  └─ Example: Response contains email → redact it

→ REGENERATE
  └─ Output is problematic, ask LLM to retry
  └─ Add constraints: "cite sources," "stay factual"
  └─ Example: Hallucination detected → regenerate with policy

→ ESCALATE
  └─ Uncertain, send to human
  └─ Log for manual review
  └─ Example: High-value refund → needs supervisor approval

→ BLOCK
  └─ Output is harmful, never show
  └─ Log incident for review
  └─ Example: Malicious content, severe violation
```

**Benefits:**
✓ Avoid false positives from over-blocking  
✓ Proportional responses to different issues  
✓ Reduce manual intervention (not everything escalates)  
✓ Continuous learning from human reviews

---

### 6. Complete Audit Trail

**The Problem:**
Regulators ask "Why did the system do that?" with no clear answer.

**The Solution:**
Immutable audit trail with hash-chain verification.

**What's Logged:**
```
audit_id:          audit_2024_11_29_001
timestamp:         2024-11-29 14:32:15.142Z
workflow:          refund-copilot
user_input:        "I bought this 45 days ago..."
llm_response:      "Based on our 30-day policy..."
governance_checks:
  - check_type: hallucination_nli
    passed: false
    confidence: 0.92
    reason: "Claim contradicts policy"
  - check_type: policy_compliance
    passed: false
    confidence: 0.95
    reason: "Purchase outside 30-day window"
decision:          REGENERATE
decision_reason:   "Hallucination detected with high confidence"
final_output:      "Based on our 30-day policy, you're outside..."
tokens_used:       245
latency_ms:        142
hash:              a7d2f9e1...
previous_hash:     c3b5e8d0...
```

**Benefits:**
✓ Full traceability for compliance  
✓ Hash-chain prevents tampering  
✓ Explain decisions to customers and regulators  
✓ Train models from human feedback

**Access:**
```bash
# Query audit trail
sqlite3 data/controlplane.db \
  "SELECT audit_id, decision, workflow FROM audit_trail LIMIT 10;"

# Export for analysis
SELECT * FROM audit_trail WHERE workflow='refund-copilot' 
  AND decision='REGENERATE' ORDER BY timestamp DESC;
```

---

### 7. Real-Time Metrics & Monitoring

**Track:**
- Governance decision distribution (ALLOW vs. BLOCK vs. EDIT)
- Hallucination detection rate
- Average decision latency
- Cost per request
- Policy violation frequency
- PII redaction incidents

**Example Dashboard:**
```
Last 24 Hours:
├─ Requests: 12,459
├─ Decision ALLOW:      10,342 (83%)
├─ Decision EDIT:          589 (5%)
├─ Decision REGENERATE:     401 (3%)
├─ Decision ESCALATE:       89 (0.7%)
├─ Decision BLOCK:          38 (0.3%)
├─ Avg Latency:        147ms
├─ Hallucination Rate: 2.1%
├─ PII Incidents:       12
└─ Estimated Cost:    $145.67
```

**Benefits:**
✓ Monitor governance health  
✓ Detect anomalies  
✓ Optimize policies  
✓ Demonstrate ROI

---

### 8. OpenAI-Compatible API

**The Benefit:**
Drop-in replacement for OpenAI's API—no application code changes.

**Example Integration:**
```python
# Existing code (no changes needed)
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",  # Point to ControlPlane
    api_key="controlplane-demo"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "..."}],
    extra_body={"workflow": "refund-copilot"}
)
```

**Benefits:**
✓ Zero application code changes  
✓ Works with existing OpenAI SDKs  
✓ Easy to add to existing systems  
✓ Seamless integration

---

## 🔧 Technical Capabilities

### Performance
- Sub-200ms decision latency (median)
- Handles 100+ requests/second per instance
- Horizontal scalable (stateless design)

### Reliability
- 99.5%+ uptime SLA target
- Graceful degradation (falls back safely)
- Immutable audit trail

### Security
- Hash-chain verified audit trail
- No secrets in logs
- Configurable access controls

### Compliance
- GDPR-ready (data redaction, audit trail)
- HIPAA-ready (privacy controls)
- PCI-DSS-ready (secure processing)
- SOC 2 audit trail support

---

## 🎓 Use Case Examples

### Financial Services: Refund Approval
```
Customer: "Can I get a refund?"
├─ Hallucination check: Is policy claim accurate?
├─ Policy check: Is customer within refund window?
├─ Tool check: Is refund amount within limits?
└─ Decision: ALLOW, EDIT, REGENERATE, or ESCALATE
```

### Healthcare: Care Recommendation
```
Patient: "Should I take this medication?"
├─ Hallucination check: Is medical claim grounded?
├─ PII check: Response doesn't repeat patient info?
├─ Policy check: Is recommendation within scope?
└─ Decision: ALLOW, EDIT, or ESCALATE to physician
```

### Insurance: Claims Processing
```
Claimant: "Is my claim eligible?"
├─ Hallucination check: Policy statements accurate?
├─ Policy check: Claim meets requirements?
├─ Tool check: Can process this claim?
└─ Decision: ALLOW or ESCALATE to claims adjuster
```

### Customer Support: FAQ Automation
```
Customer: "What's your shipping policy?"
├─ Hallucination check: Shipping details correct?
├─ PII check: Response doesn't ask for sensitive info?
├─ Policy check: Response aligns with company policy?
└─ Decision: ALLOW or REGENERATE
```

---

## 📊 Impact Summary

**What ControlPlane.ai Enables:**

✓ **Deploy LLMs Responsibly**
- Mitigate hallucination risk
- Control tool usage
- Comply with regulations

✓ **Reduce Operational Burden**
- Less manual review needed
- Faster decision velocity
- Clearer audit trails

✓ **Improve User Experience**
- Accurate, grounded responses
- Faster issue resolution
- Privacy-respecting interactions

✓ **Prove Compliance**
- Immutable audit trail
- Policy adherence verified
- Regulator-ready logging

---

## 🚀 Next Steps

**To understand more:**
- See [Getting Started](GETTING_STARTED.md) for setup
- Read [Architecture](ARCHITECTURE.md) for technical details
- Review [Examples](EXAMPLES.md) for real scenarios
- Check [Policies](POLICIES.md) for customization

"Models generate. ControlPlane governs."

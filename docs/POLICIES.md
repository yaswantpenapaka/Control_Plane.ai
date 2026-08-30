# Policy Configuration Guide

How to define, configure, and manage governance policies in ControlPlane.ai.

## Policy Basics

Policies are YAML files that define governance rules for specific workflows.

**File Location:** `policy/workflows/`
**Format:** YAML
**Example:** `policy/workflows/refund-copilot.yaml`

---

## Policy Structure

### Complete Example

```yaml
# Policy name (used in API calls)
refund-copilot:
  # Risk classification (low, medium, high)
  risk_tier: high
  
  # Evidence requirements for NLI checks
  evidence:
    required: true                    # Require evidence for claims?
    min_confidence: 0.85              # Minimum NLI confidence (0-1)
    top_k_documents: 3                # Number of policy docs to consider
  
  # Which checks to run
  checks:
    - type: hallucination_detection
      enabled: true
      confidence_threshold: 0.80      # When to flag as hallucination
      
    - type: policy_compliance
      enabled: true
      confidence_threshold: 0.75
      
    - type: pii_detection
      enabled: true
      
    - type: tool_validation
      enabled: true
  
  # Tool usage configuration
  tools:
    issue_refund:
      max_per_transaction: 500        # Max per single call
      max_per_month: 10000            # Max per cohort per month
      max_per_user: 2000              # Max per individual user
      requires_escalation_above: 1000 # Auto-escalate above amount
      
    modify_order:
      max_per_transaction: 5          # Examples only
      max_per_month: 100
  
  # Escalation configuration
  escalation:
    enabled: true
    handlers:
      - supervisor@company.com
      - compliance@company.com
    timeout_minutes: 60               # Max time before auto-reject
  
  # Decision thresholds
  decision_thresholds:
    allow_confidence: 0.95            # When can we ALLOW?
    block_confidence: 0.90            # When should we BLOCK?
    regenerate_confidence: 0.80       # When should we REGENERATE?
  
  # Policy documents (for NLI)
  corpus:
    - refund_policy.txt
    - faq.txt
    - business_rules.txt
```

---

## Check Types

### Hallucination Detection

Detects when LLM claims things not supported by policy documents.

```yaml
checks:
  - type: hallucination_detection
    enabled: true
    confidence_threshold: 0.80        # Flag if confidence >= 0.80
    
    # Advanced options
    nli_model: cross-encoder/nli-deberta-v3-base
    uncertainty_samples: 3            # Multiple inference runs
    similarity_threshold: 0.5         # Evidence relevance
```

**When to enable:**
- High-stakes decisions (refunds, medical advice)
- Compliance-heavy workflows
- When policy documents exist

**When to disable:**
- General Q&A (no policy to violate)
- Creative content generation
- When policy corpus unavailable

---

### Policy Compliance

Checks if response violates defined business rules.

```yaml
checks:
  - type: policy_compliance
    enabled: true
    confidence_threshold: 0.75
    
    # Rules can be:
    rules:
      - "Refunds only within 30 days"
      - "No refunds over $1000 without supervisor"
      - "Cannot promise 100% satisfaction guarantee"
```

**When to enable:**
- Enforcing business rules
- Preventing unauthorized commitments
- Ensuring consistent messaging

---

### PII Detection

Automatically detects and redacts sensitive information.

```yaml
checks:
  - type: pii_detection
    enabled: true
    
    # What to detect
    detect:
      - email
      - phone
      - ssn
      - credit_card
      - account_number
      - address
      - date_of_birth
    
    # Action on detection
    action: redact               # redact or block
    confidence_threshold: 0.95   # Require high confidence
```

**When to enable:**
- Always (PII is always risky)
- Essential for GDPR/HIPAA/PCI compliance

---

### Tool Validation

Validates function calls before execution.

```yaml
tools:
  issue_refund:
    max_per_transaction: 500
    max_per_month: 10000
    requires_escalation_above: 1000
    requires_approval: false
    whitelist:
      - authorized_users: []          # Empty = all allowed
  
  modify_order:
    max_per_transaction: 5
    forbidden_states: ["shipped", "delivered"]  # Can't modify
    requires_approval: true
    whitelist:
      - authorized_roles: ["supervisor", "manager"]
```

**When to enable:**
- When LLM can call external APIs
- Budget/cost control needed
- Authorization required

---

## Risk Tiers

### Low-Risk Workflows

```yaml
low-risk-faq:
  risk_tier: low
  
  checks:
    - type: pii_detection
      enabled: true              # Still detect PII
    - type: hallucination_detection
      enabled: false             # Not needed for FAQs
  
  escalation:
    enabled: false               # No human review needed
```

Use for:
- FAQ answering
- General information
- No sensitive decisions

---

### Medium-Risk Workflows

```yaml
medium-risk-support:
  risk_tier: medium
  
  checks:
    - type: pii_detection
      enabled: true
    - type: hallucination_detection
      enabled: true
      confidence_threshold: 0.75   # Less strict
    - type: tool_validation
      enabled: true
  
  escalation:
    enabled: true
    timeout_minutes: 30              # Quick response needed
```

Use for:
- Customer support
- Account information
- Some tool usage

---

### High-Risk Workflows

```yaml
high-risk-finance:
  risk_tier: high
  
  checks:
    - type: pii_detection
      enabled: true
    - type: hallucination_detection
      enabled: true
      confidence_threshold: 0.85   # Strict
    - type: policy_compliance
      enabled: true
    - type: tool_validation
      enabled: true
  
  escalation:
    enabled: true
    timeout_minutes: 60
    handlers:
      - compliance@company.com
      - legal@company.com
```

Use for:
- Financial decisions
- Medical recommendations
- High-value transactions

---

## Policy Documents (Corpus)

For hallucination detection to work, you need policy documents.

### Creating Policy Documents

**File:** `corpus/refund-policy.txt`

```
REFUND POLICY

Return Window:
- Standard products: 30 days from purchase
- Electronics: 15 days from purchase
- Final sale items: No refunds

Refund Amount:
- Within return window: Full refund minus restocking fee (15%)
- Restocking fee waived for defective items

Process:
1. Customer initiates return within return window
2. Item inspected for condition
3. Refund issued within 5-7 business days

Exceptions:
- Items marked "final sale": No refunds allowed
- Opened electronics: 15-day window only
- Supervisor approval required for refunds > $1000
```

### Good Practices

1. **Be specific:** Vague policies lead to hallucinations
   - ❌ "Reasonable refund window"
   - ✅ "30 days from purchase"

2. **Document exceptions:** Make all rules explicit
   - ❌ Implied exceptions
   - ✅ "Electronics: 15 days. Final sale: No refunds."

3. **Include examples:** Help NLI understand context
   ```
   EXAMPLE 1: Customer bought product 20 days ago
   Eligible? YES (within 30-day window)
   
   EXAMPLE 2: Customer bought product 45 days ago
   Eligible? NO (outside 30-day window)
   ```

4. **Update frequently:** Policies change
   - Review quarterly
   - Update when rules change
   - Version your corpus

---

## Decision Logic

### How Decisions Are Made

```
Check Results → Aggregate Issues → Apply Logic → Decision
        ↓                ↓               ↓           ↓
    Lane A/B      Severity/Count   Rules Match   ALLOW/EDIT/
    Results                                      REGEN/BLOCK
```

### Example Decision Tree

```yaml
decision_logic:
  # No issues
  if: all_checks_pass
  then: ALLOW

  # Only PII issues
  elif: only_pii_detected
  then: EDIT
  reason: "Remove PII, keep content"

  # High-confidence hallucination
  elif: hallucination_detected AND confidence > 0.85
  then: REGENERATE
  reason: "Regenerate without hallucination"

  # Policy violation
  elif: policy_violation
  then: ESCALATE
  reason: "Violates business policy"

  # Uncertain
  else: ESCALATE
  reason: "Uncertain, needs human review"
```

### Customizing Decision Logic

You can override default logic:

```yaml
refund-copilot:
  # Custom decision logic
  decision_overrides:
    # Always ALLOW if policy-grounded
    - if: "hallucination_detection.passed AND policy_compliance.passed"
      then: ALLOW
      confidence: 0.98
    
    # Always BLOCK high-value issues
    - if: "tool_call.amount > 5000"
      then: ESCALATE
      confidence: 1.0
```

---

## Testing Your Policy

### 1. Unit Test

```yaml
# policy/tests/refund-copilot-tests.yaml
test_cases:
  - name: "Within refund window"
    input: "I bought this 20 days ago. Can I get a refund?"
    expected_decision: ALLOW
    reason: "Within 30-day window"
  
  - name: "Outside refund window"
    input: "I bought this 45 days ago. Can I get a refund?"
    expected_decision: REGENERATE
    reason: "Outside 30-day window (hallucination)"
  
  - name: "High-value refund"
    input: "I want a $5000 refund"
    expected_decision: ESCALATE
    reason: "Exceeds $1000 limit"
```

### 2. Run Tests

```bash
python -m tests.policy_tests --policy refund-copilot
```

### 3. Production Validation

```bash
# Check recent decisions match policy intent
sqlite3 data/controlplane.db \
  "SELECT workflow, decision, COUNT(*) \
   FROM audit_trail \
   WHERE workflow='refund-copilot' \
   GROUP BY decision;"
```

---

## Policy Performance Tuning

### Slow? Reduce checks

```yaml
# Remove non-critical checks
checks:
  - type: hallucination_detection
    enabled: true
  - type: pii_detection
    enabled: true
  # Remove: policy_compliance (if not critical)
```

### Too many false positives? Adjust thresholds

```yaml
# Loosen confidence requirements
checks:
  - type: hallucination_detection
    confidence_threshold: 0.70  # Was 0.85 (less strict)
```

### Too many false negatives? Tighten thresholds

```yaml
# Stricter confidence requirements
checks:
  - type: hallucination_detection
    confidence_threshold: 0.90  # Was 0.80 (more strict)
```

---

## Multi-Workflow Setup

### Financial Services Example

```yaml
refund-copilot:
  risk_tier: high
  checks: [hallucination, policy, tool]
  escalation: enabled

faq-bot:
  risk_tier: low
  checks: [pii_detection]
  escalation: disabled

claims-processor:
  risk_tier: high
  checks: [hallucination, policy, tool]
  escalation: enabled
  handlers:
    - claims_adjuster@company.com
```

### Use in API

```python
# Different policies for different workflows
response1 = client.chat.completions.create(
    model="gpt-oss-120b",
    messages=[...],
    extra_body={"workflow": "refund-copilot"}  # Strict policy
)

response2 = client.chat.completions.create(
    model="gpt-oss-120b",
    messages=[...],
    extra_body={"workflow": "faq-bot"}  # Loose policy
)
```

---

## Policy Versioning

### Track changes

```yaml
# Header of each policy file
# Policy: refund-copilot
# Version: 2.1
# Last Updated: 2024-11-29
# Changes:
#   2.1: Increased max refund to $500 (was $300)
#   2.0: Added supervisor approval for > $1000
#   1.0: Initial version

refund-copilot:
  version: 2.1
  ...
```

### Rollback safely

```bash
# Use git to manage policy versions
git log policy/workflows/refund-copilot.yaml

# Rollback if needed
git checkout <commit-hash> policy/workflows/refund-copilot.yaml
```

---

## Common Patterns

### Refund Approval

```yaml
refund-copilot:
  risk_tier: high
  checks:
    - type: hallucination_detection
      enabled: true
    - type: policy_compliance
      enabled: true
  tools:
    issue_refund:
      max_per_transaction: 500
      requires_escalation_above: 500
```

### Healthcare Recommendation

```yaml
care-advisor:
  risk_tier: high
  checks:
    - type: hallucination_detection
      enabled: true
    - type: pii_detection
      enabled: true
  escalation:
    enabled: true
    handlers: ["doctor@clinic.com"]
```

### Customer Support FAQ

```yaml
support-faq:
  risk_tier: low
  checks:
    - type: pii_detection
      enabled: true
    - type: hallucination_detection
      enabled: false  # Not needed for FAQs
  escalation:
    enabled: false
```

### Payment Processing

```yaml
payment-processor:
  risk_tier: high
  checks:
    - type: tool_validation
      enabled: true
    - type: pii_detection
      enabled: true
  tools:
    process_payment:
      max_per_transaction: 50000
      requires_approval: true
```

---

## Debugging Policies

### Enable policy logging

```bash
LOG_LEVEL=DEBUG python -m gateway.app
```

### Check policy loading

```bash
python -c "from policy.engine import PolicyEngine; engine = PolicyEngine(); print(engine.list_workflows())"
```

### Test policy on input

```python
from policy.engine import PolicyEngine

engine = PolicyEngine()
policy = engine.get_policy("refund-copilot")

# Simulate response
test_response = "I can offer you a 90-day refund"

# Check against policy
result = engine.check_compliance(test_response, policy)
print(result)
```

---

## Best Practices

1. **Start strict, loosen over time**
   - Begin with high confidence thresholds
   - Reduce false positives gradually

2. **Monitor decision distribution**
   - Track % ALLOW vs. BLOCK vs. ESCALATE
   - Alert on unusual patterns

3. **Update corpus regularly**
   - Add new policy documents as rules change
   - Remove outdated information

4. **Test before deploying**
   - Use test cases to validate policy
   - Gradual rollout (canary deployment)

5. **Review escalations**
   - Monitor which escalations are approved/rejected
   - Use feedback to tune thresholds

6. **Keep policies simple**
   - One responsibility per policy
   - Clear, explicit rules
   - Well-documented examples

---

**For more information:**
- [Features](FEATURES.md) — What policies can do
- [Architecture](ARCHITECTURE.md) — How policy checking works
- [Examples](EXAMPLES.md) — Real-world scenarios
- [Deployment Guide](DEPLOYMENT_GUIDE.md) — Production setup

"Models generate. ControlPlane governs."

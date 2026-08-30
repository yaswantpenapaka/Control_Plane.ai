# ControlPlane.ai Architecture

Complete system design, component interactions, and decision flow.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        APPLICATION                          │
│              (e.g., Customer Support Chatbot)               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ REST API (OpenAI-compatible)
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    API GATEWAY                              │
│  (FastAPI, OpenAI SDK compatibility)                        │
├─────────────────────────────────────────────────────────────┤
│ • Request validation                                        │
│ • OpenAI protocol translation                               │
│ • Response formatting                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│           GOVERNANCE ORCHESTRATOR                           │
│  (Main decision pipeline coordinator)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    STEP 1: REQUEST INTERPRETATION                  │   │
│  │  • Extract workflow name                           │   │
│  │  • Identify cohort/user segment                    │   │
│  │  • Load policy configuration                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    STEP 2: LLM GENERATION                          │   │
│  │  • Call LLM (Groq, OpenAI, etc.)                  │   │
│  │  • Generate response                              │   │
│  │  • Extract tool calls (if any)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    STEP 3: RISK ROUTER                            │   │
│  │  • Assess response risk level                     │   │
│  │  • Route to appropriate checks (Lane A / Lane B)  │   │
│  │  • Parallel or sequential execution               │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│         ┌────────────┴────────────┐                        │
│         │                         │                        │
│         ▼                         ▼                        │
│  ┌─────────────────┐     ┌──────────────────┐              │
│  │  LANE A         │     │  LANE B          │              │
│  │  DETERMINISTIC  │     │  ML-BASED        │              │
│  │  CHECKS         │     │  CHECKS          │              │
│  └─────────────────┘     └──────────────────┘              │
│         │                         │                        │
│         └────────────┬────────────┘                        │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    STEP 4: DECISION ENGINE                         │   │
│  │  • Aggregate check results                         │   │
│  │  • Apply decision logic                            │   │
│  │  • Generate reasoning                              │   │
│  │  • Make final decision (ALLOW/EDIT/REGEN/...)     │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                      │
│                      ▼                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    STEP 5: ACTION EXECUTION                        │   │
│  │  • Apply decision (edit, regenerate, etc.)        │   │
│  │  • Log audit trail                                 │   │
│  │  • Format response                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                       │
                       │ Response with metadata
                       ▼
            ┌──────────────────────┐
            │   Application        │
            │   (enriched response │
            │    + governance meta)│
            └──────────────────────┘
```

---

## Component Details

### 1. API Gateway (`gateway/app.py`)

**Responsibility:** Translate user requests into governance pipeline.

**Key Functions:**
- Validate incoming requests
- Transform OpenAI format to internal format
- Call governance orchestrator
- Format response for OpenAI SDK compatibility
- Handle streaming (if implemented)

**Input:** OpenAI-compatible chat completion request
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [{"role": "user", "content": "..."}],
  "extra_body": {"workflow": "refund-copilot"}
}
```

**Output:** OpenAI-compatible response + governance metadata
```json
{
  "choices": [{"message": {"content": "..."}}],
  "controlplane": {
    "decision": "ALLOW",
    "confidence": 0.95,
    "audit_id": "..."
  },
  "usage": {...}
}
```

---

### 2. Governance Orchestrator (`controlplane/orchestrator.py`)

**Responsibility:** Coordinate the multi-stage governance pipeline.

**Workflow:**
```python
# Simplified pseudocode
def governance_pipeline(request):
    # Step 1: Interpret request
    policy = load_policy(request.workflow)
    risk_level = assess_initial_risk(request, policy)
    
    # Step 2: Generate LLM response
    llm_response = call_llm(request.messages)
    
    # Step 3: Route to appropriate checks
    if risk_level == "low":
        # Lane A only (fast, deterministic)
        results = run_lane_a_checks(llm_response)
    elif risk_level == "high":
        # Both lanes (comprehensive)
        results_a = run_lane_a_checks(llm_response)
        results_b = run_lane_b_checks(llm_response, policy)
        results = merge_results(results_a, results_b)
    
    # Step 4: Make decision
    decision = decision_engine.decide(results, policy)
    
    # Step 5: Execute decision
    final_output = execute_decision(decision, llm_response)
    
    # Step 6: Log audit trail
    log_audit_trail(request, llm_response, decision, final_output)
    
    return response_with_metadata(final_output, decision)
```

---

### 3. Lane A: Deterministic Checks

**Responsibility:** Fast, reliable checks that don't require ML.

**Checks in Lane A:**
- **Budget/Amount Validation** — Is tool call amount within limits?
- **PII Detection** — Contains email, phone, SSN, etc.?
- **Security Rules** — Violates hardcoded security policies?
- **Rate Limiting** — Exceeds request rate limits?
- **Blacklist Checking** — Contains forbidden words/patterns?

**Implementation:**
```python
class LaneAChecker:
    def check_budget(self, tool_call, policy):
        # Deterministic: amount < policy_limit?
        return pass_or_fail
    
    def check_pii(self, text):
        # Regex/heuristics: find email, phone, SSN?
        return pii_detected_or_not
    
    def check_security_rules(self, response, policy):
        # Apply hardcoded security rules
        return violation_or_ok
```

**Benefits:**
- Sub-10ms latency
- Zero false negatives (if rule matches, it's real)
- No ML model needed
- Deterministic results

---

### 4. Lane B: ML-Based Checks

**Responsibility:** Context-aware checks using NLI and policy reasoning.

**Checks in Lane B:**
- **Hallucination Detection** — Does claim match policy documents?
- **Policy Compliance** — Does response follow business rules?
- **Tone/Style Validation** — Is response appropriate for context?

**Implementation:**

#### 4a. Hallucination Detection (NLI)

```python
class HallucinationDetector:
    def __init__(self):
        self.nli_model = load_nli_model()
        self.retriever = PolicyRetriever()
    
    def detect(self, claim, policy):
        # 1. Retrieve relevant evidence
        evidence = self.retriever.find_relevant_docs(claim)
        
        # 2. Check each piece of evidence
        for doc in evidence:
            # NLI: entailment, neutral, or contradiction?
            inference = self.nli_model.infer(claim, doc)
            
            if inference == "contradiction":
                return {
                    "hallucinated": True,
                    "confidence": 0.92,
                    "evidence": doc,
                    "reason": "Claim contradicts policy"
                }
        
        return {"hallucinated": False, "confidence": 0.95}
```

#### 4b. Policy Compliance

```python
class PolicyCompliance:
    def check(self, response, policy):
        # 1. Extract key claims from response
        claims = extract_claims(response)
        
        # 2. Check each claim against policy
        for claim in claims:
            if violates_policy(claim, policy):
                return {
                    "compliant": False,
                    "violation": claim,
                    "policy_rule": violated_rule
                }
        
        return {"compliant": True}
```

**Benefits:**
- Context-aware decisions
- Handles nuance and semantics
- Reduces false positives
- Explainable reasoning

**Cost:**
- 100-200ms latency
- ML model inference required
- Can be parallelized

---

### 5. Decision Engine (`decision/engine.py`)

**Responsibility:** Aggregate check results and make final governance decision.

**Decision Logic:**

```python
class DecisionEngine:
    def decide(self, check_results, policy):
        # Classify issues by severity
        issues = classify_issues(check_results)
        
        if not issues:
            # No problems found
            return Decision.ALLOW
        
        elif issues.all_are("pii"):
            # Only PII issues → redact
            return Decision.EDIT
        
        elif issues.any_is("hallucination") and issues.high_confidence():
            # Hallucination with high confidence → regenerate
            return Decision.REGENERATE
        
        elif issues.any_is("tool_amount_violation") and issues.severe():
            # Severe policy violation → escalate or block
            if policy.requires_escalation:
                return Decision.ESCALATE
            else:
                return Decision.BLOCK
        
        else:
            # Uncertain or borderline → escalate to human
            return Decision.ESCALATE
```

**Decision Types:**
```python
class Decision(Enum):
    ALLOW      = "send as-is"
    EDIT       = "modify then send"
    REGENERATE = "ask LLM to retry"
    ESCALATE   = "send to human"
    BLOCK      = "don't send"
```

---

### 6. Audit Trail (`audit/trail.py`)

**Responsibility:** Immutable record of all governance decisions.

**Database Schema:**
```sql
CREATE TABLE audit_trail (
    audit_id TEXT PRIMARY KEY,
    timestamp DATETIME,
    workflow TEXT,
    user_input TEXT,
    llm_response TEXT,
    checks_lane_a JSON,
    checks_lane_b JSON,
    decision TEXT,
    decision_reason TEXT,
    final_output TEXT,
    tokens_used INTEGER,
    latency_ms INTEGER,
    hash TEXT,
    previous_hash TEXT,  -- For chain verification
    created_at DATETIME
);
```

**Hash Chain Verification:**
```
audit_1 (hash=a7d2...)
    ↓
audit_2 (hash=c3b5... previous_hash=a7d2...)
    ↓
audit_3 (hash=e1f9... previous_hash=c3b5...)

Tampering detected if previous_hash doesn't match!
```

---

## Data Flow Example

**Scenario: Hallucination Detection**

```
1. USER REQUEST
   Input: "I bought this 45 days ago. Can I get a full refund?
            Everyone gets 90-day refunds, right?"
   Workflow: refund-copilot

2. API GATEWAY
   ├─ Validate request ✓
   ├─ Load refund-copilot policy
   └─ Call governance orchestrator

3. GOVERNANCE ORCHESTRATOR
   ├─ Assess risk: HIGH (refund request)
   └─ Route to both Lane A + Lane B

4. LANE A CHECKS
   ├─ Budget check: PASS (no tool call yet)
   ├─ PII check: PASS (no sensitive data)
   └─ Security check: PASS

5. LANE B CHECKS
   ├─ Hallucination detection:
   │  ├─ Extract claim: "Everyone gets 90-day refunds"
   │  ├─ Retrieve evidence: Policy says "30-day refund window"
   │  ├─ NLI inference: CONTRADICTION
   │  └─ Result: HALLUCINATION DETECTED (confidence 0.92)
   │
   ├─ Policy compliance:
   │  ├─ Check claim against policy
   │  └─ Result: POLICY_VIOLATION
   │
   └─ Tool validation: N/A (no tool call yet)

6. DECISION ENGINE
   ├─ Aggregate results
   ├─ Classify issues: [hallucination, policy_violation]
   ├─ Apply decision logic
   └─ Decision: REGENERATE (high-confidence hallucination)

7. ACTION EXECUTION
   ├─ Ask LLM to regenerate:
   │  "Answer but cite the actual refund policy"
   │
   ├─ New response: "Based on our 30-day policy, you're outside
   │                 the window. Would you like to discuss a
   │                 partial refund?"
   │
   ├─ Re-check new response
   └─ Final response passes all checks ✓

8. AUDIT TRAIL
   ├─ Log original request
   ├─ Log checks and results
   ├─ Log decision and reason
   ├─ Log final output
   ├─ Hash chain verification
   └─ Audit ID: audit_2024_11_29_001

9. RESPONSE TO USER
   {
     "choices": [{
       "message": {"content": "Based on our 30-day policy..."}
     }],
     "controlplane": {
       "decision": "REGENERATE",
       "reason": "Hallucination detected",
       "confidence": 0.92,
       "audit_id": "audit_2024_11_29_001"
     }
   }
```

---

## Performance Characteristics

### Latency Breakdown (typical)

```
Lane A Checks:         ~15ms
  - Budget check:      2ms
  - PII detection:     8ms
  - Security check:    5ms

LLM Generation:        ~100ms (Groq)
  (can be parallelized with Lane A)

Lane B Checks:         ~80ms
  - Evidence retrieval: 30ms
  - NLI inference:     50ms

Decision Engine:       ~5ms

Audit Logging:         ~10ms
─────────────────────────────
Total:                 ~210ms (sequential worst case)
                       ~125ms (with parallelization)
```

**Target:** <200ms median latency ✓

### Throughput

- **Single Instance:** 100+ requests/second
- **Horizontal Scaling:** Add more instances for linear scaling
- **Bottleneck:** LLM provider (Groq API limits)

### Reliability

- **Graceful Degradation:** If Lane B fails, fall back to Lane A
- **Timeout Handling:** If check takes too long, use default action
- **Error Recovery:** Failed checks don't crash pipeline

---

## Error Handling Strategy

```
┌─────────────────────────────┐
│   Check Execution Timeout   │
└──────────────┬──────────────┘
               │
        ┌──────▼──────┐
        │ Severity?   │
        └──────┬──────┘
               │
      ┌────────┴─────────┐
      │                  │
   Low Risk         High Risk
      │                  │
   ALLOW            ESCALATE
      │                  │
    Send            Send to
    as-is           human
```

---

## Configuration & Extensibility

### Adding a New Check

```python
# 1. Implement check interface
class MyNewCheck(BaseCheck):
    def execute(self, response, policy):
        # Your check logic
        return CheckResult(
            passed=True/False,
            confidence=0.95,
            reason="..."
        )

# 2. Register in decision engine
decision_engine.register_check("my_new_check", MyNewCheck())

# 3. Enable in policy YAML
checks:
  my_new_check:
    enabled: true
    confidence_threshold: 0.80
```

### Adding a New Workflow

```yaml
# policies/my-workflow.yaml
my-workflow:
  risk_tier: medium
  evidence:
    required: true
    min_confidence: 0.75
  checks:
    - type: pii_detection
      enabled: true
    - type: hallucination_detection
      enabled: true
    - type: my_new_check
      enabled: true
  tools:
    my_tool:
      max_per_transaction: 1000
```

---

## Security Considerations

1. **API Key Management**
   - Keys stored in environment variables
   - Never logged or audited
   - Rotated periodically

2. **Audit Trail Integrity**
   - Hash-chain prevents tampering
   - Immutable SQLite database
   - Regular verification checks

3. **Model Security**
   - Models downloaded from trusted sources
   - Verified checksums
   - Sandboxed execution

4. **Input Validation**
   - Request size limits
   - Timeout protection
   - Rate limiting

---

## Monitoring & Observability

**Key Metrics:**
- Decision distribution (ALLOW %, BLOCK %, etc.)
- Average latency
- Error rate
- Hallucination detection rate
- Cost per request

**Logging:**
- Request/response logging
- Decision reasoning
- Error tracking
- Performance metrics

**Alerting:**
- High error rate
- Latency spikes
- Unusual decision patterns
- Audit trail verification failures

---

## Deployment Topology

### Development
```
Single Machine
├─ API Gateway (port 8000)
├─ Governance Orchestrator
├─ SQLite Database
└─ Models cached locally
```

### Production
```
Load Balancer
    ├─ API Gateway (instance 1)
    ├─ API Gateway (instance 2)
    └─ API Gateway (instance N)
        │
        ├─ Shared Database (RDS/PostgreSQL)
        ├─ Shared Model Cache
        ├─ Audit Trail Database
        └─ Monitoring/Logging (ELK/DataDog)
```

---

**For more details, see:**
- [Getting Started](GETTING_STARTED.md) — Setup and first run
- [Features](FEATURES.md) — What each component does
- [Deployment Guide](DEPLOYMENT_GUIDE.md) — Production setup
- [Policies](POLICIES.md) — How to configure checks

"Models generate. ControlPlane governs."

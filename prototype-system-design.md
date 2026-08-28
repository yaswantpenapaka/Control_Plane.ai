# ControlPlane.ai — Round 2 Prototype System Design

**Team:** VARANASI  
**Challenge:** Accenture Innovation Challenge 2026 — Round 2  
**Problem Track:** ControlPlane.ai  
**Prototype stack:** Python 3.11+ · FastAPI gateway · Streamlit UI · Groq API · Sentence-Transformers · local NLI · SQLite  
**Submission freeze:** 30 August 2026

---

## 0. Design status

This document is the **implementation contract** for the Round 2 prototype.

It deliberately refines the earlier design in four ways:

1. **Groq is the only external LLM provider used by the prototype.**
2. **NLI, embeddings, and PII detection run locally** so the safety decision does not depend on a second paid API.
3. **"Unverified" is not treated as "hallucinated."** The prototype explicitly represents `entailed`, `contradicted`, `unverified`, and `uncertain`.
4. The prototype is **evidence- and policy-grounded, not a truth oracle**. Its evaluation claims apply to the seeded benchmark/corpus, not to arbitrary real-world truth.

The official Round 2 brief says ControlPlane should handle different use cases/risk tolerances, overlapping risks, missing ground truth, false-positive/false-negative tradeoffs, agentic actions, configurable governance, tiered decisions, audit trails, and monitoring. It also explicitly allows simulated data and asks for a working proof of the core mechanism rather than production-grade infrastructure.

---

# 1. Product definition

## 1.1 One-sentence definition

> **ControlPlane.ai is an AI governance middleware that sits between an enterprise AI application and its model provider, applying workflow-specific policies to generated responses and proposed actions before they reach a user or execute a tool.**

## 1.2 Product positioning

ControlPlane is **not**:

- another foundation model;
- a generic chatbot safety filter;
- a universal hallucination detector;
- a replacement for enterprise policy owners;
- a claim that AI truth can always be established automatically.

ControlPlane is:

- a **policy enforcement layer**;
- a **risk-routing layer**;
- an **evidence verification layer** for claims where trusted local evidence exists;
- an **action/tool gate** for AI systems that can act;
- a **governance and audit layer**.

### Core message

> **Models generate. ControlPlane governs.**

### Operating loop

> **Declare → Inspect → Verify → Decide → Intervene → Audit**

---

# 2. Round 1 continuity

The Round 1 submission framed three enterprise failures:

1. **Confidently wrong:** unsupported claims reach users.
2. **Quietly expensive:** unnecessary model calls, regeneration and correction create untracked rework.
3. **Subtly biased:** outcome disparities can be invisible in individual responses but visible across populations.

The Round 1 differentiator was the idea of a **workflow-specific error budget**: a declared ceiling on tolerated risk, rather than one universal safety threshold.

Round 1 also proposed:

- gateway/middleware placement;
- cheap checks on all traffic;
- expensive inspection only when needed;
- evidence entailment rather than similarity;
- semantic uncertainty;
- deterministic privacy detection;
- tool-call gating;
- least-disruptive interventions;
- tamper-evident decision records.

The Round 2 prototype retains these ideas but makes the claims more precise.

---

# 3. What the prototype must prove

The prototype must make these six claims demonstrable.

### P1 — One integration boundary

A demo client uses an OpenAI-compatible interface and changes its model endpoint to ControlPlane. The client does not need to know the internal safety pipeline.

**Important precision:** the prototype demonstrates **OpenAI-compatible gateway integration**, not universal drop-in compatibility with every provider-specific feature.

### P2 — Governance differs by workflow

A `refund-copilot` workflow can require evidence and strict tool gating while an `internal-summarizer` workflow can use a lower-risk policy.

The same underlying Groq model can therefore receive different governance treatment.

### P3 — Confidence is not treated as correctness

A fluent response is not accepted merely because the model sounds certain.

When trusted source evidence exists, claims are checked using **retrieval + NLI**.

When multiple sampled answers disagree semantically, that disagreement is represented as an **uncertainty signal**.

### P4 — Uncertainty is handled honestly

The system distinguishes:

- `entailed` — evidence supports the claim;
- `contradicted` — evidence conflicts with the claim;
- `unverified` — insufficient trusted evidence;
- `uncertain` — generation/checking signals are materially inconsistent.

**Unverified is not automatically hallucinated.**

If evidence is missing for a high-risk claim, the system can abstain/escalate instead of pretending to know the truth.

### P5 — Least-disruptive intervention

The decision engine uses:

`allow → edit → regenerate → escalate → block`

The first applicable intervention that satisfies the workflow policy is selected.

### P6 — AI actions are governed before execution

A proposed tool call such as:

`issue_refund(amount=8000)`

passes through a ControlPlane tool gate before the simulated tool executes.

For high-risk gated tools, evidence requirements and argument constraints must pass first.

---

# 4. Scope

## 4.1 In scope

- Groq-hosted LLM generation.
- OpenAI-compatible request/response shape at the ControlPlane boundary.
- Streamlit governance console.
- Workflow YAML policies.
- Local fictional enterprise knowledge corpus.
- Local embedding retrieval.
- Local NLI.
- Local deterministic PII detection.
- Claim extraction through Groq structured output.
- Semantic uncertainty via repeated Groq sampling.
- Risk routing.
- Intervention ladder.
- Simulated tool execution.
- Error/risk budget accounting.
- Population-level bias analytics using seeded/simulated records.
- SQLite audit/metrics storage.
- Hash-chained audit verification.
- Deterministic replay/demo mode.
- Seeded evaluation suite.
- Latency, token and estimated-cost telemetry.

## 4.2 Explicitly out of scope

- Production authentication/RBAC.
- Multi-tenancy.
- Production RAG infrastructure.
- Real customer/bank data.
- Real financial transactions.
- Real external tool execution.
- Fine-tuning custom detectors.
- Continuous online model training.
- Automated regulatory/legal compliance certification.
- Streaming-token interception.
- Guaranteed truth detection.
- Production-grade distributed deployment.
- Kubernetes/microservice infrastructure for the competition prototype.

These are roadmap items, not hidden gaps.

---

# 5. High-level architecture

```text
┌─────────────────────── DEMO / CLIENT APPLICATION ───────────────────────┐
│  Refund Copilot / Internal Summarizer                                  │
│  OpenAI-compatible chat completion client                              │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                               │ POST /v1/chat/completions
                               ▼
┌──────────────────────────── CONTROLPLANE ────────────────────────────────┐
│                                                                         │
│  ┌────────────────────┐     ┌────────────────────────────────────────┐ │
│  │ Request / Gateway  │────►│ Workflow Policy Engine                │ │
│  │ Adapter            │     │ YAML → validated Policy                │ │
│  └─────────┬──────────┘     └──────────────────┬─────────────────────┘ │
│            │                                   │                       │
│            │                                   ▼                       │
│            │                        ┌──────────────────────┐           │
│            │                        │ Groq Upstream Client │           │
│            │                        └──────────┬───────────┘           │
│            │                                   │                       │
│            │◄──────────── generated response / tool call ─────────────┘
│            │
│            ▼
│  ┌──────────────────────────── CHECK PIPELINE ────────────────────────┐ │
│  │                                                                     │ │
│  │  Lane A — deterministic / cheap                                    │ │
│  │  • PII & secrets   • tool policy   • safety keywords   • telemetry │ │
│  │                                                                     │ │
│  │                    Risk Router                                      │ │
│  │                         │                                           │ │
│  │                         ▼                                           │ │
│  │  Lane B — evidence / uncertainty                                  │ │
│  │  • claim extraction (Groq)                                         │ │
│  │  • local retrieval (MiniLM)                                       │ │
│  │  • local NLI (DeBERTa-v3 NLI)                                     │ │
│  │  • semantic uncertainty (k=3 Groq samples + clustering)            │ │
│  │                                                                     │ │
│  └──────────────────────────────┬──────────────────────────────────────┘ │
│                                 ▼                                       │
│                       ┌────────────────────┐                            │
│                       │ Decision Engine    │                            │
│                       │ + Budget Accountant│                            │
│                       └─────────┬──────────┘                            │
│                                 │                                       │
│              ┌──────────────────┼──────────────────┐                    │
│              ▼                  ▼                  ▼                    │
│           Response           Tool Call          Audit                  │
│          intervention        Tool Gate          Ledger                 │
│              │                  │                  │                    │
│              └──────────────────┴──────────────────┘                    │
│                                 │                                       │
│                         SQLite + Streamlit                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 6. Runtime model strategy

## 6.1 External model

**Groq API** is the prototype's generation provider.

The application reads:

- `GROQ_API_KEY`
- `GROQ_MODEL`

from environment variables.

The model must be selected through configuration rather than hard-coded throughout the codebase.

### Recommended default

At design time, use:

`qwen/qwen3.8-27b`

because Groq currently documents it as supporting tool use and strict structured outputs.

The implementation must still expose `GROQ_MODEL` as an environment variable and validate the selected model at startup. If Groq changes availability, the prototype can be switched without code changes.

A documented fallback may be:

`openai/gpt-oss-20b`

provided the selected model is active on the account.

## 6.2 Why not use Groq for every safety component?

The prototype deliberately separates:

### Groq
- user-facing generation;
- claim extraction;
- controlled regeneration;
- uncertainty sampling.

### Local open-source models
- embeddings;
- NLI;
- deterministic PII detection.

This avoids making the safety decision dependent on a second paid API and demonstrates that ControlPlane is an independent governance layer rather than another LLM judging the first LLM.

## 6.3 Important limitation

Local models are downloaded from Hugging Face on first run unless already cached. They are not APIs and require no Hugging Face token for the public models selected here.

---

# 7. Request lifecycle

## Step 1 — Client request

The demo client sends an OpenAI-compatible chat completion request to ControlPlane.

Required metadata:

- workflow identifier;
- messages;
- optional declared cohort attribute for the simulated bias dataset;
- optional conversation/session identifier.

For the prototype, workflow identity may be supplied through:

`X-ControlPlane-Workflow`

or selected by the Streamlit demo.

The README must show the exact integration.

## Step 2 — Load workflow policy

The Policy Engine loads a validated YAML policy.

Example:

```yaml
workflow: refund-copilot
risk_tier: high

error_budget:
  target: 0.005
  window: 7d

latency_budget_ms: 2500

evidence:
  required: true
  min_entailment: 0.70
  abstain_without_evidence: true

privacy:
  pii: [EMAIL, PHONE, PAN, AADHAAR, ACCOUNT_NO]
  action_on_hit: edit

tools:
  issue_refund:
    gate: true
    max_amount: 5000
    prohibited_if:
      - unsupported_claim
      - evidence_failed
      - budget_exhausted

interventions:
  ladder: [allow, edit, regenerate, escalate, block]
  max_regenerations: 1
```

Low-risk example:

```yaml
workflow: internal-summarizer
risk_tier: low

error_budget:
  target: 0.05
  window: 7d

evidence:
  required: false

privacy:
  pii: [EMAIL, PHONE, PAN, AADHAAR, ACCOUNT_NO]
  action_on_hit: edit

tools: {}

interventions:
  ladder: [allow, edit, escalate, block]
  max_regenerations: 0
```

## Step 3 — Upstream generation

ControlPlane sends the request to Groq.

The upstream call records:

- model;
- start/end timestamps;
- input/output token usage when returned by the API;
- estimated cost;
- tool calls if any.

## Step 4 — Lane A

Lane A performs cheap deterministic checks.

### PII/secrets

Detect:

- email;
- phone;
- PAN;
- Aadhaar;
- account number;
- common API-key/secret patterns.

The prototype should use clearly labeled simulated examples and must not claim full production-grade DLP coverage.

### Tool policy

For each proposed tool:

- allowed tool name?
- required arguments present?
- amount within limit?
- prohibited state triggered?
- evidence requirement satisfied?

### Safety keywords

Small workflow-specific denylist for demo purposes.

### Telemetry

Record:

- latency;
- token usage;
- estimated cost;
- intervention/rework count.

## Step 5 — Risk Router

Lane B is invoked when one or more conditions apply:

- workflow is high risk;
- a factual/policy claim is detected;
- a tool call is present;
- the response contains high claim density;
- budget burn is elevated;
- policy requires evidence;
- the deterministic lane raises a relevant flag.

The router must be deterministic and explainable.

The UI must show **why Lane B fired**.

Example:

```text
Lane B triggered because:
✓ risk_tier = high
✓ policy requires evidence
✓ factual claim density = high
```

## Step 6 — Retrieval

The local corpus is embedded once at startup.

Recommended model:

`sentence-transformers/all-MiniLM-L6-v2`

For each factual claim:

1. embed the claim;
2. retrieve top-k relevant chunks;
3. retain source id/title/version;
4. pass the best evidence candidates to NLI.

Retrieval is only a supporting component. It is not presented as proof of truth.

## Step 7 — Claim extraction

Use Groq structured output to turn a response into atomic factual claims.

Example:

```json
{
  "claims": [
    {
      "text": "Customers are entitled to a full refund within 90 days.",
      "type": "policy_fact",
      "material": true
    }
  ]
}
```

The extractor must not decide whether a claim is true. It only decomposes the response.

## Step 8 — NLI verification

Use:

`cross-encoder/nli-deberta-v3-base`

locally.

For each claim/evidence pair, produce:

- entailment score;
- neutral score;
- contradiction score;
- label.

The important distinction is:

> **Entailment is not semantic similarity.**

A retrieved paragraph being similar to a claim does not prove the claim.

## Step 9 — Evidence state

Aggregate claim-level results into a response-level evidence state.

Possible values:

### ENTAILED
Material claims are supported by trusted retrieved evidence.

### CONTRADICTED
At least one material claim conflicts with trusted evidence strongly enough to violate policy.

### UNVERIFIED
A material claim has insufficient trusted evidence.

### UNCERTAIN
The evidence and/or generation signals are materially inconsistent.

The decision engine must never silently convert `UNVERIFIED` into `CONTRADICTED`.

## Step 10 — Semantic uncertainty

Semantic uncertainty is a **risk signal**, not a truth detector.

For eligible high-risk responses:

1. sample `k=3` additional Groq answers at a non-zero temperature;
2. normalize answers;
3. compare samples using bidirectional NLI;
4. cluster semantically equivalent answers;
5. compute Shannon entropy over cluster probabilities.

Formula:

`H = -Σ p_i log(p_i)`

Higher entropy means the model's sampled answers are more semantically diverse.

The UI should call this:

> **Semantic uncertainty**

rather than:

> hallucination probability.

A high entropy value alone must not prove hallucination.

## Step 11 — Decision fusion

The Decision Engine combines:

- policy;
- PII findings;
- evidence state;
- NLI scores;
- uncertainty score;
- tool status;
- budget state.

The output is a structured decision object.

Example:

```json
{
  "decision": "regenerate",
  "risk_state": "contradicted",
  "reason_codes": [
    "EVIDENCE_CONTRADICTION",
    "HIGH_RISK_WORKFLOW"
  ],
  "confidence": 0.93,
  "tool_execution_allowed": false
}
```

`confidence` here means **decision confidence under the implemented checks**, not confidence that the world is objectively true.

---

# 8. Intervention ladder

The ladder is:

```text
ALLOW
  ↓
EDIT
  ↓
REGENERATE
  ↓
ESCALATE
  ↓
BLOCK
```

The system does not blindly move down the ladder. It chooses the least disruptive action that satisfies policy.

## Allow

Use when all required checks pass.

## Edit

Use for deterministic, local repairs such as PII redaction.

Example:

```text
"My email is yaswant@example.com"
→
"My email is [REDACTED]"
```

## Regenerate

Use when:

- evidence failed;
- trusted source evidence exists;
- the issue is repairable through grounded regeneration;
- regeneration budget permits another attempt.

The regeneration prompt must pin the relevant evidence and explicitly instruct the model not to invent unsupported facts.

## Escalate

Use when:

- evidence is unavailable for a material high-risk claim;
- regeneration fails;
- a gated tool call depends on unresolved reasoning;
- policy requires human review;
- uncertainty is too high for the workflow's tolerance.

The prototype returns a structured review object.

## Block

Use when:

- policy explicitly prohibits the response/action;
- a tool call violates hard constraints;
- a critical budget/control condition is exhausted;
- no lower intervention can safely satisfy policy.

---

# 9. Error/risk budget

## 9.1 Definition

For this prototype:

> A risk-budget event is a response that, according to the seeded evaluation oracle and implemented policy checks, would have reached the user with an unsupported material claim when the workflow required evidence.

This definition is intentionally narrower than "all hallucinations in the real world."

## 9.2 Example

```yaml
error_budget:
  target: 0.005
  window: 7d
```

means:

`0.005 = 0.5%`

of eligible evaluated responses may be classified as budget-consuming failures within the chosen simulation window.

## 9.3 Burn rate

Track:

- fast window: 1 hour;
- slow window: 7 days.

For the prototype, these are simulated timestamps or accelerated evaluation windows.

The budget accountant calculates:

`burn_rate = consumed_budget / allowed_budget`

and:

`projected_burn = observed_failure_rate / target`

The system should not pretend that a small demo dataset estimates real production reliability.

## 9.4 Budget tightening

As burn increases, policy can:

- route more traffic to Lane B;
- require evidence on more claims;
- escalate earlier;
- reduce permitted regeneration;
- block certain high-risk actions.

The exact thresholds are configuration values and must be visible in policy.

---

# 10. Tool-call governance

This is a core prototype capability.

## Tool lifecycle

```text
Groq proposes tool call
        ↓
ControlPlane parses tool name + args
        ↓
Policy validation
        ↓
Evidence dependency validation
        ↓
Decision
   ┌────┼─────────┐
   ↓    ↓         ↓
 ALLOW ESCALATE  BLOCK
   ↓
Simulated tool executes
```

### Example

Model proposes:

```json
{
  "name": "issue_refund",
  "arguments": {
    "customer_id": "C-1042",
    "amount": 8000
  }
}
```

Policy:

```yaml
issue_refund:
  gate: true
  max_amount: 5000
```

Decision:

```text
BLOCK / ESCALATE
Reason:
TOOL_AMOUNT_LIMIT_EXCEEDED
```

The simulated refund tool must **not execute**.

### Critical rule

The prototype must never execute an external real-world action.

---

# 11. Multi-turn risk

The Round 2 brief specifically identifies compounding risk in multi-turn and agentic systems.

The prototype implements a lightweight version.

Each session stores:

- conversation id;
- previous decisions;
- unresolved risk states;
- evidence references;
- prior tool decisions.

Example:

### Turn 1

```text
User:
"Can I get a refund after 45 days?"

Model:
"Yes, the policy allows 90 days."

ControlPlane:
CONTRADICTED → REGENERATE
```

### Turn 2

```text
User:
"Okay, issue that refund."

Model:
issue_refund(8000)
```

ControlPlane carries the unresolved/previous evidence context into the tool gate and does not treat Turn 2 as an isolated event.

---

# 12. Bias monitoring

Bias is **population-level analytics**, not a per-response "bias score."

The prototype uses simulated/de-identified cohort labels.

Example fields:

```text
request_id
workflow
cohort
decision
outcome
timestamp
```

The dashboard calculates simple outcome disparity.

For two cohorts A and B:

`disparity = |P(positive outcome | A) - P(positive outcome | B)|`

Optional ratio:

`selection_rate_ratio = P(positive | A) / P(positive | B)`

The UI must clearly label these as **simulated monitoring metrics**, not proof of discrimination.

A minimum seeded dataset should contain enough records to show a visibly different outcome distribution.

---

# 13. Audit ledger

Use SQLite for durable prototype storage.

Each decision record contains at least:

```text
id
timestamp
request_id
session_id
workflow
policy_version
model
input_hash
output_hash
checks
risk_state
decision
reason_codes
tool_name
tool_args_hash
token_usage
estimated_cost
latency_ms
regeneration_count
budget_before
budget_after
prev_hash
record_hash
```

## Hash chaining

`record_hash = SHA256(canonical_record_without_record_hash)`

The next record stores the previous record's hash.

Verification:

```text
record 1
   ↓ hash
record 2
   ↓ hash
record 3
   ↓ hash
...
```

The verifier must report:

- chain intact, or;
- first broken record.

### Terminology rule

Unless an actual digital signature is implemented, call this:

> **tamper-evident hash chain**

Do not call it a "signed audit record."

---

# 14. Streamlit application

The Streamlit app is the primary judge-facing UI.

## Page 1 — Live Control

Show:

- workflow selector;
- policy summary;
- prompt input;
- live Groq response;
- final ControlPlane response;
- decision;
- risk state;
- reasons;
- latency;
- token usage;
- estimated cost;
- tool status.

## Page 2 — Decision Inspector

For one request:

```text
Response
  ↓
Lane A findings
  ↓
Risk Router reason
  ↓
Claims
  ↓
Retrieved evidence
  ↓
NLI result
  ↓
Semantic uncertainty
  ↓
Policy threshold
  ↓
Decision
```

This is the most important explanatory screen.

## Page 3 — Policy Center

Show:

- workflow;
- risk tier;
- budget;
- evidence requirements;
- privacy policy;
- tool policy;
- intervention ladder.

Allow safe demo-only policy switching/reloading.

Do not build a full enterprise policy editor.

## Page 4 — Risk & Budget

Show:

- budget burn;
- intervention counts;
- Lane A vs Lane B volume;
- regeneration/rework;
- estimated cost;
- latency p50/p95 from evaluation data.

## Page 5 — Bias Monitor

Show:

- simulated cohort outcome counts;
- disparity;
- selection-rate ratio;
- warning state.

## Page 6 — Audit Explorer

Show:

- recent audit records;
- decision details;
- policy version;
- hash status;
- "Verify chain" action.

## Page 7 — Evaluation

Show:

- scenario counts;
- precision/recall;
- PII redaction accuracy;
- tool-gate accuracy;
- Lane A latency;
- Lane A+B latency;
- budget adherence;
- false-positive/false-negative tradeoff.

## Page 8 — Demo Scenarios

One-click buttons for deterministic scenarios.

---

# 15. Deterministic demo mode

The prototype must support:

```text
CONTROLPLANE_MODE=demo
```

or an equivalent setting.

Demo mode uses seeded upstream outputs and expected outcomes.

This is not fake evaluation. It is a deterministic fixture mode for repeatable demonstrations.

## Required demo scenarios

### D01 — Grounded policy answer

Expected:

`ALLOW`

### D02 — Plausible hallucinated policy claim

Expected:

`CONTRADICTED → REGENERATE`

### D03 — No evidence

Expected:

`UNVERIFIED → ESCALATE`

### D04 — PII leakage

Expected:

`EDIT`

### D05 — Tool amount within policy

Expected:

`ALLOW → simulated tool executes`

### D06 — Tool amount above policy

Expected:

`ESCALATE/BLOCK → tool does not execute`

### D07 — Tool call backed by unsupported claim

Expected:

`ESCALATE/BLOCK`

### D08 — Low-risk workflow

Same style of questionable response, but policy requires less inspection.

Expected:

policy-dependent intervention demonstrating workflow differentiation.

### D09 — Budget pressure

Seed enough failures to cross a budget threshold.

Expected:

more aggressive routing/intervention.

### D10 — Multi-turn propagation

Turn 1 creates unresolved evidence risk; Turn 2 attempts an action.

Expected:

action remains gated.

### D11 — Bias batch

Seeded cohort outcomes show measurable disparity.

Expected:

dashboard warning.

### D12 — Audit tampering

Modify one stored record in a controlled test copy.

Expected:

verification identifies the broken chain.

---

# 16. Fictional enterprise corpus

Use a fictional bank/financial-services corpus.

No real customer data.

Recommended documents:

```text
refund_policy_v3.md
refund_policy_exceptions.md
chargeback_policy.md
customer_tier_policy.md
international_refund_policy.md
digital_goods_policy.md
merchant_dispute_policy.md
escalation_policy.md
tool_authorization_policy.md
privacy_policy.md
```

Every document should contain:

- document id;
- title;
- version;
- effective date;
- source label;
- content.

The key demo contradiction:

```text
Old policy:
full refund within 90 days

Active policy:
full refund within 30 days
```

Retrieval must prefer the active/effective policy.

This demonstrates policy/version awareness without pretending to be production document governance.

---

# 17. Data model

Minimum SQLite tables:

## `audit_events`

Stores immutable-ish append records and hash-chain fields.

## `requests`

Stores request/session/workflow metadata.

## `metrics`

Stores latency, tokens, estimated cost and intervention events.

## `budget_events`

Stores budget-consuming events and window calculations.

## `bias_events`

Stores simulated cohort outcome records.

## `sessions`

Stores lightweight multi-turn state.

No sensitive real-world data should be persisted.

---

# 18. Cost telemetry

The system should record actual token usage returned by Groq when available.

Estimated cost:

`estimated_cost = input_tokens × input_price + output_tokens × output_price`

Prices must be stored in configuration, not hard-coded in business logic.

If the current provider/model price is unavailable, the UI must label the result:

> `estimated cost using configured price table`

Do not present a fabricated cost as an actual invoice.

Regeneration is counted as **rework cost**.

---

# 19. Latency strategy

Lane A is designed to be cheap and local.

Lane B is intentionally more expensive because it can involve:

- claim extraction;
- retrieval;
- NLI;
- three additional sampled generations for uncertainty.

The prototype should measure, not assume:

- total request latency;
- Lane A latency;
- Lane B latency;
- regeneration latency;
- tool-gate latency.

Report p50 and p95 from the seeded evaluation run.

Do not promise a fixed `<15 ms` or `2.5 s` production SLA unless the measured prototype supports it.

---

# 20. Evaluation methodology

## 20.1 Seeded suite

Use approximately 60 evaluation cases:

- 20 grounded responses;
- 15 seeded unsupported/contradicted claims;
- 10 PII cases;
- 8 tool-call cases;
- 7 cohort replay batches.

The exact count may be increased if implementation is stable.

## 20.2 Metrics

### Unsupported-claim recall

`TP / (TP + FN)`

### False-positive rate

`FP / (FP + TN)`

### Precision

`TP / (TP + FP)`

### PII redaction recall

`correctly redacted PII spans / all seeded PII spans`

### Tool-gate accuracy

`correct tool decisions / all tool cases`

### Regeneration success rate

`successful grounded regenerations / regeneration attempts`

### Budget adherence

Compare seeded budget-consuming events with configured target.

### Latency

Report:

- p50;
- p95;

for:

- baseline Groq call;
- Lane A;
- Lane A + Lane B;
- Lane A + Lane B + regeneration.

### Cost

Report:

- average input tokens;
- average output tokens;
- average additional tokens due to ControlPlane;
- regeneration/rework tokens;
- configured estimated cost.

## 20.3 Evaluation honesty

The benchmark is **constructed and simulated**.

Therefore:

- do not call it a production accuracy benchmark;
- do not claim general hallucination detection accuracy;
- report the test corpus and oracle definition;
- distinguish seeded ground truth from real-world truth.

---

# 21. Acceptance criteria

The prototype is complete only if all are true.

## Gateway

- [ ] Streamlit/demo client can send through ControlPlane.
- [ ] Groq is successfully called in live mode.
- [ ] Demo mode works without Groq.
- [ ] Invalid API responses are handled gracefully.

## Policy

- [ ] Two workflow policies load.
- [ ] Policies validate.
- [ ] Workflow-specific behavior differs.
- [ ] Policy version is recorded in audit.

## Detection

- [ ] PII detection works on seeded examples.
- [ ] Retrieval returns relevant evidence.
- [ ] NLI distinguishes entailment/contradiction on seeded examples.
- [ ] Unverified evidence is represented explicitly.
- [ ] Uncertainty sampling works when enabled.

## Decisions

- [ ] Allow works.
- [ ] Edit/redaction works.
- [ ] Regeneration works.
- [ ] Escalation works.
- [ ] Block works.

## Tools

- [ ] Simulated tool executes only after gate approval.
- [ ] Amount limit is enforced.
- [ ] Unsupported-claim-backed tool calls are prevented.

## Governance

- [ ] Budget accounting works.
- [ ] Bias dashboard works on seeded data.
- [ ] Audit chain verifies.
- [ ] Tampering test fails verification.

## Evaluation

- [ ] `pytest` passes.
- [ ] Evaluation script produces metrics.
- [ ] Latency metrics are measured.
- [ ] Token/cost metrics are recorded.

## Demo

- [ ] D01–D12 scenarios run deterministically.
- [ ] Full hero scenario can be completed repeatedly.
- [ ] Offline/replay mode works.
- [ ] UI clearly explains every major decision.

---

# 22. Recommended repository structure

```text
controlplane/
├── app.py                         # Streamlit entrypoint
├── gateway/app.py                 # FastAPI OpenAI-compatible gateway
├── requirements.txt
├── .env.example
├── README.md
├── Makefile
├── pyproject.toml
│
├── config/
│   ├── settings.py
│   └── pricing.yaml
│
├── policy/
│   ├── engine.py
│   ├── schema.py
│   └── workflows/
│       ├── refund-copilot.yaml
│       └── internal-summarizer.yaml
│
├── llm/
│   ├── groq_client.py
│   ├── schemas.py
│   └── prompts.py
│
├── retrieval/
│   ├── embedder.py
│   ├── index.py
│   └── retriever.py
│
├── checks/
│   ├── pii.py
│   ├── claims.py
│   ├── nli.py
│   ├── uncertainty.py
│   ├── tools.py
│   └── router.py
│
├── decision/
│   ├── engine.py
│   ├── budget.py
│   └── models.py
│
├── tools/
│   ├── registry.py
│   ├── simulated_tools.py
│   └── gateway.py
│
├── audit/
│   ├── store.py
│   ├── chain.py
│   └── verify.py
│
├── storage/
│   └── database.py
│
├── demo/
│   ├── scenarios.py
│   ├── fixtures/
│   └── replay.py
│
├── corpus/
│   └── *.md
│
├── evaluation/
│   ├── dataset.py
│   ├── metrics.py
│   └── run_eval.py
│
├── ui/
│   ├── pages/
│   └── components/
│
└── tests/
    ├── test_policy.py
    ├── test_pii.py
    ├── test_retrieval.py
    ├── test_nli.py
    ├── test_decision.py
    ├── test_budget.py
    ├── test_tools.py
    ├── test_audit.py
    └── test_scenarios.py
```

---

# 23. Prerequisites before coding

## Required

### Software

- Python 3.11 or 3.12.
- Git.
- A code editor/terminal.
- Internet access for:
  - installing Python dependencies;
  - first-time Hugging Face model download;
  - Groq API calls.

### Groq

Create a Groq account/API key.

Set:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=qwen/qwen3.8-27b
CONTROLPLANE_MODE=live
```

Do not commit `.env`.

Groq's official API is OpenAI-compatible at:

`https://api.groq.com/openai/v1`

and Groq provides a model-list endpoint. The application should use the configured model id and validate it rather than assuming permanent availability.

### Local ML models

No separate API keys are required for:

- `sentence-transformers/all-MiniLM-L6-v2`
- `cross-encoder/nli-deberta-v3-base`

The first run downloads the models.

### Python packages

The implementation will install the required packages from `requirements.txt`.

Core packages are expected to include:

- streamlit
- groq
- pydantic
- pyyaml
- python-dotenv
- sentence-transformers
- torch
- numpy
- pandas
- scikit-learn
- pytest
- httpx

Use a compatible `transformers`/`sentence-transformers` stack selected during implementation.

## Optional

- Hugging Face account/token: **not required** for the public models selected.
- GPU: **not required**. CPU is the intended baseline.
- Docker: **not required**.
- Cloud deployment: **not required**.

---

# 24. Environment configuration

Create `.env` locally:

```env
GROQ_API_KEY=
GROQ_MODEL=qwen/qwen3.8-27b

CONTROLPLANE_MODE=live

DATABASE_PATH=data/controlplane.db

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base

UNCERTAINTY_SAMPLES=3
TOP_K_EVIDENCE=3

DEFAULT_WORKFLOW=refund-copilot

LOG_LEVEL=INFO
```

Create `.env.example` with blank secrets.

Never commit:

- `.env`;
- API keys;
- SQLite databases containing real user data;
- model caches;
- private credentials.

---

# 25. Hero demo

The main story should be one continuous scenario.

## Part A — hallucinated policy

User:

> "I bought this product 45 days ago. Can I get a full refund?"

Groq returns a plausible but unsupported answer:

> "Yes, customers are entitled to a full refund within 90 days."

ControlPlane:

```text
CLAIM:
Full refund within 90 days.

SOURCE:
Refund Policy v3

SOURCE:
Full refund within 30 days.

NLI:
CONTRADICTION

SEMANTIC UNCERTAINTY:
HIGH

DECISION:
REGENERATE
```

Grounded regenerated response is released.

## Part B — action attempt

User:

> "Okay, issue the refund."

Model proposes:

```text
issue_refund(amount=8000)
```

ControlPlane:

```text
POLICY MAX:
₹5,000

EVIDENCE:
NOT PASSED

DECISION:
ESCALATE / BLOCK

TOOL EXECUTION:
PREVENTED
```

## Part C — proof

Open the audit record.

Show:

- policy version;
- checks;
- decision;
- latency;
- token/cost data;
- hash-chain status.

This is the primary demo narrative.

---

# 26. Technical principles for implementation

1. **Never use an LLM as the sole truth detector.**
2. **Never treat semantic similarity as entailment.**
3. **Never equate uncertainty with hallucination.**
4. **Never equate missing evidence with contradiction.**
5. **Never execute a gated tool before policy validation.**
6. **Never hide intervention reasons from the UI.**
7. **Never fabricate evaluation metrics.**
8. **Never store secrets in source control.**
9. **Never make production claims from a simulated benchmark.**
10. **Prefer deterministic logic when deterministic logic is sufficient.**

---

# 27. Final architecture decision

The final Round 2 prototype is:

> **Streamlit governance console + Python control layer + Groq generation + local retrieval/NLI/PII + policy-driven decision engine + simulated tool gate + SQLite audit/metrics + deterministic replay/evaluation.**

The core differentiator is not "another AI judge."

It is:

> **Workflow-specific governance that decides when an AI response is sufficiently supported to release, repair, escalate, or act.**

The prototype should leave the judge with three clear impressions:

1. **The same model can be governed differently by workflow.**
2. **ControlPlane knows when evidence is missing instead of pretending certainty.**
3. **An AI-generated action can be stopped before it executes.**


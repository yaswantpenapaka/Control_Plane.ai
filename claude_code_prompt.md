# Claude Code Master Prompt — ControlPlane.ai Round 2 Prototype

## 0. Role

You are Claude Code acting as the **lead implementation engineer** for the Accenture Innovation Challenge 2026 Round 2 prototype **ControlPlane.ai**.

Build the prototype described in `prototype-system-design.md`.

Do not redesign the product unless a requirement is technically impossible. When a design choice is ambiguous, prefer the smallest implementation that proves the intended mechanism and is deterministic enough for a live competition demo.

This is a competition prototype, not a production SaaS platform.

---

# 1. Non-negotiable product definition

ControlPlane.ai is:

> **AI governance middleware that sits between an enterprise AI application and its model provider, applying workflow-specific policies to generated responses and proposed actions before they reach a user or execute a tool.**

Core loop:

> **Declare → Inspect → Verify → Decide → Intervene → Audit**

Core product message:

> **Models generate. ControlPlane governs.**

Do not reposition the project as a generic chatbot, a universal hallucination detector, or another LLM judge.

---

# 2. Source-of-truth documents

Before writing code:

1. Read `prototype-system-design.md` completely.
2. Read the existing Round 1 submission if it is present in the repository.
3. Preserve the ControlPlane terminology:
   - error/risk budget;
   - workflow-specific governance;
   - entailment, not similarity;
   - least-disruptive intervention;
   - tool-call gate;
   - tamper-evident audit;
   - confidence is not correctness.
4. If the design document and this prompt conflict, this prompt controls implementation details and the design document controls product intent.
5. Do not add unrelated features.

---

# 3. Critical architecture decision

Use:

```text
Client/demo app
      |
      | OpenAI-compatible /v1/chat/completions
      v
FastAPI ControlPlane Gateway
      |
      +---- Policy Engine
      |
      +---- Groq Upstream
      |
      +---- Lane A deterministic checks
      |
      +---- Risk Router
      |
      +---- Lane B evidence/uncertainty checks
      |
      +---- Decision Engine
      |
      +---- Tool Gate
      |
      +---- Audit / SQLite
      |
      v
Streamlit Governance Console
```

### Important

**Streamlit is the primary UI.**

**FastAPI is the runtime gateway.**

Do not attempt to implement a custom OpenAI-compatible HTTP gateway purely inside Streamlit.

The gateway is required because the prototype must demonstrate the Round 1 "one-line base URL" integration concept.

---

# 4. Runtime modes

Implement three modes.

## 4.1 LIVE

```env
CONTROLPLANE_MODE=live
```

Flow:

```text
Client → ControlPlane → Groq → checks → decision → response
```

This requires `GROQ_API_KEY`.

## 4.2 DEMO

```env
CONTROLPLANE_MODE=demo
```

Use deterministic seeded upstream responses and expected scenarios.

The demo must not depend on Groq producing the exact desired hallucination on camera.

## 4.3 REPLAY

```env
CONTROLPLANE_MODE=replay
```

Replay recorded/cached responses and evaluation artifacts.

This is the emergency offline mode.

The UI must clearly display the current mode.

Never pretend replay output came from a live Groq call.

---

# 5. Groq integration

Use the official Groq Python SDK unless there is a strong reason to use another compatible client.

Environment:

```env
GROQ_API_KEY=
GROQ_MODEL=qwen/qwen3.8-27b
```

The model must be configurable.

Do not scatter model ids through the source.

Create:

```text
llm/groq_client.py
```

Responsibilities:

- initialize Groq client;
- make chat completion calls;
- handle tool calls;
- handle structured claim extraction;
- expose usage metadata;
- retry transient failures safely;
- normalize Groq responses into internal models;
- never log the API key.

Do not hard-code the API key.

At startup:

- fail with a clear message if LIVE mode has no API key;
- validate that the configured model is available if practical;
- do not make the whole application unusable in DEMO/REPLAY mode when the key is absent.

---

# 6. Model strategy

Do NOT use Ollama.

Do NOT require another paid LLM API.

Use Groq for:

- user-facing generation;
- claim extraction;
- evidence-grounded regeneration;
- uncertainty sampling.

Use local models for:

- embeddings;
- NLI.

Use deterministic code for:

- PII;
- secrets;
- tool constraints;
- budget accounting;
- audit hashing.

Recommended local models:

```text
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base
```

These must load lazily or at startup with friendly progress/errors.

CPU must work.

GPU acceleration is optional.

---

# 7. Repository to create

Create:

```text
controlplane/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Makefile
├── pyproject.toml
│
├── gateway/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   └── service.py
│
├── policy/
│   ├── __init__.py
│   ├── engine.py
│   ├── schema.py
│   └── workflows/
│       ├── refund-copilot.yaml
│       └── internal-summarizer.yaml
│
├── llm/
│   ├── __init__.py
│   ├── groq_client.py
│   ├── prompts.py
│   └── schemas.py
│
├── retrieval/
│   ├── __init__.py
│   ├── documents.py
│   ├── embedder.py
│   ├── index.py
│   └── retriever.py
│
├── checks/
│   ├── __init__.py
│   ├── pii.py
│   ├── claims.py
│   ├── nli.py
│   ├── uncertainty.py
│   ├── router.py
│   └── tools.py
│
├── decision/
│   ├── __init__.py
│   ├── models.py
│   ├── engine.py
│   └── budget.py
│
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   ├── simulated_tools.py
│   └── gate.py
│
├── audit/
│   ├── __init__.py
│   ├── store.py
│   ├── chain.py
│   └── verify.py
│
├── storage/
│   ├── __init__.py
│   └── database.py
│
├── demo/
│   ├── __init__.py
│   ├── scenarios.py
│   ├── fixtures.py
│   └── replay.py
│
├── corpus/
│   ├── refund_policy_v3.md
│   ├── refund_policy_exceptions.md
│   ├── chargeback_policy.md
│   ├── customer_tier_policy.md
│   ├── international_refund_policy.md
│   ├── digital_goods_policy.md
│   ├── merchant_dispute_policy.md
│   ├── escalation_policy.md
│   ├── tool_authorization_policy.md
│   └── privacy_policy.md
│
├── evaluation/
│   ├── __init__.py
│   ├── dataset.py
│   ├── metrics.py
│   └── run_eval.py
│
├── ui/
│   ├── __init__.py
│   ├── components.py
│   └── pages/
│       ├── live_control.py
│       ├── decision_inspector.py
│       ├── policy_center.py
│       ├── risk_budget.py
│       ├── bias_monitor.py
│       ├── audit_explorer.py
│       ├── evaluation.py
│       └── demo_scenarios.py
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
    ├── test_scenarios.py
    └── test_gateway.py
```

If a simpler structure is demonstrably cleaner, you may consolidate files, but preserve the separation of concerns.

---

# 8. Internal data contracts

Use Pydantic models.

Create clear models for:

```text
ChatRequest
ChatResponse
WorkflowPolicy
Claim
EvidenceChunk
ClaimVerification
LaneAResult
LaneBResult
RiskAssessment
ToolCallRequest
ToolDecision
DecisionResult
BudgetState
AuditEvent
EvaluationCase
EvaluationResult
```

Do not pass untyped dictionaries everywhere.

Use enums where appropriate:

```text
RiskState:
    ENTAILED
    CONTRADICTED
    UNVERIFIED
    UNCERTAIN

Decision:
    ALLOW
    EDIT
    REGENERATE
    ESCALATE
    BLOCK
```

---

# 9. Policy engine

Implement YAML loading and validation.

Required workflow fields:

```yaml
workflow:
risk_tier:

error_budget:
  target:
  window:

latency_budget_ms:

evidence:
  required:
  min_entailment:
  abstain_without_evidence:

privacy:
  pii:
  action_on_hit:

tools:

interventions:
  ladder:
  max_regenerations:
```

Support at least:

```text
refund-copilot
internal-summarizer
```

Policy must be immutable for an individual request.

Compute a stable policy version/hash and store it in audit records.

Do not implement a complicated policy UI.

---

# 10. Refund policy corpus

Create a fictional bank.

Use clearly fictional names.

Example:

```text
FictionalBank
```

The active policy must state:

> Full refunds are generally permitted within 30 days of purchase, subject to listed exceptions.

Create an older document with:

> 90 days

but mark it as superseded.

The retrieval system must prefer the active document.

This creates the central contradiction scenario.

Do not use real bank policies.

---

# 11. Retrieval

Implement a small local vector index.

At startup:

1. read corpus files;
2. parse metadata;
3. chunk documents;
4. generate embeddings;
5. normalize vectors;
6. store in memory.

For a query:

```text
retrieve(query, top_k=3)
```

Return:

```text
document_id
title
version
effective_date
content
similarity
```

Retrieval similarity is only for finding candidates.

Do NOT call similarity a truth score.

---

# 12. Claim extraction

Use Groq structured output.

The extractor should return atomic claims only.

Example schema:

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

Do not ask the extractor whether the claim is true.

Do not let the extractor determine the final decision.

If structured output fails:

1. retry once;
2. attempt safe JSON parsing if supported;
3. otherwise mark claim extraction unavailable and route high-risk requests to escalation.

Never crash the gateway because claim extraction failed.

---

# 13. NLI

Use:

```text
cross-encoder/nli-deberta-v3-base
```

For each claim and retrieved evidence chunk, obtain probabilities for:

- entailment;
- neutral;
- contradiction.

Return a normalized result.

Aggregation rules must be explicit and testable.

A reasonable initial rule:

```text
if best_evidence_entailment >= min_entailment:
    ENTAILED

elif best_evidence_contradiction >= contradiction_threshold:
    CONTRADICTED

else:
    UNVERIFIED
```

If different claims have conflicting states, preserve claim-level results and use a conservative response-level aggregation.

Do not silently mark all neutral cases as hallucinations.

---

# 14. Semantic uncertainty

Implement only for eligible cases.

Use `k=3` additional Groq generations.

Do not rely on Groq `n=3`; make three explicit calls because API compatibility does not guarantee multi-choice generation behavior.

Use a non-zero temperature.

Compare generated answers using the local NLI model.

Two answers are semantically equivalent when bidirectional entailment passes a configurable threshold.

Cluster equivalent answers.

Calculate:

```text
H = -Σ p_i log(p_i)
```

Normalize if useful for UI:

```text
normalized_entropy = H / log(number_of_clusters)
```

Handle the one-cluster case as zero entropy.

Label the result:

```text
LOW
MEDIUM
HIGH
```

based on configurable thresholds.

Critical wording:

> Semantic uncertainty is an uncertainty signal. It is not a hallucination probability and is not proof of falsehood.

If one sample is malformed, do not crash the entire decision. Record the sampling failure.

---

# 15. PII

Implement deterministic detection.

At minimum:

- email;
- phone;
- PAN;
- Aadhaar;
- account number;
- API key-like secrets.

Return spans and entity types.

Use replacement:

```text
[REDACTED:EMAIL]
[REDACTED:PHONE]
...
```

Do not store the original sensitive value in the audit record.

Store:

- entity type;
- count;
- span hash if useful.

Do not claim complete DLP coverage.

---

# 16. Risk router

Lane A always runs.

Lane B should run when:

```text
policy.evidence.required
OR risk_tier == high
OR tool_call_present
OR factual_claim_density_is_high
OR lane_a_relevant_flag
OR budget_burn_is_high
```

The router returns explicit reason codes.

Example:

```json
{
  "route_to_lane_b": true,
  "reasons": [
    "HIGH_RISK_WORKFLOW",
    "EVIDENCE_REQUIRED",
    "FACTUAL_CLAIM_DETECTED"
  ]
}
```

The Streamlit UI must display these.

---

# 17. Decision engine

Implement the ladder:

```text
allow
edit
regenerate
escalate
block
```

Rules:

### ALLOW

Use when:

- no hard policy violation;
- evidence requirements pass or are not required;
- no unresolved critical uncertainty;
- tool call passes gate if present.

### EDIT

Use when:

- PII can be safely redacted;
- no other critical failure exists.

### REGENERATE

Use when:

- evidence contradicts or fails;
- trusted source evidence exists;
- max regeneration count not reached;
- regeneration can be grounded.

Regenerate with evidence pinned.

Re-run checks after regeneration.

### ESCALATE

Use when:

- no trusted evidence exists for a required claim;
- regeneration fails;
- gated tool reasoning is unresolved;
- policy requires human review;
- uncertainty is too high.

### BLOCK

Use when:

- hard prohibited action;
- hard tool constraint violation;
- policy explicitly requires block;
- severe budget-control state requires block.

Do not block every uncertain answer.

---

# 18. Regeneration

Grounded regeneration prompt must include:

- original user request;
- relevant conversation;
- retrieved evidence;
- explicit instruction to answer only from evidence;
- instruction to say information is unavailable when evidence does not support an answer.

Example intent:

```text
You are revising an enterprise response.

Use only the supplied evidence for policy facts.
Do not invent policy details.
If the evidence does not support the requested fact, say that the information
cannot be verified and ask for human review.
```

After regeneration:

1. run PII checks;
2. extract claims;
3. retrieve evidence;
4. run NLI;
5. determine final state;
6. only release if policy passes.

Never release a regenerated response merely because the model sounds better.

---

# 19. Tool calling

Define simulated tools:

```text
issue_refund
lookup_customer
cancel_subscription
change_address
```

At minimum implement:

```text
issue_refund(customer_id, amount)
```

The tool gateway must be separate from the LLM client.

The LLM proposes a tool call.

ControlPlane decides whether it can execute.

Only the simulated tool registry may execute the function.

Never let model output directly execute Python functions.

---

# 20. Tool policy

For:

```yaml
issue_refund:
  gate: true
  max_amount: 5000
```

Require:

- valid tool name;
- valid JSON arguments;
- amount numeric;
- amount <= max;
- no budget-exhausted prohibition;
- no unsupported-claim dependency;
- evidence requirements satisfied.

Return a structured tool decision.

Example:

```json
{
  "allowed": false,
  "decision": "ESCALATE",
  "reason_codes": [
    "TOOL_AMOUNT_LIMIT_EXCEEDED",
    "EVIDENCE_NOT_PASSED"
  ]
}
```

---

# 21. Multi-turn state

Use SQLite or in-memory session state for the prototype.

Track:

```text
session_id
workflow
conversation
unresolved_risks
evidence_refs
previous_decisions
```

Do not store secrets or raw sensitive PII.

The tool gate must be able to see whether the current action depends on an unresolved earlier risk.

---

# 22. Error/risk budget

Implement:

```text
BudgetAccountant
```

It must track:

- target;
- window;
- consumed events;
- total eligible requests;
- burn rate;
- budget state.

Use seeded timestamps for deterministic evaluation.

Suggested states:

```text
HEALTHY
WATCH
TIGHTEN
EXHAUSTED
```

As state worsens:

```text
HEALTHY
→ normal routing

WATCH
→ more Lane B

TIGHTEN
→ stricter escalation

EXHAUSTED
→ high-risk actions may block/escalate
```

Do not dynamically alter `min_entailment` in a confusing way unless it is explicitly configured. Prefer clear policy changes.

---

# 23. Bias monitor

Use simulated cohort data.

Do not infer bias from one response.

Implement:

```text
cohort
decision
outcome
```

Calculate:

```text
positive_rate_by_cohort
disparity
selection_rate_ratio
```

Display:

> Population-level monitoring — simulated data

Do not use protected attributes unless necessary for the scenario.

Use generic cohort labels such as:

```text
Cohort A
Cohort B
```

---

# 24. Audit chain

Implement SQLite persistence.

For each decision:

1. create canonical JSON;
2. hash it with SHA-256;
3. include previous hash;
4. write the record;
5. calculate/store current hash.

Important:

```text
prev_hash = previous_record.record_hash
```

The first record has:

```text
prev_hash = GENESIS
```

Implement:

```bash
python -m audit.verify
```

Output:

```text
AUDIT CHAIN: VALID
records_checked: 37
```

or:

```text
AUDIT CHAIN: BROKEN
first_invalid_record: 18
reason: previous_hash mismatch
```

Do not call this a digital signature.

---

# 25. SQLite

Use SQLite.

Create tables with migrations or idempotent initialization.

Do not require Postgres/Supabase.

The prototype should start from an empty directory.

Database path configurable through:

```env
DATABASE_PATH=data/controlplane.db
```

---

# 26. Streamlit UI

The UI must feel like an enterprise governance console.

Do not make it look like a generic chatbot.

Use:

- clear status badges;
- decision colors only where helpful;
- expandable evidence;
- policy summaries;
- metrics;
- audit status.

Do not overdesign.

---

# 27. Streamlit pages

## Live Control

Controls:

- workflow;
- mode;
- user prompt;
- optional cohort;
- send button.

Show:

```text
MODEL RESPONSE
CONTROLPLANE RESPONSE
DECISION
RISK STATE
REASONS
LATENCY
TOKENS
ESTIMATED COST
TOOL STATUS
```

## Decision Inspector

Show:

```text
Request
↓
Lane A
↓
Risk Router
↓
Claims
↓
Evidence
↓
NLI
↓
Uncertainty
↓
Policy
↓
Decision
```

Every step must be understandable to a non-developer judge.

## Policy Center

Show YAML-derived policy cards.

## Risk & Budget

Show:

- current burn;
- target;
- intervention distribution;
- Lane A/B routing;
- regeneration/rework;
- token/cost telemetry;
- latency.

## Bias Monitor

Show simulated cohort analytics.

## Audit Explorer

Show recent records and chain verification.

## Evaluation

Show measured benchmark metrics.

## Demo Scenarios

Buttons:

```text
D01 Grounded
D02 Hallucination
D03 No Evidence
D04 PII
D05 Tool Allowed
D06 Tool Over Limit
D07 Unsupported Tool
D08 Workflow Difference
D09 Budget Pressure
D10 Multi-turn
D11 Bias
D12 Audit Tamper
```

---

# 28. Demo scenario contracts

Create deterministic fixtures.

Each scenario should specify:

```python
Scenario(
    id="D02",
    name="Unsupported refund policy",
    workflow="refund-copilot",
    user_messages=[...],
    upstream_response=...,
    expected_risk_state="CONTRADICTED",
    expected_decision="REGENERATE",
)
```

The scenario runner must verify actual vs expected.

If a deterministic scenario fails, display:

```text
SCENARIO FAILED
expected: REGENERATE
actual: ALLOW
```

Do not hide failures.

---

# 29. Hero scenario

Make this work perfectly.

## Input

```text
I bought this product 45 days ago. Can I get a full refund?
```

## Seeded model answer

```text
Yes. Customers are entitled to a full refund within 90 days.
```

## Evidence

Active policy says:

```text
Full refunds are generally permitted within 30 days.
```

## Expected

```text
NLI:
CONTRADICTION

UNCERTAINTY:
HIGH

DECISION:
REGENERATE
```

## Grounded regeneration

Expected final response:

```text
According to the current refund policy, full refunds are generally
available within 30 days, subject to the listed exceptions.
```

Then:

```text
User:
Okay, issue the refund.
```

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

Expected:

```text
TOOL:
BLOCKED / ESCALATED

REASON:
AMOUNT_LIMIT_EXCEEDED

TOOL EXECUTED:
NO
```

This is the primary video flow.

---

# 30. Evaluation dataset

Create approximately:

```text
20 grounded
15 unsupported/contradicted
10 PII
8 tool calls
7 cohort replay batches
```

Each case needs an oracle.

Example:

```python
EvaluationCase(
    id="H01",
    category="unsupported_claim",
    expected_risk_state="CONTRADICTED",
    expected_decision="REGENERATE",
)
```

Run:

```bash
python -m evaluation.run_eval
```

Produce:

```text
evaluation/results.json
evaluation/report.md
```

Do not commit fake results.

---

# 31. Metrics

Implement:

```text
precision
recall
false_positive_rate
false_negative_rate
PII redaction recall
tool gate accuracy
regeneration success
budget adherence
latency p50
latency p95
average input tokens
average output tokens
estimated cost
additional rework tokens
```

The report must state:

> Results are from a seeded/simulated prototype benchmark and do not represent production accuracy.

---

# 32. Live evaluation vs deterministic evaluation

Do not make the official benchmark depend entirely on live Groq behavior.

Use deterministic fixtures for correctness evaluation.

Optionally provide a live smoke test:

```bash
python -m evaluation.run_live_smoke
```

but keep it separate.

This prevents model drift, quota, or provider changes from destroying reproducibility.

---

# 33. Error handling

The app must never expose stack traces to judges.

Handle:

- missing API key;
- invalid model;
- Groq timeout;
- rate limit;
- malformed tool call;
- NLI model load failure;
- embedding model load failure;
- malformed policy;
- database failure;
- structured output failure.

For each, show a human-readable message.

Example:

```text
Groq is unavailable.

Switching to DEMO/REPLAY mode is recommended for deterministic presentation.
```

Do not silently fall back from LIVE to DEMO.

The user must know which mode is active.

---

# 34. Security requirements

- `.env` in `.gitignore`.
- `.env.example` only.
- Never print API keys.
- Never store raw PII in audit records.
- Never execute arbitrary model-generated Python.
- Tool calls go through an allowlisted registry.
- No real banking integrations.
- No external side effects.

---

# 35. Requirements

Use Python 3.11+.

Keep dependencies minimal.

Likely dependencies:

```text
streamlit
fastapi
uvicorn
groq
pydantic
pydantic-settings
python-dotenv
pyyaml
sentence-transformers
torch
numpy
pandas
scikit-learn
httpx
pytest
```

Use versions compatible with the current environment.

Do not pin arbitrary old versions just to make the file look precise.

After installing, run the full test suite.

---

# 36. Commands to support

At minimum:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run gateway:

```bash
uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

Run UI:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest
```

Run evaluation:

```bash
python -m evaluation.run_eval
```

Verify audit:

```bash
python -m audit.verify
```

If a Makefile is included:

```bash
make install
make test
make eval
make gateway
make ui
```

---

# 37. OpenAI-compatible demo client

Create a tiny client demonstrating the integration.

Use:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="controlplane-demo"
)
```

The important demonstration is that the application points to ControlPlane instead of the upstream provider.

The ControlPlane gateway itself calls Groq.

Document the integration clearly.

Do not claim that the gateway supports every OpenAI feature.

Support only the subset implemented by the prototype:

- chat completions;
- messages;
- model;
- temperature;
- tools/tool calls as needed by the scenarios.

---

# 38. API contract

Implement:

```text
POST /v1/chat/completions
```

and:

```text
GET /health
GET /v1/controlplane/health
```

Health response should show:

```json
{
  "status": "ok",
  "mode": "live",
  "groq_configured": true,
  "policy_loaded": true,
  "embedding_loaded": true,
  "nli_loaded": true
}
```

Do not expose secrets.

---

# 39. Streamlit architecture

`app.py` should:

1. initialize services once using caching;
2. load configuration;
3. initialize database;
4. expose navigation;
5. call the gateway/service layer;
6. render decision details.

Do not put the entire business logic into `app.py`.

---

# 40. Testing

Write tests before declaring completion.

Minimum tests:

## Policy

- valid policy loads;
- invalid policy rejected;
- version hash stable.

## PII

- email detected;
- phone detected;
- PAN detected;
- account number detected;
- redaction does not leak original value.

## Retrieval

- active refund policy retrieved for refund query;
- superseded policy is lower priority when effective metadata is considered.

## NLI

- known supported claim → entailment;
- known wrong claim → contradiction;
- unrelated claim → unverified/neutral.

## Decision

- safe → allow;
- PII only → edit;
- contradicted + source → regenerate;
- no evidence high-risk → escalate;
- prohibited tool → block.

## Budget

- consumption increments;
- target calculation correct;
- state transitions correct.

## Tools

- allowed amount executes;
- excessive amount does not execute;
- unsupported-claim-backed tool call does not execute.

## Audit

- chain validates;
- tampered record fails.

## Scenarios

All D01–D12 deterministic cases pass.

---

# 41. README requirements

Create a strong README.

Top:

```text
# ControlPlane.ai

### Models generate. ControlPlane governs.
```

Then:

1. problem;
2. solution;
3. architecture diagram;
4. key mechanisms;
5. demo screenshots/placeholders;
6. quickstart;
7. environment variables;
8. demo scenarios;
9. evaluation;
10. limitations;
11. repository structure;
12. video link placeholder;
13. competition context.

Do not write generic AI hype.

Be precise.

---

# 42. Architecture diagram

The README must include a Mermaid or ASCII diagram.

Prefer Mermaid if GitHub rendering is clean.

Show:

```text
Client
 ↓
FastAPI Gateway
 ↓
Policy Engine
 ↓
Groq
 ↓
Lane A
 ↓
Risk Router
 ↓
Lane B
 ├─ Claims
 ├─ Retrieval
 ├─ NLI
 └─ Uncertainty
 ↓
Decision
 ├─ Response
 └─ Tool Gate
 ↓
Audit
 ↓
Streamlit
```

---

# 43. UI quality requirements

The judge should understand the system without opening source code.

Every decision card should include:

```text
DECISION
RISK STATE
WHY
EVIDENCE
POLICY
ACTION
LATENCY
COST
AUDIT
```

Example:

```text
REGENERATE

Risk:
CONTRADICTED

Why:
Refund claim conflicts with active policy.

Evidence:
Refund Policy v3 · effective 2026-08-01

NLI:
Contradiction 0.94

Action:
Regenerated with evidence pinned.

Audit:
✓ recorded
```

---

# 44. Do not make these implementation mistakes

## Do not

- use Ollama;
- call Groq for NLI;
- call embeddings through an API;
- use an LLM as sole truth judge;
- equate cosine similarity with entailment;
- call semantic entropy a hallucination probability;
- call missing evidence a contradiction;
- execute arbitrary model tool calls;
- hard-code secrets;
- fabricate benchmark numbers;
- add Kubernetes;
- add authentication for show;
- add a production vector database;
- build a full policy-management SaaS;
- build unnecessary agents;
- use real financial systems.

---

# 45. Demo reliability

The prototype is being judged live.

Implement:

### Preload

Load local models once.

### Cache

Cache corpus embeddings.

### Replay

Cache deterministic upstream outputs.

### Timeouts

Use bounded Groq timeouts.

### Clear mode

Always show:

```text
LIVE
DEMO
REPLAY
```

### Reset

Provide:

```text
Reset demo data
```

to restore deterministic dashboard state.

---

# 46. Performance

Do not optimize prematurely.

Measure.

Use caching for:

- embedding model;
- NLI model;
- corpus index;
- policy configuration.

Avoid:

- loading models per request;
- rebuilding embeddings per request;
- unnecessary Groq calls;
- semantic uncertainty on low-risk requests.

---

# 47. Implementation order

Build in this order.

## Phase 1

Repository + configuration + models + policy engine.

## Phase 2

Groq client + FastAPI gateway + simple pass-through.

## Phase 3

SQLite + audit chain.

## Phase 4

Lane A:

- PII;
- tool policy;
- telemetry.

## Phase 5

Retrieval + NLI.

## Phase 6

Claim extraction.

## Phase 7

Decision engine + regeneration.

## Phase 8

Tool gate.

## Phase 9

Uncertainty sampling.

## Phase 10

Budget accountant + bias analytics.

## Phase 11

Streamlit UI.

## Phase 12

Deterministic scenarios + evaluation.

## Phase 13

Tests + README + polish.

At every phase, keep the previous working behavior intact.

---

# 48. Acceptance gate before declaring done

Do not say "done" until:

```text
[ ] python environment installs successfully
[ ] demo mode starts without Groq
[ ] live mode works with Groq
[ ] gateway health works
[ ] Streamlit starts
[ ] policy files validate
[ ] corpus loads
[ ] embeddings load
[ ] NLI loads
[ ] D01 passes
[ ] D02 passes
[ ] D03 passes
[ ] D04 passes
[ ] D05 passes
[ ] D06 passes
[ ] D07 passes
[ ] D08 passes
[ ] D09 passes
[ ] D10 passes
[ ] D11 passes
[ ] D12 passes
[ ] audit verification passes
[ ] tamper test detects corruption
[ ] pytest passes
[ ] evaluation runs
[ ] README quickstart works
[ ] no secret is committed
```

---

# 49. Final self-review before completion

After implementation, inspect the repository as a competition judge.

Ask:

### Product

Can I explain ControlPlane in 20 seconds?

### Technical

Can I understand why a response was allowed or stopped?

### Evidence

Can I see the exact source used for a decision?

### Governance

Can I see that two workflows behave differently?

### Action safety

Can I see that an unsafe tool call never executed?

### Uncertainty

Can I see that the system abstains when evidence is missing?

### Audit

Can I verify that a decision record was tampered with?

### Evaluation

Can I see measured metrics rather than claims?

### Reliability

Can the demo run offline?

If any answer is no, fix it before adding features.

---

# 50. Final instruction to Claude Code

Build the system.

Do not merely create placeholders.

Do not stop at architecture.

Do not fabricate functionality.

Do not fabricate evaluation results.

Do not fabricate latency or cost numbers.

If a feature cannot be implemented reliably, implement the smallest honest version and document the limitation.

The final prototype should be **small, understandable, testable, repeatable, and visually convincing**.

The goal is not to demonstrate how many technologies were used.

The goal is to make the following statement demonstrably true:

> **ControlPlane can govern an AI workflow differently according to its risk, verify claims against trusted evidence when evidence exists, abstain when evidence is insufficient, prevent unsafe AI actions, and produce an auditable record of the decision.**

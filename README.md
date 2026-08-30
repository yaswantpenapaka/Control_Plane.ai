# ControlPlane-ai

### Models generate. ControlPlane governs.

**ControlPlane-ai** is an AI governance middleware that sits between an enterprise AI application and its model provider, applying workflow-specific policies to generated responses and proposed actions before they reach a user or execute a tool.

---

## Problem

Modern AI systems generate fluent, confident responses that can be:

1. **Confidently wrong** — Unsupported claims reach users without verification
2. **Quietly expensive** — Unnecessary model calls and rework remain untracked
3. **Subtly biased** — Outcome disparities are invisible in individual responses

## Solution

ControlPlane-ai implements a **workflow-specific governance layer** with:

- **Evidence verification** — Claims are checked against trusted local evidence using NLI
- **Risk routing** — Cheap checks handle all traffic; expensive verification runs only when needed
- **Least-disruptive intervention** — ALLOW → EDIT → REGENERATE → ESCALATE → BLOCK
- **Tool-call gating** — AI-generated actions pass policy validation before execution
- **Error budgeting** — Workflows declare a ceiling on tolerated risk
- **Tamper-evident audit** — Hash-chained decision records

---

## Architecture

```
Client/Demo App
      ↓
FastAPI Gateway (OpenAI-compatible /v1/chat/completions)
      ↓
Policy Engine (YAML-driven workflow definitions)
      ↓
Groq Upstream (LLM generation)
      ↓
Lane A (Deterministic checks: PII, tool policy, safety keywords)
      ↓
Risk Router (Decide whether Lane B is needed)
      ↓
Lane B (Evidence & uncertainty: retrieval, NLI, claim extraction)
      ↓
Decision Engine (ALLOW/EDIT/REGENERATE/ESCALATE/BLOCK)
      ↓
Audit & SQLite
      ↓
Streamlit Governance Console
```

---

## Key Mechanisms

### P1 — One Integration Boundary

A demo client uses an OpenAI-compatible interface:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="controlplane-demo"
)

response = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": "Can I get a refund?"}],
)
```

### P2 — Governance Differs by Workflow

The same Groq model receives different governance:

- **refund-copilot** (high-risk): Evidence required, tool gating enabled, strict budget
- **internal-summarizer** (low-risk): Evidence optional, no tool gating, relaxed budget

### P3 — Confidence is Not Correctness

A fluent response is verified using **local retrieval + NLI**, not LLM confidence:

- **ENTAILED** — Evidence supports the claim
- **CONTRADICTED** — Evidence conflicts with the claim
- **UNVERIFIED** — Insufficient trusted evidence
- **UNCERTAIN** — Generation signals are inconsistent

### P4 — Uncertainty is Handled Honestly

The system abstracts when evidence is missing instead of pretending certainty.

### P5 — Least-Disruptive Intervention

```
ALLOW → EDIT (PII redaction) → REGENERATE (with evidence) → ESCALATE (human review) → BLOCK
```

### P6 — AI Actions are Governed Before Execution

```json
{
  "tool_call": "issue_refund",
  "arguments": {"customer_id": "C-1042", "amount": 8000},
  "policy_max": 5000,
  "decision": "ESCALATE"
}
```

---

## Runtime Modes

### LIVE

```env
CONTROLPLANE_MODE=live
GROQ_API_KEY=your_key
```

Connects to Groq for real-time generation.

### DEMO

```env
CONTROLPLANE_MODE=demo
```

Uses deterministic seeded responses. No Groq API key required.

### REPLAY

```env
CONTROLPLANE_MODE=replay
```

Cached responses and evaluation artifacts. Offline mode for demos.

---

## Quick Start

### 1. Clone & Setup

```bash
cd controlplane
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

For LIVE mode, add your Groq API key:

```env
GROQ_API_KEY=your_key_here
CONTROLPLANE_MODE=live
```

For DEMO mode (no key needed):

```env
CONTROLPLANE_MODE=demo
```

### 4. Start the FastAPI Gateway

```bash
uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

You should see:
```
ControlPlane Gateway starting in DEMO mode
Loaded 2 workflows: ['refund-copilot', 'internal-summarizer']
```

### 5. Start the Streamlit UI

In a new terminal:

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

### 6. Run Tests

```bash
pytest
```

### 7. Verify Audit Chain

```bash
python -m audit.verify
```

Should output:
```
✓ AUDIT CHAIN: VALID
  records_checked: 0
```

---

## Hero Demo Scenario

### Part A: Hallucinated Policy

**User:**
> "I bought this product 45 days ago. Can I get a full refund?"

**Groq generates:**
> "Yes, customers are entitled to a full refund within 90 days."

**ControlPlane:**
- Retrieves active policy: "Full refund within **30 days**"
- NLI: **CONTRADICTION** (0.94 confidence)
- Uncertainty: **HIGH**
- **Decision: REGENERATE**

**Grounded regeneration returns:**
> "According to the current refund policy, full refunds are available within 30 days."

### Part B: Action Attempt

**User:**
> "Okay, issue the refund."

**Groq proposes:**
```json
{
  "tool": "issue_refund",
  "amount": 8000
}
```

**ControlPlane:**
- Policy max: ₹5,000
- Evidence state: UNVERIFIED (policy claims conflict remains)
- **Decision: ESCALATE / BLOCK**
- **Tool execution: PREVENTED**

### Part C: Audit Proof

Open the audit record and verify:
- Policy version hash
- Decision chain
- Evidence used
- Latency (ms) and token count

---

## Environment Variables

```env
GROQ_API_KEY=                    # Groq API key (LIVE mode only)
GROQ_MODEL=qwen/qwen3.8-27b    # Model ID
CONTROLPLANE_MODE=demo           # live | demo | replay
DATABASE_PATH=data/controlplane.db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base
UNCERTAINTY_SAMPLES=3
TOP_K_EVIDENCE=3
DEFAULT_WORKFLOW=refund-copilot
LOG_LEVEL=INFO
```

---

## Demo Scenarios (D01–D12)

- **D01** — Grounded policy answer → **ALLOW**
- **D02** — Hallucinated policy claim → **REGENERATE**
- **D03** — No evidence available → **ESCALATE**
- **D04** — PII leakage → **EDIT**
- **D05** — Tool within policy → **ALLOW**
- **D06** — Tool over limit → **ESCALATE**
- **D07** — Tool backed by unsupported claim → **BLOCK**
- **D08** — Low-risk workflow → Policy-dependent
- **D09** — Budget pressure → Tighter routing
- **D10** — Multi-turn propagation → Action remains gated
- **D11** — Bias batch → Dashboard warning
- **D12** — Audit tampering → Chain verification fails

---

## Policies

### refund-copilot.yaml

High-risk financial workflow:
- Evidence required
- Tool gating enabled (max ₹5,000)
- Error budget: 0.5%

### internal-summarizer.yaml

Low-risk content workflow:
- Evidence optional
- No tool gating
- Error budget: 5%

---

## Evaluation Metrics

The prototype measures:

- **Unsupported-claim recall** — How many contradictions are caught
- **False-positive rate** — How many safe claims are wrongly flagged
- **PII redaction recall** — Span-level accuracy
- **Tool-gate accuracy** — Correct allow/block decisions
- **Latency** — p50 and p95 by phase
- **Cost** — Input/output tokens and estimated spend
- **Budget adherence** — Observed vs. target burn rate

---

## Limitations

This is a **competition prototype**, not a production SaaS platform.

### Out of Scope

- Production authentication/RBAC
- Multi-tenancy
- Real customer/bank data
- Fine-tuned detectors
- Streaming-token interception
- Guaranteed truth detection
- Distributed deployment

### Simulated Components

- Refund policy corpus (fictional bank)
- Tool execution (no real transactions)
- Cohort data (seeded, not real customer cohorts)
- Evaluation metrics (seeded benchmark, not production accuracy)

---

## Repository Structure

```
controlplane/
├── app.py                      # Streamlit UI
├── gateway/app.py              # FastAPI OpenAI-compatible gateway
├── config/settings.py          # Environment & configuration
├── policy/
│   ├── engine.py               # YAML policy loader/validator
│   └── workflows/              # *.yaml policy definitions
├── llm/
│   ├── groq_client.py          # Groq SDK wrapper
│   └── schemas.py              # Pydantic data models
├── retrieval/
│   ├── embedder.py             # Sentence-transformers wrapper
│   ├── documents.py            # Corpus loader
│   └── retriever.py            # Vector search
├── checks/
│   ├── pii.py                  # Deterministic PII detection
│   ├── claims.py               # Claim extraction
│   ├── nli.py                  # NLI verification
│   └── tools.py                # Tool policy validation
├── decision/
│   ├── engine.py               # Decision orchestrator
│   └── budget.py               # Error budget accountant
├── tools/
│   └── simulated_tools.py      # Safe tool mock
├── audit/
│   ├── chain.py                # Hash-chain audit
│   └── verify.py               # Chain verification CLI
├── storage/
│   └── database.py             # SQLite persistence
├── corpus/                      # Fictional bank policies
├── evaluation/                  # Benchmark suite
├── tests/                       # Unit tests
└── requirements.txt
```

---

## Integration Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="controlplane-demo"
)

response = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {
            "role": "user",
            "content": "I bought a digital book 45 days ago. Can I get a refund?"
        }
    ],
    extra_body={
        "workflow": "refund-copilot",
        "cohort": "standard"
    }
)

print(response.choices[0].message.content)
print(response.metadata)
```

---

## Video Submission

[Link to live demo video will be recorded]

---

## Submission

**Team:** VARANASI  
**Challenge:** Accenture Innovation Challenge 2026 — Round 2  
**Prototype:** ControlPlane-ai  
**Submission Deadline:** August 30, 2026

---


**ControlPlane-ai — Governance Layer for AI Workflows**

*"The difference between a model and a system is accountability."*

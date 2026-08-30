# ControlPlane.ai Documentation

Welcome to ControlPlane.ai—a governance system for enterprise LLM applications. This documentation covers everything you need to understand, deploy, and use the platform.

## 📖 Navigation Guide

### For First-Time Users
Start here to get up and running quickly:
- **[Getting Started](GETTING_STARTED.md)** — 5-minute setup guide
- **[Features Overview](FEATURES.md)** — What ControlPlane.ai can do
- **[Examples](EXAMPLES.md)** — Real-world scenarios and use cases

### For Architects & Technical Leaders
Understanding the system design:
- **[Architecture Guide](ARCHITECTURE.md)** — System design, components, decision flow
- **[API Reference](API_REFERENCE.md)** — OpenAI-compatible API documentation
- **[How Policies Work](POLICIES.md)** — Policy definition, configuration, tuning

### For Operators & DevOps
Running the system in production:
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** — Installation, configuration, monitoring
- **[Troubleshooting](TROUBLESHOOTING.md)** — Common issues and solutions

### For Judges & Evaluators
Understanding the innovation:
- **[Judge Reference](JUDGE_REFERENCE.md)** — Competition guide, hero scenarios, metrics

---

## 🚀 Quick Start (2 minutes)

### Prerequisites
- Python 3.10+
- GPU recommended (for NLI model) or CPU-only mode supported
- `pip install -r requirements.txt`

### Run the Demo
```bash
# Terminal 1: Start the governance gateway
uvicorn gateway.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Run demo scenarios
python demo_client.py
```

You'll see three governance scenarios:
1. **Hallucination Detection** — Catches false policy claims
2. **Tool Usage Gating** — Prevents unauthorized API calls
3. **PII Detection** — Redacts sensitive information

---

## 🎯 Core Concepts

### The Problem
Enterprises want to deploy large language models in customer-facing applications but are blocked by:
- **Hallucinations** — Models confidently stating false information
- **Uncontrolled tool usage** — APIs called without budget/authorization limits
- **Privacy violations** — PII leakage and compliance violations
- **Audit gaps** — No clear explanation of decisions

### The Solution
ControlPlane.ai injects intelligent governance into the LLM pipeline:

```
User Input → LLM → ControlPlane Governance → Decision → User
                    ├─ Lane A: Deterministic checks (fast, reliable)
                    ├─ Lane B: ML-based checks (context-aware)
                    └─ Decision Engine (evidence-based judgment)
```

### The Decision Ladder
ControlPlane doesn't just block—it responds proportionally:

```
✓ ALLOW      → Output is safe, send as-is
→ EDIT       → Modify output to fix issues (redact PII, fix tone)
→ REGENERATE → Ask LLM to re-answer with constraints
→ ESCALATE   → Send to human for review
→ BLOCK      → Never show to user (last resort)
```

---

## 📊 Key Features

**Hallucination Detection**
- Natural Language Inference (NLI) verification
- Cross-references claims against policy documents
- Regenerates factually grounded responses
- Confidence scoring for each check

**Tool Usage Control**
- Validates function calls before execution
- Per-cohort spending limits
- Prevents unauthorized API access
- Immutable audit trail

**Compliance & Privacy**
- PII detection and automatic redaction
- GDPR, HIPAA, PCI-DSS ready
- Hash-chain verified audit trail
- Decision reasoning fully logged

**Configurable Policies**
- YAML-based policy definitions
- Per-workflow configuration
- Dynamic risk routing
- Real-time policy updates

---

## 🏗️ System Architecture

ControlPlane.ai consists of:

- **API Gateway** — OpenAI-compatible interface for easy integration
- **Governance Orchestrator** — Multi-lane decision pipeline
- **Lane A** — Deterministic checks (budget, PII, security)
- **Lane B** — ML-based checks (hallucination, policy compliance)
- **Risk Router** — Decides which checks to run
- **Decision Engine** — Applies policies, makes final decision
- **Audit Trail Database** — SQLite with hash-chain verification
- **Evidence Retrieval** — Policy document corpus for NLI

See [Architecture](ARCHITECTURE.md) for detailed diagrams and flow explanations.

---

## 📝 Configuration

All configuration is via environment variables:

```bash
# LLM Provider
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Governance Mode
CONTROLPLANE_MODE=demo  # demo, live, or replay

# Database
DATABASE_PATH=data/controlplane.db

# Models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base

# Parameters
UNCERTAINTY_SAMPLES=3
TOP_K_EVIDENCE=3
DEFAULT_WORKFLOW=refund-copilot

# Logging
LOG_LEVEL=INFO
```

See [Deployment Guide](DEPLOYMENT_GUIDE.md) for full configuration options.

---

## 🔗 Integration

ControlPlane.ai provides an OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="controlplane-demo"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "..."}],
    extra_body={"workflow": "refund-copilot"}
)
```

The response includes governance metadata:

```json
{
  "choices": [{
    "message": {"content": "..."}
  }],
  "controlplane": {
    "decision": "ALLOW|EDIT|REGENERATE|ESCALATE|BLOCK",
    "risk_state": "...",
    "confidence": 0.95,
    "reason_codes": ["..."],
    "latency_ms": 142,
    "audit_id": "audit_2024_11_29_001"
  },
  "usage": {...},
  "metadata": {...}
}
```

---

## 📚 Documentation Map

```
docs/
├─ README.md (you are here)
├─ GETTING_STARTED.md — 5-minute quickstart
├─ FEATURES.md — Feature overview
├─ ARCHITECTURE.md — System design & internals
├─ API_REFERENCE.md — API documentation
├─ POLICIES.md — How to write policies
├─ EXAMPLES.md — Real-world scenarios
├─ DEPLOYMENT_GUIDE.md — Production setup
├─ TROUBLESHOOTING.md — Common issues
└─ JUDGE_REFERENCE.md — Competition guide
```

---

## 🎓 Learning Path

**For Product Managers:**
1. [Features Overview](FEATURES.md)
2. [Examples](EXAMPLES.md)
3. [Judge Reference](JUDGE_REFERENCE.md)

**For Engineers:**
1. [Getting Started](GETTING_STARTED.md)
2. [Architecture](ARCHITECTURE.md)
3. [API Reference](API_REFERENCE.md)
4. [Deployment Guide](DEPLOYMENT_GUIDE.md)

**For Data Scientists:**
1. [Architecture](ARCHITECTURE.md) (Lane B section)
2. [How Policies Work](POLICIES.md)
3. [Examples](EXAMPLES.md) (NLI scenarios)

**For Compliance Officers:**
1. [Features Overview](FEATURES.md) (Compliance section)
2. [Policies](POLICIES.md) (Policy configuration)
3. [Deployment Guide](DEPLOYMENT_GUIDE.md) (Audit trail section)

---

## 🆘 Getting Help

**Found a bug?**
- Check [Troubleshooting](TROUBLESHOOTING.md) first
- Review [GitHub Issues](https://github.com/yaswantpenapaka/Control_Plane.ai/issues)

**Have a question?**
- See the relevant documentation file above
- Check [Examples](EXAMPLES.md) for similar scenarios
- Review [API Reference](API_REFERENCE.md) for integration questions

**Want to contribute?**
- See repository README for contribution guidelines

---

## 📞 Support & Contact

For questions about the ControlPlane.ai prototype:
- Review the documentation above
- Check working examples in `demo/` folder
- Examine test scenarios in the code

---

## 📄 License

ControlPlane.ai prototype. See LICENSE file in repository root.

---

**Last Updated:** August 29, 2026

"Models generate. ControlPlane governs."

# Getting Started with ControlPlane.ai

Get up and running with ControlPlane.ai in 5 minutes.

## Prerequisites

- Python 3.10 or later
- pip (Python package manager)
- Git (for cloning the repository)
- Optional: GPU for faster NLI inference (CPU-only mode supported)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yaswantpenapaka/Control_Plane.ai.git
cd Control_Plane.ai
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (API gateway)
- Transformers & Torch (NLI models)
- Groq SDK (LLM provider)
- SQLite (audit database)
- Python-dotenv (configuration)
- And 10+ supporting libraries

### 4. Configure Environment

Copy the `.env.example` file (if you don't have `.env` already):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Groq API Key (required for LIVE mode)
GROQ_API_KEY=your_groq_api_key_here

# LLM Model
GROQ_MODEL=openai/gpt-oss-120b

# Mode: demo, live, or replay
CONTROLPLANE_MODE=demo

# Database path
DATABASE_PATH=data/controlplane.db

# Models for governance
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base

# Governance parameters
UNCERTAINTY_SAMPLES=3
TOP_K_EVIDENCE=3
DEFAULT_WORKFLOW=refund-copilot

# Logging
LOG_LEVEL=INFO
```

**For quick testing:** Use `CONTROLPLANE_MODE=demo` (no API key needed).

---

## Running the Demo

### Terminal 1: Start the API Gateway

```bash
uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
```

### Terminal 2: Run Demo Scenarios

In a new terminal (with venv activated):

```bash
python demo_client.py
```

You'll see output for three scenarios:

```
================================================================================
SCENARIO: HERO_1: Hallucination Detection
================================================================================

User Query:
  I bought this 45 days ago. Can I get a full refund? Everyone gets 90-day 
  refunds, right?

AI Response:
  Based on our 30-day policy, you're outside the window. However, I can 
  explore alternative solutions like store credit or a partial refund. 
  Would you like me to check those options?

GOVERNANCE DECISION:
  Decision:      REGENERATE
  Risk State:    HALLUCINATION_DETECTED
  Confidence:    0.92
  Reason Codes:  CLAIM_NOT_SUPPORTED, POLICY_VIOLATION
  Latency:       142ms
  Audit ID:      audit_2024_11_29_001
```

---

## Understanding the Demo Output

Each scenario shows:

### User Query
The input sent to the LLM.

### AI Response
The LLM's initial response (before governance).

### Governance Decision
**Decision Types:**
- `ALLOW` — Output is safe, send as-is
- `EDIT` — Modify output to fix issues
- `REGENERATE` — Re-answer with constraints
- `ESCALATE` — Send to human for review
- `BLOCK` — Don't send to user

**Risk State:**
- `CLEAN` — No issues detected
- `HALLUCINATION_DETECTED` — Claim contradicts policy
- `PII_DETECTED` — Sensitive data found
- `POLICY_VIOLATION` — Breaks business rules
- `WITHIN_POLICY` — Meets all requirements

**Confidence:**
0.0-1.0 score for decision confidence.

**Reason Codes:**
Why the decision was made.

**Latency:**
How long governance took (milliseconds).

**Audit ID:**
Unique identifier for compliance logging.

---

## Three Hero Scenarios

### Scenario 1: Hallucination Detection

**Input:**
```
I bought this 45 days ago. Can I get a full refund? 
Everyone gets 90-day refunds, right?
```

**What Happens:**
1. NLI check: "90-day refund" claim checked against policy
2. Policy says: 30 days max
3. Conclusion: Hallucination detected (confidence: 92%)
4. Action: REGENERATE with accurate information

**Learning:** ControlPlane catches false claims before they reach customers.

---

### Scenario 2: Tool Usage Control

**Input:**
```
Issue the refund for me.
```

**What Happens:**
1. LLM decides to call `issue_refund()` tool with $45
2. Tool validation checks:
   - Amount within policy? ✓ Yes
   - Account eligible? ✓ Yes
   - Monthly limit OK? ✓ Yes
3. Action: ALLOW (safe to execute)

**Learning:** ControlPlane validates tool usage before APIs are called.

---

### Scenario 3: PII Detection

**Input:**
```
My email is john.doe@example.com and my phone is 9876543210. 
Can you confirm my account?
```

**What Happens:**
1. LLM responds with helpful information about the account
2. But would include the customer's email/phone in response
3. PII detection triggers: Email detected (confidence: 99%)
4. Action: EDIT — Remove PII, keep helpful response

**Learning:** ControlPlane redacts sensitive information automatically.

---

## Next Steps

### To Understand the System
- Read [Architecture Guide](ARCHITECTURE.md) to see how components work
- Review [How Policies Work](POLICIES.md) to customize governance

### To Integrate with Your App
- See [API Reference](API_REFERENCE.md) for integration examples
- Check [Examples](EXAMPLES.md) for more scenarios

### To Deploy to Production
- Follow [Deployment Guide](DEPLOYMENT_GUIDE.md)
- Configure policies for your workflows
- Set up monitoring and audit logging

### To Troubleshoot
- See [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues

---

## Common Commands

```bash
# Start gateway (from main directory)
uvicorn gateway.app:app --host 127.0.0.1 --port 8000

# Run demo scenarios
python demo_client.py

# Start Streamlit UI (optional, for interactive testing)
streamlit run app.py

# Check audit trail
sqlite3 data/controlplane.db "SELECT * FROM audit_trail LIMIT 10;"

# View logs
tail -f logs/controlplane.log
```

---

## Mode: Demo vs. Live vs. Replay

### DEMO Mode (Default)
- No API key required
- Pre-recorded LLM responses
- Fast, no external dependencies
- Perfect for testing and demos

```bash
CONTROLPLANE_MODE=demo
```

### LIVE Mode
- Real Groq API calls
- Real-time LLM responses
- Requires valid `GROQ_API_KEY`
- Costs tokens from your API quota

```bash
CONTROLPLANE_MODE=live
GROQ_API_KEY=your_key_here
```

### REPLAY Mode
- Stored audit trail responses
- Replays previous decisions
- No API calls
- For auditing and compliance

```bash
CONTROLPLANE_MODE=replay
```

---

## File Structure

```
control_plane.ai/
├─ gateway/              # FastAPI application
├─ controlplane/         # Governance orchestrator
├─ decision/             # Decision engine
├─ checks/               # Verification checks (NLI, PII, etc.)
├─ retrieval/            # Evidence retrieval system
├─ policy/               # Policy YAML files & engine
├─ corpus/               # Policy documents for NLI
├─ demo/                 # Demo scenarios
├─ evaluation/           # Metrics collection
├─ storage/              # Database layer
├─ llm/                  # Groq client wrapper
├─ config/               # Configuration management
├─ audit/                # Audit trail & logging
├─ tools/                # Utility functions
├─ docs/                 # Documentation (this folder)
├─ demo_client.py        # Demo script
├─ app.py                # Streamlit UI
├─ requirements.txt      # Python dependencies
└─ .env                  # Configuration (not pushed to git)
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'groq'"

**Solution:**
```bash
pip install groq
```

### "Connection refused on port 8000"

**Check:**
- Is the gateway running? (Terminal 1 should show "Uvicorn running")
- Is port 8000 already in use? Try `--port 9000`

### "API key error"

**For DEMO mode:** Not needed, should work without `.env`

**For LIVE mode:**
- Get API key from Groq console
- Add to `.env`: `GROQ_API_KEY=your_key`
- Restart gateway

### "Torch not installed"

**Solution:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more issues.

---

## What's Next?

After running the demo successfully:

1. **Explore the code** — Look at `gateway/app.py` to see the API
2. **Understand policies** — Read `policy/refund-copilot.yaml`
3. **Integrate** — Use [API Reference](API_REFERENCE.md) to add to your app
4. **Customize** — Edit policies for your use cases
5. **Deploy** — Follow [Deployment Guide](DEPLOYMENT_GUIDE.md)

---

## Support

For issues:
1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review code comments in relevant modules
3. Check GitHub issues at [repository](https://github.com/yaswantpenapaka/Control_Plane.ai/issues)

**Tip:** Run with `LOG_LEVEL=DEBUG` for detailed logs:
```bash
LOG_LEVEL=DEBUG uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

---

**Ready to run?**

```bash
# Terminal 1
uvicorn gateway.app:app --host 127.0.0.1 --port 8000

# Terminal 2
python demo_client.py
```

Enjoy exploring ControlPlane.ai! 🚀

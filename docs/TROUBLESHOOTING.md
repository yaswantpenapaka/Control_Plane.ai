# Troubleshooting Guide

Common issues and solutions for ControlPlane.ai.

## Installation Issues

### ModuleNotFoundError: No module named 'torch'

**Error:**
```
ModuleNotFoundError: No module named 'torch'
```

**Cause:** PyTorch not installed, needed for NLI model.

**Solution:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Or with GPU:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

### ModuleNotFoundError: No module named 'transformers'

**Error:**
```
ModuleNotFoundError: No module named 'transformers'
```

**Cause:** Hugging Face transformers library not installed.

**Solution:**
```bash
pip install transformers>=4.30.0
```

---

### ModuleNotFoundError: No module named 'groq'

**Error:**
```
ModuleNotFoundError: No module named 'groq'
```

**Cause:** Groq SDK not installed.

**Solution:**
```bash
pip install groq
```

---

### RuntimeError: CUDA out of memory

**Error:**
```
RuntimeError: CUDA out of memory
```

**Cause:** GPU memory exhausted (NLI model too large for GPU).

**Solution:**
```bash
# Use CPU-only mode
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Or set environment variable
export CUDA_VISIBLE_DEVICES=""
```

---

## Startup Issues

### "Connection refused on port 8000"

**Error:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:** Gateway not running on port 8000.

**Solution:**
1. Check if gateway is running:
   ```bash
   lsof -i :8000  # On Mac/Linux
   netstat -ano | findstr :8000  # On Windows
   ```

2. Start the gateway:
   ```bash
   uvicorn gateway.app:app --host 127.0.0.1 --port 8000
   ```

3. If port is in use, kill the process or use different port:
   ```bash
   uvicorn gateway.app:app --host 127.0.0.1 --port 9000
   ```

---

### "Address already in use"

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Cause:** Another process using port 8000.

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process (Mac/Linux)
kill -9 <PID>

# Or use different port
uvicorn gateway.app:app --port 8001
```

---

### "API key not found" or "Authentication error"

**Error:**
```
AuthenticationError: Invalid API key
```

**Cause:** Missing or invalid Groq API key (in LIVE mode).

**Solution:**
1. Check `.env` file:
   ```bash
   cat .env | grep GROQ_API_KEY
   ```

2. Get API key from [Groq Console](https://console.groq.com)

3. Update `.env`:
   ```bash
   GROQ_API_KEY=your_actual_key_here
   ```

4. For DEMO mode, no key needed:
   ```bash
   CONTROLPLANE_MODE=demo
   ```

---

## Runtime Issues

### High latency (>500ms)

**Symptom:** Governance checks taking longer than expected.

**Causes & Solutions:**

1. **NLI model inference too slow**
   ```bash
   # Use quantized model (faster)
   NLI_MODEL=cross-encoder/nli-deberta-v3-base-q-int8
   
   # Or reduce samples
   UNCERTAINTY_SAMPLES=1
   ```

2. **Groq API slow**
   ```bash
   # Check API status
   curl https://console.groq.com/status
   
   # Use cached responses (if available)
   ENABLE_CACHE=true
   ```

3. **Database slow**
   ```bash
   # Optimize database
   sqlite3 data/controlplane.db "VACUUM; ANALYZE;"
   ```

4. **High CPU load**
   ```bash
   # Reduce parallel tasks
   MAX_WORKERS=2
   ```

---

### Out of memory errors

**Error:**
```
MemoryError: Unable to allocate memory
```

**Cause:** Models loaded multiple times or large batches.

**Solution:**
```bash
# Increase memory (Docker)
docker run -m 8g controlplane:latest

# Or reduce batch size
MAX_BATCH_SIZE=1

# Or use CPU only
USE_GPU=false
```

---

### "Models not found" or "Cache miss"

**Error:**
```
FileNotFoundError: Model cache directory not found
```

**Cause:** Models not downloaded.

**Solution:**
```bash
# Download models manually
python -c "from transformers import AutoModel; AutoModel.from_pretrained('cross-encoder/nli-deberta-v3-base')"

# Or set cache directory
export HF_HOME=/path/to/cache

# Run again
python demo_client.py
```

---

## API Issues

### "Invalid request format"

**Error:**
```json
{
  "error": {
    "message": "Invalid request format",
    "type": "invalid_request_error"
  }
}
```

**Cause:** Request body malformed.

**Solution:**
Check request format matches [API Reference](API_REFERENCE.md):

```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {"role": "user", "content": "..."}
  ],
  "extra_body": {
    "workflow": "refund-copilot"
  }
}
```

---

### "Rate limit exceeded"

**Error:**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Cause:** Too many requests in short time.

**Solution:**
```python
import time
import random
from openai import RateLimitError

for attempt in range(3):
    try:
        response = client.chat.completions.create(...)
        break
    except RateLimitError:
        wait_time = (2 ** attempt) + random.random()
        print(f"Rate limited. Waiting {wait_time:.1f}s...")
        time.sleep(wait_time)
```

---

### "Timeout error"

**Error:**
```
TimeoutError: Request timed out after 30 seconds
```

**Cause:** Governance checks or LLM call taking too long.

**Solution:**
```python
# Increase timeout
response = client.chat.completions.create(
    ...,
    timeout=60  # 60 seconds
)

# Or reduce checks
# Set more aggressive timeouts on individual checks:
HALLUCINATION_CHECK_TIMEOUT=10s
POLICY_CHECK_TIMEOUT=10s
```

---

### "Empty response" or "No choices returned"

**Error:**
```
IndexError: list index out of range (accessing choices[0])
```

**Cause:** LLM or governance system returned empty response.

**Solution:**
1. Check LLM is working:
   ```bash
   curl -X POST http://127.0.0.1:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}]}'
   ```

2. Check Groq API has tokens:
   - Go to [Groq Console](https://console.groq.com)
   - Check quota

3. Use DEMO mode:
   ```bash
   CONTROLPLANE_MODE=demo
   ```

---

## Governance Issues

### Decision always "BLOCK" or "ESCALATE"

**Symptom:** All requests being blocked or escalated.

**Cause:** Policy too strict or misconfigured.

**Solution:**
1. Check policy configuration:
   ```bash
   cat policy/workflows/refund-copilot.yaml
   ```

2. Lower confidence thresholds:
   ```yaml
   checks:
     hallucination_detection:
       confidence_threshold: 0.70  # Was 0.85
   ```

3. Disable unnecessary checks:
   ```yaml
   checks:
     hallucination_detection:
       enabled: true  # Keep important ones
     policy_compliance:
       enabled: false  # Disable non-critical
   ```

4. Test with simple input:
   ```python
   response = client.chat.completions.create(
       model="openai/gpt-oss-120b",
       messages=[{"role": "user", "content": "What time is it?"}]
   )
   ```

---

### No hallucinations detected

**Symptom:** Responses with false claims are marked as "ALLOW".

**Cause:** NLI confidence too low or policy corpus incomplete.

**Solution:**
1. Check policy corpus:
   ```bash
   ls -la corpus/
   # Should have policy documents
   ```

2. Check confidence thresholds:
   ```bash
   # Lower the threshold (more sensitive)
   UNCERTAINTY_SAMPLES=5  # Was 3
   TOP_K_EVIDENCE=5       # Was 3
   ```

3. Test hallucination detection:
   ```python
   # With known hallucination
   response = client.chat.completions.create(
       model="openai/gpt-oss-120b",
       messages=[{
           "role": "user",
           "content": "Does your company offer 200-year warranties?"
       }]
   )
   # Should detect as hallucination
   ```

---

### PII not being detected

**Symptom:** Emails, phone numbers not being redacted.

**Cause:** PII detection disabled or patterns not matching.

**Solution:**
1. Check PII detection is enabled:
   ```yaml
   checks:
     pii_detection:
       enabled: true
   ```

2. Check patterns:
   ```python
   # Test detection directly
   from checks.pii import PIIDetector
   detector = PIIDetector()
   result = detector.detect("My email is test@example.com")
   print(result.detected)  # Should be True
   ```

3. Enable debug logging:
   ```bash
   LOG_LEVEL=DEBUG python -m gateway.app
   ```

---

## Database Issues

### "database is locked"

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing database simultaneously.

**Solution:**
1. Close other connections:
   ```bash
   # Find processes accessing database
   lsof | grep controlplane.db
   kill -9 <PID>
   ```

2. Use PostgreSQL (production):
   ```bash
   # Switch to PostgreSQL
   DATABASE_URL=postgresql://user:pass@localhost/controlplane
   ```

3. Increase timeout:
   ```python
   import sqlite3
   conn = sqlite3.connect('data/controlplane.db', timeout=30)
   ```

---

### "database disk image is malformed"

**Error:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Cause:** Database corruption.

**Solution:**
1. Restore from backup:
   ```bash
   # If backup exists
   cp backups/controlplane.db.bak data/controlplane.db
   ```

2. Or check/repair:
   ```bash
   sqlite3 data/controlplane.db "PRAGMA integrity_check;"
   
   # If errors, try recovery
   sqlite3 data/controlplane.db ".recover" | sqlite3 recovered.db
   mv recovered.db data/controlplane.db
   ```

---

### Audit trail not being logged

**Symptom:** No entries in audit_trail table.

**Cause:** Audit logging disabled or database permission issue.

**Solution:**
1. Check audit table exists:
   ```bash
   sqlite3 data/controlplane.db ".schema audit_trail"
   ```

2. Check database permissions:
   ```bash
   ls -la data/controlplane.db
   # Should be writable by running user
   chmod 644 data/controlplane.db
   ```

3. Check audit logging is enabled:
   ```yaml
   # In configuration
   ENABLE_AUDIT_LOGGING=true
   ```

---

## Performance Issues

### Slow startup (models loading)

**Symptom:** Takes 30+ seconds to start.

**Cause:** Models being loaded for first time.

**Solution:**
- First startup is slow (normal)
- Subsequent restarts are fast (models cached)
- Pre-load models on deployment:
  ```bash
  python -c "from checks.hallucination import HallucinationDetector; HallucinationDetector()"
  ```

---

### High memory usage

**Symptom:** Process consuming 4GB+ RAM.

**Cause:** Models loaded + cached responses.

**Solution:**
```bash
# Reduce cache size
CACHE_MAX_SIZE=100  # Was 1000

# Or clear cache periodically
CACHE_TTL_SECONDS=600  # Clear every 10 min

# Or use memory-efficient models
NLI_MODEL=cross-encoder/nli-deberta-v3-small
```

---

### Many "INFO" logs

**Symptom:** Log file growing too large.

**Cause:** Too verbose logging.

**Solution:**
```bash
# Reduce log level
LOG_LEVEL=WARNING  # Was INFO

# Or rotate logs
# In logging config:
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    maxBytes: 10485760  # 10MB
    backupCount: 5
```

---

## Docker Issues

### "Docker image not found"

**Error:**
```
docker: Error response from daemon: image not found
```

**Solution:**
```bash
# Build image first
docker build -t controlplane:latest .

# Or pull from registry
docker pull myregistry.azurecr.io/controlplane:latest
```

---

### Container exits immediately

**Error:**
```
docker: The container exited immediately with code 1
```

**Cause:** Startup error.

**Solution:**
```bash
# Check logs
docker logs <container_id>

# Run with verbose output
docker run -it controlplane:latest uvicorn gateway.app:app --log-level debug
```

---

## Kubernetes Issues

### Pods not starting

**Symptom:** Pods stuck in "Pending" or "CrashLoopBackOff".

**Solution:**
```bash
# Check pod status
kubectl describe pod <pod_name> -n governance

# Check logs
kubectl logs <pod_name> -n governance

# Check resource availability
kubectl top nodes
```

---

### Service unreachable

**Symptom:** Cannot reach service endpoint.

**Solution:**
```bash
# Check service exists
kubectl get svc -n governance

# Check endpoint
kubectl get endpoints -n governance

# Test connectivity
kubectl exec -it <pod> -- curl http://localhost:8000/health
```

---

## Monitoring & Debugging

### Enable Debug Logging

```bash
# Set environment variable
LOG_LEVEL=DEBUG

# Start gateway with debug
uvicorn gateway.app:app --log-level debug
```

### Check Health

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics
```

### Inspect Audit Trail

```bash
# Recent decisions
sqlite3 data/controlplane.db \
  "SELECT audit_id, decision, latency_ms FROM audit_trail ORDER BY timestamp DESC LIMIT 5;"

# Decisions by workflow
sqlite3 data/controlplane.db \
  "SELECT workflow, COUNT(*) as count, decision FROM audit_trail GROUP BY workflow, decision;"

# Average latency
sqlite3 data/controlplane.db \
  "SELECT workflow, AVG(latency_ms) FROM audit_trail GROUP BY workflow;"
```

---

## Getting Help

1. **Check this guide** — Most issues are documented here
2. **Review logs** — `LOG_LEVEL=DEBUG` shows detailed flow
3. **Check configuration** — Review `.env` and policy YAML
4. **Test in isolation** — Use DEMO mode to isolate issues
5. **Check GitHub issues** — Others may have solved it
6. **Open issue** — Include logs and `.env` (sanitized)

---

## Quick Test Commands

```bash
# Test gateway running
curl http://localhost:8000/health

# Test demo mode
CONTROLPLANE_MODE=demo python demo_client.py

# Test API key (LIVE mode)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer controlplane-demo" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}]}'

# Test models loaded
python -c "from checks.hallucination import HallucinationDetector; print('Models OK')"

# Test database
sqlite3 data/controlplane.db "SELECT COUNT(*) FROM audit_trail;"
```

---

**For more information:**
- [Getting Started](GETTING_STARTED.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Architecture](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)

"Models generate. ControlPlane governs."

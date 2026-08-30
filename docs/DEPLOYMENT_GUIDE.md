# Deployment Guide

Production deployment and operations guide for ControlPlane.ai.

## Quick Start (5 minutes)

### Development Setup

```bash
# 1. Clone and setup
git clone https://github.com/yaswantpenapaka/Control_Plane.ai.git
cd Control_Plane.ai
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your settings

# 4. Run
uvicorn gateway.app:app --host 127.0.0.1 --port 8000
```

---

## Configuration

### Environment Variables

**Required:**

```bash
# Mode of operation
CONTROLPLANE_MODE=demo  # demo, live, or replay

# Database
DATABASE_PATH=data/controlplane.db

# Models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NLI_MODEL=cross-encoder/nli-deberta-v3-base
```

**For LIVE mode:**

```bash
# Groq API key (get from https://console.groq.com)
GROQ_API_KEY=your_api_key_here

# LLM model
GROQ_MODEL=openai/gpt-oss-120b
```

**Optional:**

```bash
# Governance tuning
UNCERTAINTY_SAMPLES=3      # NLI verification samples
TOP_K_EVIDENCE=3           # Evidence documents to retrieve
DEFAULT_WORKFLOW=refund-copilot

# Logging
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/controlplane.log

# Performance
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
```

### Policy Configuration

Policies are defined in YAML:

```yaml
# policy/workflows/refund-copilot.yaml
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
      max_per_month: 10000
      requires_escalation_above: 1000
  escalation:
    enabled: true
    handlers: ["supervisor@company.com"]
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment
ENV CONTROLPLANE_MODE=live
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t controlplane:latest .

# Run container
docker run -d \
  --name controlplane \
  -p 8000:8000 \
  -e CONTROLPLANE_MODE=live \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/policy:/app/policy \
  controlplane:latest

# View logs
docker logs -f controlplane

# Stop container
docker stop controlplane
```

### Docker Compose

```yaml
version: '3.8'

services:
  controlplane:
    build: .
    ports:
      - "8000:8000"
    environment:
      CONTROLPLANE_MODE: live
      GROQ_API_KEY: ${GROQ_API_KEY}
      DATABASE_PATH: /data/controlplane.db
      LOG_LEVEL: INFO
    volumes:
      - ./data:/app/data
      - ./policy:/app/policy
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: PostgreSQL for audit trail (production)
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: controlplane
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: controlplane
  namespace: governance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: controlplane
  template:
    metadata:
      labels:
        app: controlplane
    spec:
      containers:
      - name: controlplane
        image: controlplane:latest
        ports:
        - containerPort: 8000
        env:
        - name: CONTROLPLANE_MODE
          value: "live"
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: groq-api-key
              key: api_key
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: policies
          mountPath: /app/policy
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: controlplane-data
      - name: policies
        configMap:
          name: controlplane-policies
---
apiVersion: v1
kind: Service
metadata:
  name: controlplane-service
  namespace: governance
spec:
  type: LoadBalancer
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: controlplane
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace governance

# Create secrets
kubectl create secret generic groq-api-key \
  --from-literal=api_key=$GROQ_API_KEY \
  -n governance

# Create PVC for data
kubectl apply -f pvc.yaml -n governance

# Create ConfigMap for policies
kubectl create configmap controlplane-policies \
  --from-file=policy/ \
  -n governance

# Deploy
kubectl apply -f deployment.yaml -n governance

# Check status
kubectl get deployments -n governance
kubectl get pods -n governance
kubectl logs -f deployment/controlplane -n governance
```

---

## Monitoring & Observability

### Prometheus Metrics

Configure Prometheus to scrape metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'controlplane'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Key Metrics to Monitor

```
# Decision distribution
controlplane_decisions_total{decision="ALLOW"}
controlplane_decisions_total{decision="BLOCK"}
controlplane_decisions_total{decision="ESCALATE"}

# Latency
controlplane_decision_latency_ms (histogram)

# Hallucination rate
controlplane_hallucinations_detected_total
controlplane_hallucination_rate (percentage)

# Error rate
controlplane_errors_total{error_type="..."}

# Cost
controlplane_tokens_used_total
controlplane_estimated_cost_usd_total
```

### Sample Alerts

```yaml
groups:
  - name: controlplane
    rules:
      - alert: HighErrorRate
        expr: rate(controlplane_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "ControlPlane error rate > 5%"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, controlplane_decision_latency_ms) > 500
        for: 5m
        annotations:
          summary: "P95 latency > 500ms"
      
      - alert: UnusualBlockRate
        expr: rate(controlplane_decisions_total{decision="BLOCK"}[1h]) > 0.1
        for: 10m
        annotations:
          summary: "Block rate > 10% (unusual)"
```

### Logging

**ELK Stack Setup:**

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/controlplane.log
  json.message_key: message
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

**Sample Log Entry:**

```json
{
  "timestamp": "2024-11-29T14:32:15.142Z",
  "level": "INFO",
  "workflow": "refund-copilot",
  "decision": "REGENERATE",
  "audit_id": "audit_2024_11_29_001",
  "latency_ms": 142,
  "reason_codes": ["HALLUCINATION_DETECTED"],
  "confidence": 0.92
}
```

---

## Database Management

### SQLite (Development)

```bash
# Initialize database
sqlite3 data/controlplane.db < schema.sql

# Backup
sqlite3 data/controlplane.db ".dump" > backup.sql

# Check integrity
sqlite3 data/controlplane.db "PRAGMA integrity_check;"

# Query audit trail
sqlite3 data/controlplane.db \
  "SELECT audit_id, decision, workflow, timestamp FROM audit_trail LIMIT 10;"
```

### PostgreSQL (Production)

```bash
# Connect
psql -h postgres.example.com -U controlplane -d controlplane_db

# Backup
pg_dump controlplane_db > backup.sql

# Restore
psql controlplane_db < backup.sql

# Check audit trail
SELECT audit_id, decision, workflow, timestamp 
FROM audit_trail 
WHERE workflow='refund-copilot' 
ORDER BY timestamp DESC 
LIMIT 10;
```

---

## Performance Tuning

### Caching

Enable response caching for frequently accessed policies:

```bash
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

### Model Optimization

**Use quantized models for faster inference:**

```bash
# Instead of full-precision NLI
NLI_MODEL=cross-encoder/nli-deberta-v3-base

# Use quantized version (faster, smaller)
NLI_MODEL=cross-encoder/nli-deberta-v3-base-q-int8
```

### Parallel Processing

Lane A and Lane B checks run in parallel:

```python
# gateway/app.py
async def governance_pipeline(request):
    # Parallel execution
    lane_a_results = await asyncio.gather(
        pii_check(response),
        budget_check(response),
        security_check(response)
    )
    
    lane_b_results = await asyncio.gather(
        hallucination_check(response),
        policy_check(response)
    )
    
    # Combine results
    return merge_results(lane_a_results, lane_b_results)
```

---

## Scaling

### Horizontal Scaling

ControlPlane.ai is stateless and horizontally scalable:

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┼────┐
    │    │    │
┌───▼──┐ │ ┌──▼──┐
│ Pod1 │ │ │ Pod2 │
└──────┘ │ └──────┘
    ┌────▼──┐
    │ Pod3  │
    └───────┘
    
Shared Resources:
├─ Database (PostgreSQL)
├─ Model Cache
└─ Policy ConfigMap
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 \
  -H "Authorization: Bearer controlplane-demo" \
  http://localhost:8000/v1/chat/completions

# Using wrk
wrk -t12 -c400 -d30s \
  -s script.lua \
  http://localhost:8000/v1/chat/completions

# Expected: 100+ req/sec per instance
```

---

## Security

### API Key Management

```bash
# Generate strong API key
openssl rand -hex 32

# Store in secrets manager (not .env!)
# AWS Secrets Manager, HashiCorp Vault, etc.

# Access in code (example with AWS)
import boto3
sm = boto3.client('secretsmanager')
api_key = sm.get_secret_value(SecretId='controlplane-api-key')
```

### Network Security

```yaml
# Network Policy (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: controlplane-network-policy
spec:
  podSelector:
    matchLabels:
      app: controlplane
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: apps
      ports:
      - protocol: TCP
        port: 8000
  egress:
    - to:
      - namespaceSelector: {}
      ports:
      - protocol: TCP
        port: 443  # HTTPS for external APIs
```

### Audit Trail Security

- Hash-chain verification prevents tampering
- Immutable database (append-only logs)
- Regular integrity checks

```bash
# Verify audit trail integrity
python -m audit.verify_chain --database=data/controlplane.db
```

---

## Backup & Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR=/backups/controlplane
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
sqlite3 data/controlplane.db ".dump" > $BACKUP_DIR/db_$TIMESTAMP.sql

# Backup policies
tar -czf $BACKUP_DIR/policies_$TIMESTAMP.tar.gz policy/

# Upload to S3
aws s3 cp $BACKUP_DIR/ s3://my-backups/controlplane/ --recursive

# Clean old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

### Recovery Procedure

```bash
# Restore database
sqlite3 data/controlplane.db < backup.sql

# Restore policies
tar -xzf policies_backup.tar.gz

# Verify integrity
sqlite3 data/controlplane.db "PRAGMA integrity_check;"

# Restart service
systemctl restart controlplane
```

---

## Upgrades

### Zero-Downtime Deployment

```bash
# Using Kubernetes rolling update
kubectl set image deployment/controlplane \
  controlplane=controlplane:v1.1.0 \
  -n governance

# Monitor rollout
kubectl rollout status deployment/controlplane -n governance

# Rollback if needed
kubectl rollout undo deployment/controlplane -n governance
```

### Database Migrations

```bash
# Run migrations
python -m alembic upgrade head

# Verify compatibility
python -m tests.migration_test

# Gradual rollout (canary deployment)
# 1. Deploy to 10% of pods
# 2. Monitor metrics
# 3. Expand to 50%
# 4. Expand to 100%
```

---

## Troubleshooting

### Check Service Health

```bash
# Health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### View Metrics

```bash
curl http://localhost:8000/metrics

# Check key metrics:
# - requests_total
# - decision_distribution
# - avg_latency_ms
# - error_rate
```

### Debug Logs

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m gateway.app

# Check specific workflow
sqlite3 data/controlplane.db \
  "SELECT * FROM audit_trail WHERE workflow='refund-copilot' \
   ORDER BY timestamp DESC LIMIT 10;"
```

---

## Maintenance

### Regular Tasks

- **Daily:** Monitor error rate, check backups
- **Weekly:** Review unusual decision patterns, check disk usage
- **Monthly:** Database optimization, policy review
- **Quarterly:** Security audit, capacity planning

### Scheduled Maintenance

```bash
# Optimize database (weekly)
sqlite3 data/controlplane.db "VACUUM; ANALYZE;"

# Clear old logs (monthly)
find logs/ -type f -mtime +90 -delete

# Check model freshness (quarterly)
python -m checks.verify_models
```

---

**For help:**
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Reference](API_REFERENCE.md)
- [Architecture](ARCHITECTURE.md)

"Models generate. ControlPlane governs."

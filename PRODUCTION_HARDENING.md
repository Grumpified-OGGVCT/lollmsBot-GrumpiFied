# Production Hardening Guide

This document provides comprehensive guidance for deploying lollmsBot in production environments with security, reliability, and scalability best practices.

## 🔒 Security Hardening

### 1. Input Validation

**Status:** ✅ Implemented

All user inputs are now validated before processing:

```python
# User ID validation
- Must be non-empty string
- Maximum 256 characters
- Only alphanumeric, underscore, hyphen, @, . characters allowed

# Message validation
- Must be non-empty string
- Cannot be whitespace only
- Maximum 50,000 characters (configurable)
```

**Configuration:**
```python
# In agent.py, adjust max message length:
validate_message(message, max_length=50000)  # Change as needed
```

### 2. CORS Configuration

**Status:** ✅ Configurable via environment

CORS origins are now fully configurable and secure by default:

```bash
# .env configuration
LOLLMSBOT_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Leave empty for default localhost-only mode
# Set to empty string explicitly to allow all origins (NOT RECOMMENDED)
```

**Default behavior:**
- **Localhost mode** (LOLLMSBOT_HOST=127.0.0.1): Only allows http://localhost, http://127.0.0.1
- **External mode** (LOLLMSBOT_HOST=0.0.0.0): No origins by default (must explicitly configure)

### 3. API Key Security

**Best Practices:**

```bash
# Generate strong API key (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment
LOLLMSBOT_API_KEY=your_generated_key_here

# All external requests must include:
# Authorization: Bearer your_generated_key_here
```

**Key rotation:**
1. Generate new key
2. Update LOLLMSBOT_API_KEY in environment
3. Restart service
4. Update all clients with new key

### 4. URL Validation

**Status:** ✅ Implemented

All URLs (LoLLMS host addresses) are validated:
- Must have valid scheme (http, https, ws, wss)
- Must have valid netloc (domain/IP)
- Invalid URLs raise ValueError on startup

### 5. Thread-Safe Singletons

**Status:** ✅ Implemented

Global singleton instances now use double-checked locking pattern:
- Prevents race conditions during initialization
- Thread-safe for concurrent access
- No performance penalty after initialization

## 🛡️ Error Handling

### 1. Specific Exception Catching

**Status:** ✅ Fixed

Replaced all bare `except:` clauses with specific exception types:

```python
# Before (DANGEROUS):
except:
    pass  # Catches KeyboardInterrupt, SystemExit, etc.

# After (SAFE):
except (json.JSONDecodeError, ValueError) as e:
    logger.debug(f"Error details: {e}")
    pass
```

**Files updated:**
- `skills.py`: JSON parsing errors
- `config.py`: Config loading errors
- `ui/app.py`: WebSocket errors
- `wizard.py`: User input parsing
- `browser_agent.py`: Page parsing errors

### 2. Error Propagation

**Best Practice:** Always log errors before handling:

```python
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Handle or re-raise
    raise
```

## 📊 Observability

### 1. Structured Logging

**Recommendation:** Add structured logging with request IDs

```python
import logging
import contextvars

request_id_var = contextvars.ContextVar('request_id', default='')

# In each request handler:
request_id = str(uuid.uuid4())
request_id_var.set(request_id)

# All log messages will include request ID
logger.info(f"[{request_id_var.get()}] Processing message")
```

### 2. Health Checks

**Implementation:**

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    agent = get_agent()
    lollms_ok = get_lollms_client() is not None
    
    return {
        "status": "ok" if lollms_ok else "degraded",
        "agent_state": agent._state.name,
        "quarantine": agent._guardian.is_quarantined if agent._guardian else False,
        "channels": list(_active_channels.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 3. Metrics Collection

**Recommendation:** Integrate Prometheus metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
message_counter = Counter('lollmsbot_messages_total', 'Total messages processed')
response_time = Histogram('lollmsbot_response_seconds', 'Response time')
active_users = Gauge('lollmsbot_active_users', 'Number of active users')

# Use in handlers
@message_counter.count_exceptions()
async def handle_message(...):
    with response_time.time():
        # Process message
        pass
```

## ⚙️ Configuration Management

### 1. Environment Variables

**All configurable settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `LOLLMS_HOST_ADDRESS` | http://localhost:9600 | LoLLMS server URL |
| `LOLLMS_API_KEY` | - | LoLLMS API key |
| `LOLLMS_BINDING_NAME` | lollms | LLM binding name |
| `LOLLMS_MODEL_NAME` | - | Model name override |
| `LOLLMS_CONTEXT_SIZE` | 4096 | Context window size |
| `LOLLMSBOT_HOST` | 127.0.0.1 | Gateway bind address |
| `LOLLMSBOT_PORT` | 8800 | Gateway port |
| `LOLLMSBOT_API_KEY` | auto-generated | API key for external access |
| `LOLLMSBOT_CORS_ORIGINS` | localhost | Comma-separated allowed origins |
| `LOLLMSBOT_ENABLE_SHELL` | false | Enable shell tool (dangerous) |
| `LOLLMSBOT_DEFAULT_PERMISSION` | BASIC | Default user permission level |

### 2. Configuration Validation

**Startup checks:**

```bash
# Run validation before starting
lollmsbot validate-config

# Check specific settings
lollmsbot config get LOLLMS_HOST_ADDRESS
```

## 🚀 Scalability

### 1. Connection Pooling

**HTTP Client configuration:**

```python
# In tools/http.py
limits = httpx.Limits(
    max_keepalive_connections=20,  # Increase for high load
    max_connections=50,            # Increase for concurrent requests
    keepalive_expiry=30.0
)
```

### 2. Rate Limiting

**Recommendation:** Add per-user rate limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def chat_endpoint(...):
    pass
```

### 3. Memory Management

**Lane Queue tuning:**

```python
# In core/engine.py
# Adjust queue sizes for your workload
self._queues = {
    Lane.USER_INTERACTION: asyncio.Queue(maxsize=100),
    Lane.BACKGROUND: asyncio.Queue(maxsize=50),
    Lane.SYSTEM: asyncio.Queue(maxsize=200)
}
```

### 4. Database Connection Pooling

**SQLite optimization:**

```python
# In storage/sqlite_store.py
engine = create_async_engine(
    f"sqlite+aiosqlite:///{db_path}",
    pool_size=10,           # Increase for concurrent access
    max_overflow=20,        # Allow overflow connections
    pool_pre_ping=True,     # Check connections before use
    pool_recycle=3600       # Recycle connections hourly
)
```

## 🔧 Deployment Best Practices

### 1. Docker Deployment

**Production Dockerfile:**

```dockerfile
FROM python:3.11-slim

# Non-root user
RUN useradd -m -u 1000 lollmsbot
USER lollmsbot

# Install dependencies
COPY --chown=lollmsbot:lollmsbot requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=lollmsbot:lollmsbot . /app/
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8800/health')"

CMD ["python", "-m", "lollmsbot.gateway"]
```

### 2. Environment Separation

```bash
# Development
export LOLLMSBOT_ENV=development
export LOLLMSBOT_DEBUG=true

# Staging
export LOLLMSBOT_ENV=staging
export LOLLMSBOT_DEBUG=false

# Production
export LOLLMSBOT_ENV=production
export LOLLMSBOT_DEBUG=false
export LOLLMSBOT_LOG_LEVEL=INFO
```

### 3. Secrets Management

**Use secret management tools:**

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id lollmsbot/api-key

# HashiCorp Vault
vault kv get secret/lollmsbot/api-key

# Kubernetes Secrets
kubectl create secret generic lollmsbot-secrets \
  --from-literal=api-key=$LOLLMSBOT_API_KEY \
  --from-literal=lollms-key=$LOLLMS_API_KEY
```

### 4. Monitoring and Alerting

**Prometheus + Grafana stack:**

```yaml
# docker-compose.yml
services:
  lollmsbot:
    # ... your config
  
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
```

## 🧪 Testing

### 1. Integration Tests

**Create test suite:**

```python
# tests/test_integration.py
import pytest
from lollmsbot.agent import Agent, ValidationError

@pytest.mark.asyncio
async def test_input_validation():
    agent = Agent(config=BotConfig.from_env())
    
    # Test invalid user_id
    result = await agent.chat(user_id="", message="test")
    assert not result["success"]
    assert "validation_error" in result["error"]
    
    # Test message length limit
    long_message = "x" * 100000
    result = await agent.chat(user_id="test", message=long_message)
    assert not result["success"]
```

### 2. Load Testing

**Using locust:**

```python
# locustfile.py
from locust import HttpUser, task, between

class LollmsBotUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def chat(self):
        self.client.post("/chat", json={
            "user_id": "test_user",
            "message": "Hello, bot!"
        })
```

## 📋 Security Checklist

- [x] Input validation implemented
- [x] CORS properly configured
- [x] API keys validated
- [x] URLs validated
- [x] Thread-safe singletons
- [x] Specific exception handling
- [ ] Rate limiting (recommended)
- [ ] Structured logging with request IDs (recommended)
- [ ] Metrics collection (recommended)
- [ ] Integration tests (recommended)
- [ ] Load testing (recommended)

## 🔄 Maintenance

### Regular Tasks

1. **Weekly:**
   - Review audit logs for security events
   - Check disk space and memory usage
   - Review error logs

2. **Monthly:**
   - Update dependencies (security patches)
   - Rotate API keys
   - Review and clean old data

3. **Quarterly:**
   - Full security audit
   - Load testing
   - Dependency vulnerability scan

### Monitoring Alerts

**Set up alerts for:**
- High error rates (>5% of requests)
- Guardian quarantine events
- Unusual traffic patterns
- Resource exhaustion (>80% memory/disk)
- Failed authentication attempts

## 📚 Additional Resources

- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Last Updated:** 2026-02-06  
**Version:** 0.0.1  
**Maintainer:** lollmsBot Development Team

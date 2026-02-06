# Configuring Ollama Cloud API for RC2

## Current Status ✅

You have **three Ollama API keys** configured in organizational secrets:

1. **OLLAMA_API_KEY** - Primary key
2. **OLLAMA_PROXY_API_KEY** - Proxy key  
3. **OLLAMA_TURBO_CLOUD_API_KEY** - Turbo cloud key

These keys are ready to use but need to be mapped to environment variables.

---

## Quick Start

### Option 1: Test Locally (Recommended First Step)

```bash
# Export one of your keys
export OLLAMA_API_KEY="your-actual-key-here"

# Run the test
python3 test_ollama_connection.py
```

**Expected Output:**
```
✅ Successfully connected to Ollama Cloud!
📋 Found 50+ models
🎯 RC2 Model Availability Check:
   ✅ kimi-k2.5
   ✅ deepseek-v3.1:671b
   ... (all 17 RC2 models)
```

---

### Option 2: Use in GitHub Actions

Create `.github/workflows/test-ollama.yml`:

```yaml
name: Test Ollama Connection

on:
  workflow_dispatch:  # Manual trigger
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Test Ollama Connection (Primary Key)
        env:
          OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
        run: python3 test_ollama_connection.py
      
      # Optional: Test with other keys
      - name: Test Ollama Connection (Proxy Key)
        if: always()
        env:
          OLLAMA_PROXY_API_KEY: ${{ secrets.OLLAMA_PROXY_API_KEY }}
        run: python3 test_ollama_connection.py
      
      - name: Test Ollama Connection (Turbo Key)
        if: always()
        env:
          OLLAMA_TURBO_CLOUD_API_KEY: ${{ secrets.OLLAMA_TURBO_CLOUD_API_KEY }}
        run: python3 test_ollama_connection.py
```

---

### Option 3: Add to Existing Workflows

If you have existing GitHub Actions workflows, add the environment mapping:

```yaml
jobs:
  your-job:
    runs-on: ubuntu-latest
    env:
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
    steps:
      # your existing steps...
```

---

## Understanding Your Three Keys

### OLLAMA_API_KEY (Primary)
- **Use for:** Standard RC2 operations
- **Best for:** Most tasks, default choice
- **Rate limits:** Standard tier
- **Cost:** Standard pricing

### OLLAMA_PROXY_API_KEY (Proxy)
- **Use for:** Routing through proxy
- **Best for:** Network-restricted environments
- **May require:** Different endpoint configuration
- **Consider:** Latency may be higher

### OLLAMA_TURBO_CLOUD_API_KEY (Turbo)
- **Use for:** High-performance tasks
- **Best for:** Time-sensitive operations
- **Benefits:** Faster response times
- **Cost:** Premium pricing (likely higher)

---

## RC2 Configuration

### Priority Order

The test script checks keys in this order:

1. `OLLAMA_API_KEY` (primary)
2. `OLLAMA_PROXY_API_KEY` (proxy)
3. `OLLAMA_TURBO_CLOUD_API_KEY` (turbo)
4. Other fallbacks...

**Recommendation:** Start with `OLLAMA_API_KEY` for testing.

### Failover Strategy

For production RC2 deployment, you can configure failover:

```python
# In rc2/core/model_pool.py (future implementation)
RC2_API_KEYS = {
    "primary": os.getenv("OLLAMA_API_KEY"),
    "proxy": os.getenv("OLLAMA_PROXY_API_KEY"),
    "turbo": os.getenv("OLLAMA_TURBO_CLOUD_API_KEY"),
}

# Use primary, fall back to proxy, then turbo
for key_type in ["primary", "proxy", "turbo"]:
    if RC2_API_KEYS[key_type]:
        try:
            return make_request(RC2_API_KEYS[key_type])
        except:
            continue
```

---

## Testing Checklist

Run these tests **before** implementing RC2:

- [ ] Test with `OLLAMA_API_KEY`
  ```bash
  export OLLAMA_API_KEY="your-key"
  python3 test_ollama_connection.py
  ```

- [ ] Test with `OLLAMA_PROXY_API_KEY` (optional)
  ```bash
  export OLLAMA_PROXY_API_KEY="your-key"
  python3 test_ollama_connection.py
  ```

- [ ] Test with `OLLAMA_TURBO_CLOUD_API_KEY` (optional)
  ```bash
  export OLLAMA_TURBO_CLOUD_API_KEY="your-key"
  python3 test_ollama_connection.py
  ```

- [ ] Verify all 17 RC2 models are available
- [ ] Test basic model inference
- [ ] Document which key works best

---

## Troubleshooting

### "No API key found"

**Problem:** Keys are in secrets but not mapped to environment

**Solution:** Export the key locally or map in workflow:
```bash
export OLLAMA_API_KEY="your-key-here"
```

### "Authentication failed (401)"

**Problem:** Invalid or expired API key

**Solution:**
1. Verify key is correct (check organizational secrets)
2. Try a different key (proxy or turbo)
3. Contact Ollama support to verify key status

### "Connection timeout"

**Problem:** Network connectivity issues

**Solution:**
1. Check internet connection
2. Try `OLLAMA_PROXY_API_KEY` if behind firewall
3. Check if endpoints are blocked

### "Endpoint not found (404)"

**Problem:** Incorrect API endpoint

**Solution:**
- Test script tries multiple endpoints automatically
- If all fail, Ollama Cloud may have changed endpoints
- Check Ollama documentation for current API base URL

### "Model XYZ not available"

**Problem:** Specific RC2 model not in your plan

**Solution:**
1. Some models may require premium access
2. Check your Ollama Cloud subscription tier
3. Consider using `OLLAMA_TURBO_CLOUD_API_KEY` for expanded access
4. Contact Ollama to upgrade plan if needed

---

## Next Steps

### 1. Test Connection (Do This First!)

```bash
# Choose which key to test
export OLLAMA_API_KEY="your-actual-key-from-secrets"

# Run test
python3 test_ollama_connection.py
```

### 2. Document Results

Note which key works and what models are available:

```
✅ OLLAMA_API_KEY: Works, 52 models available
✅ All 17 RC2 models available
⏱️  Average latency: 350ms
```

### 3. Configure RC2

Once connection is verified:

```bash
# Add to .env (gitignored)
OLLAMA_API_KEY=your-key-here
RC2_ENABLED=true
RC2_PRIVACY_LEVEL=HIGH
```

### 4. Begin RC2 Implementation

Follow `RC2_PRODUCTION_PLAN.md` to implement:
- Week 1: Foundation (sub-agents, model pool, privacy router)
- Week 2-3: 8 Pillars
- Week 4+: Safety, testing, documentation

---

## Security Best Practices

✅ **DO:**
- Store keys in GitHub organizational secrets
- Use environment variables for runtime access
- Mask keys in logs (test script does this)
- Use `.env` files locally (gitignored)
- Rotate keys periodically

❌ **DON'T:**
- Hardcode keys in source code
- Commit keys to git
- Share keys in public channels
- Log full key values
- Use same key for dev and prod

---

## Cost Monitoring

Before deploying RC2 to production:

1. **Set Budget Limits:**
   ```python
   RC2_DAILY_LIMIT=50  # USD per day
   RC2_MONTHLY_LIMIT=500  # USD per month
   ```

2. **Track Usage:**
   - Monitor API calls per model
   - Track costs per key type
   - Set alerts at 50%, 75%, 90%

3. **Optimize:**
   - Use cheaper models when possible
   - Cache responses
   - Implement early exit for simple queries
   - Fallback to local models

---

## Summary

- ✅ You have 3 Ollama API keys in organizational secrets
- ✅ Test script updated to check all three
- ⏳ **Next:** Export a key and run `python3 test_ollama_connection.py`
- 🚀 **Then:** Begin RC2 implementation once connection verified

**Questions?** Check `RC2_PRODUCTION_PLAN.md` for full implementation details.

# Ollama Cloud API Configuration Guide

**Date:** 2026-02-06  
**Status:** Configuration Required

---

## 🔍 Current Status

✅ **Repository:** Grumpified-OGGVCT/lollmsBot-GrumpiFied  
✅ **GitHub Actions:** Active  
✅ **Test Script:** Created (`test_ollama_connection.py`)  
❌ **API Key:** Not yet mapped to environment variables  

---

## 📋 What We Found

The Ollama Cloud API key exists in **GitHub repository secrets** (organization level), but it's not currently mapped to environment variables in the CI/CD workflow.

### Test Results:
```
🔍 Searching for Ollama API key in environment variables...
❌ No Ollama API key found in environment variables

Checked variables:
- OLLAMA_API_KEY
- OLLAMA_CLOUD_API_KEY  
- OLLAMA_KEY
- RC2_API_KEY
- RC2_OLLAMA_KEY
```

---

## ✅ How to Configure

### Option 1: Add to Workflow (Recommended for CI/CD)

If you have workflow access, add to `.github/workflows/your-workflow.yml`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      # Map organization secret to environment variable
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
      # Or if it's named differently:
      # OLLAMA_API_KEY: ${{ secrets.OLLAMA_CLOUD_KEY }}
    steps:
      - uses: actions/checkout@v3
      - name: Test Ollama Connection
        run: python3 test_ollama_connection.py
```

### Option 2: Local Development

For local testing, create `.env` file:

```bash
# .env (DO NOT COMMIT THIS FILE)
OLLAMA_API_KEY=your_actual_api_key_here
```

Then load in your scripts:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: Runtime Configuration

Add to `lollmsbot/config.py`:

```python
@dataclass
class RC2Settings:
    """Reflective Constellation 2.0 configuration."""
    
    # Ollama Cloud API key
    ollama_api_key: Optional[str] = field(default=None)
    ollama_cloud_endpoint: str = field(default="https://api.ollama.cloud")
    
    @classmethod
    def from_env(cls) -> "RC2Settings":
        """Load RC 2.0 settings from environment."""
        
        # Try multiple possible env var names
        api_key = (
            os.getenv("OLLAMA_API_KEY") or
            os.getenv("OLLAMA_CLOUD_API_KEY") or
            os.getenv("RC2_API_KEY") or
            os.getenv("OLLAMA_KEY")
        )
        
        return cls(
            ollama_api_key=api_key,
            ollama_cloud_endpoint=os.getenv("OLLAMA_CLOUD_ENDPOINT", "https://api.ollama.cloud"),
            # ... rest of config
        )
```

---

## 🧪 Testing the Connection

Once configured, test with:

```bash
# Export the key (don't commit this!)
export OLLAMA_API_KEY="your-key-here"

# Run test
python3 test_ollama_connection.py
```

**Expected output when working:**
```
✅ Successfully connected to Ollama Cloud!
📋 Found 50+ models
🎯 RC2 Model Availability Check:
   ✅ kimi-k2.5
   ✅ deepseek-v3.1:671b
   ✅ cogito-2.1:671b
   ... etc
```

---

## 🔐 Secret Names to Check

Your organization may have the secret named as:
- `OLLAMA_API_KEY`
- `OLLAMA_CLOUD_API_KEY`
- `OLLAMA_CLOUD_KEY`
- `OLLAMA_KEY`
- Custom name

**To find the exact name:**
1. Go to: https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied/settings/secrets/actions
2. Look for secrets with "ollama" in the name
3. Use that exact name in workflow mapping

---

## 📝 RC2 Configuration Integration

Once API key is available, update `.env.example`:

```bash
# ============================================
# REFLECTIVE CONSTELLATION 2.0 (Optional)
# ============================================

# Enable RC 2.0 sub-agent system (default: false)
RC2_ENABLED=false

# Ollama Cloud API Key (REQUIRED if RC2_ENABLED=true)
OLLAMA_API_KEY=your_api_key_here

# Ollama Cloud endpoint
OLLAMA_CLOUD_ENDPOINT=https://api.ollama.cloud

# Default privacy level (CRITICAL, HIGH, MEDIUM, LOW)
RC2_PRIVACY_LEVEL=HIGH

# Enable specific features (all default to false)
RC2_CONSTITUTIONAL_CONSENSUS=false  # Byzantine consensus (2x API calls)
RC2_SELF_MODIFICATION=false         # Self-modification proposals
RC2_VISUAL_MONITORING=false         # Screenshot analysis
RC2_META_LEARNING=false             # Learning optimization

# TEE Support (if available)
RC2_TEE_AVAILABLE=false
RC2_TEE_PROVIDER=  # intel_tdx or arm_cca

# Cost Controls
RC2_DAILY_LIMIT_USD=50
RC2_MONTHLY_LIMIT_USD=500

# Model Assignments (8 Pillars)
# These can be customized if different models preferred
RC2_SOUL_PRIMARY=kimi-k2.5
RC2_SOUL_BACKUP=mistral-large-3
RC2_GUARDIAN_GOVERNOR=deepseek-v3.1:671b
RC2_GUARDIAN_AUDITOR=cogito-2.1:671b
# ... etc for all 8 pillars
```

---

## 🚀 Next Steps

1. **Verify Secret Exists:**
   - Check: https://github.com/Grumpified-OGGVCT/settings/secrets/actions (org level)
   - Or: https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied/settings/secrets/actions (repo level)

2. **Map to Environment:**
   - Update GitHub workflow to expose secret
   - Or provide for local testing

3. **Re-run Test:**
   ```bash
   python3 test_ollama_connection.py
   ```

4. **Begin Implementation:**
   - Once test passes, ready to start RC2 implementation
   - Will have confirmed access to all required Ollama Cloud models

---

## 🔒 Security Notes

⚠️ **NEVER commit API keys to the repository!**

✅ **Safe practices:**
- Store in GitHub Secrets (organization or repository level)
- Map to environment variables in workflows
- Use `.env` files locally (add to `.gitignore`)
- Never print full API keys in logs (mask: `key[:4]..."..."+key[-4:]`)

❌ **Unsafe practices:**
- Hardcoding in source files
- Committing to version control
- Printing in plain text logs
- Sharing in public channels

---

## 📞 Support

If API key is not available:
1. Check with repository owner/admin
2. Verify organization secrets at org level
3. Request access if needed
4. Consider using alternative Ollama deployment (local instance)

---

**Status:** Configuration pending - ready to test once API key is mapped  
**Test Script:** `test_ollama_connection.py` (ready to use)  
**Next Action:** Map `OLLAMA_API_KEY` secret to environment variable

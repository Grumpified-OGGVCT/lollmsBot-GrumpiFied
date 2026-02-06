# API Reference Guide - Ollama Cloud & OpenRouter

**Version:** 1.0  
**Date:** 2026-02-06  
**Status:** Official Specifications

---

## 📚 Official Documentation Sources

- **Ollama Cloud:** https://docs.ollama.com/cloud
- **Ollama API:** https://docs.ollama.com/reference/api
- **OpenRouter Free Router:** https://openrouter.ai/docs/guides/routing/routers/free-router
- **OpenRouter API:** https://openrouter.ai/docs

---

## 🔷 Ollama Cloud API

### Base URL
```
https://ollama.com/api
```

### Authentication
```python
headers = {
    "Authorization": f"Bearer {OLLAMA_API_KEY}",
    "Content-Type": "application/json"
}
```

### List Models
```bash
curl https://ollama.com/api/tags \
  -H "Authorization: Bearer $OLLAMA_API_KEY"
```

**Response Format:**
```json
{
  "models": [
    {
      "name": "gpt-oss:120b",
      "modified_at": "2024-01-15T10:30:00Z",
      "size": 123456789
    }
  ]
}
```

### Chat Completion
```bash
curl https://ollama.com/api/chat \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:120b",
    "messages": [{
      "role": "user",
      "content": "Why is the sky blue?"
    }],
    "stream": false
  }'
```

### Python Client
```python
import os
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

messages = [
    {
        'role': 'user',
        'content': 'Why is the sky blue?',
    },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
    print(part['message']['content'], end='', flush=True)
```

### Supported Capabilities
- ✅ Streaming
- ✅ Thinking mode
- ✅ Structured Outputs
- ✅ Vision
- ✅ Embeddings
- ✅ Tool calling
- ✅ Web search

### Cloud Models
All models ending in `-cloud` suffix:
- `gpt-oss:120b-cloud`
- `kimi-k2.5-cloud`
- `deepseek-v3.1:671b-cloud`
- etc.

---

## 🔶 OpenRouter API

### Base URL
```
https://openrouter.ai/api/v1
```

### Authentication
```python
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied",
    "X-Title": "LollmsBot"
}
```

### List Models
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

**Response Format:**
```json
{
  "data": [
    {
      "id": "meta-llama/llama-3.2-3b-instruct:free",
      "name": "Llama 3.2 3B Instruct (free)",
      "pricing": {
        "prompt": "0",
        "completion": "0"
      }
    }
  ]
}
```

### Free Models Router
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/free",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Response includes which model was used:**
```json
{
  "id": "gen-...",
  "model": "upstage/solar-pro-3:free",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "..."
    }
  }]
}
```

### Python Example
```python
import requests
import os

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo",
        "X-Title": "Your App Name"
    },
    json={
        "model": "openrouter/free",
        "messages": [
            {"role": "user", "content": "Hello! What can you help me with?"}
        ]
    }
)

data = response.json()
print(data['choices'][0]['message']['content'])
print(f"Model used: {data['model']}")  # Shows which free model was selected
```

### How Free Router Works
1. **Request Analysis:** Analyzes required capabilities (vision, tools, etc.)
2. **Model Filtering:** Filters free models supporting those capabilities
3. **Random Selection:** Randomly selects from filtered pool
4. **Response Tracking:** Returns which model was actually used

### Free Model Examples
- `deepseek/deepseek-r1:free`
- `meta-llama/llama-3.2-3b-instruct:free`
- `qwen/qwen-2.5-7b-instruct:free`
- `upstage/solar-pro-3:free`

**Note:** Free model availability changes frequently. Check https://openrouter.ai/models?pricing=free

---

## 🔄 Multi-Provider Integration

### Request Routing Pattern

```python
class MultiProviderClient:
    def __init__(self):
        self.ollama_keys = [
            os.getenv("OLLAMA_API_KEY"),
            os.getenv("OLLAMA_API_KEY_2"),
        ]
        self.openrouter_keys = [
            os.getenv("OPENROUTER_API_KEY_1"),
            os.getenv("OPENROUTER_API_KEY_2"),
            os.getenv("OPENROUTER_API_KEY_3"),
        ]
    
    async def chat(self, messages, model=None):
        """Route request to optimal provider."""
        
        # If specific RC2 model requested, use Ollama
        if model and model in RC2_MODELS:
            return await self.call_ollama(messages, model)
        
        # Otherwise, try OpenRouter free tier first (cycle keys)
        for key in self.openrouter_keys:
            if not self.is_quota_exhausted(key):
                try:
                    return await self.call_openrouter_free(messages, key)
                except QuotaExhaustedError:
                    self.mark_exhausted(key)
                    continue
        
        # All OpenRouter exhausted, fallback to Ollama
        return await self.call_ollama_load_balanced(messages)
```

### Ollama Cloud Example

```python
from ollama import Client
import os

class OllamaCloudClient:
    def __init__(self, api_key):
        self.client = Client(
            host="https://ollama.com",
            headers={'Authorization': f'Bearer {api_key}'}
        )
    
    def chat(self, model, messages, stream=True):
        """Chat with Ollama Cloud model."""
        for part in self.client.chat(model, messages=messages, stream=stream):
            yield part['message']['content']

# Usage
ollama = OllamaCloudClient(os.getenv("OLLAMA_API_KEY"))

for chunk in ollama.chat("gpt-oss:120b", [
    {"role": "user", "content": "Explain quantum computing"}
]):
    print(chunk, end='', flush=True)
```

### OpenRouter Free Router Example

```python
import requests
import os

class OpenRouterFreeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = "https://openrouter.ai/api/v1"
    
    def chat(self, messages):
        """Chat using OpenRouter's free model router."""
        response = requests.post(
            f"{self.endpoint}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",
                "X-Title": "Your App"
            },
            json={
                "model": "openrouter/free",
                "messages": messages
            }
        )
        
        if response.status_code == 429:
            raise QuotaExhaustedError("Free tier quota exhausted")
        
        data = response.json()
        return {
            "content": data['choices'][0]['message']['content'],
            "model_used": data['model']  # Which free model was selected
        }

# Usage with key cycling
openrouter_keys = [
    os.getenv("OPENROUTER_API_KEY_1"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
]

for key in openrouter_keys:
    try:
        client = OpenRouterFreeClient(key)
        result = client.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(f"Response: {result['content']}")
        print(f"Model: {result['model_used']}")
        break  # Success, stop trying
    except QuotaExhaustedError:
        print(f"Key {key[:10]}... exhausted, trying next")
        continue
```

---

## 🔒 Rate Limiting

### Ollama Cloud
- Rate limits apply per API key
- Typical: 1000-2000 requests/hour
- Returns `429 Too Many Requests` when exceeded
- Retry-After header indicates when to retry

### OpenRouter Free Tier
- Daily/monthly quotas per API key
- Varies by free model availability
- Returns `429` when quota exhausted
- Quota resets typically every 24 hours

### Handling Rate Limits

```python
def handle_response(response, key_name):
    """Handle API response with rate limit detection."""
    
    if response.status_code == 429:
        # Rate limited
        retry_after = response.headers.get('Retry-After', 3600)
        mark_key_limited(key_name, duration=int(retry_after))
        raise RateLimitError(f"{key_name} rate limited for {retry_after}s")
    
    elif response.status_code == 401:
        # Auth failed
        raise AuthError(f"{key_name} authentication failed")
    
    elif response.status_code == 503:
        # Service unavailable
        raise ServiceUnavailableError(f"{key_name} temporarily unavailable")
    
    return response.json()
```

---

## 💰 Cost Tracking

### Ollama Cloud Pricing
- Pay per token usage
- Varies by model
- Typically $0.001-0.01 per 1K tokens
- Check current pricing: https://ollama.com/pricing

### OpenRouter Free Router
- **Cost: $0** (completely free)
- No charge for using `openrouter/free`
- Quota-based (not cost-based)
- Multiple keys multiply quota

### Cost Calculation

```python
def calculate_cost(provider, model, tokens):
    """Calculate API call cost."""
    
    if provider == "openrouter" and model == "openrouter/free":
        return 0.0  # Free
    
    elif provider == "ollama":
        # Example pricing (check actual rates)
        rates = {
            "gpt-oss:120b": 0.01,  # per 1K tokens
            "kimi-k2.5": 0.005,
            "deepseek-v3.1:671b": 0.015,
        }
        rate = rates.get(model, 0.01)  # default rate
        return (tokens / 1000) * rate
    
    return 0.0
```

---

## 🧪 Testing Scripts

### Test Ollama Cloud Connection

```python
import requests
import os

def test_ollama():
    response = requests.get(
        "https://ollama.com/api/tags",
        headers={
            "Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"
        }
    )
    
    if response.status_code == 200:
        models = response.json()['models']
        print(f"✅ Ollama Cloud: {len(models)} models available")
        for model in models[:5]:
            print(f"  - {model['name']}")
    else:
        print(f"❌ Ollama Cloud failed: {response.status_code}")

test_ollama()
```

### Test OpenRouter Free Router

```python
import requests
import os

def test_openrouter_free():
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY_1']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "Say 'OK'"}],
            "max_tokens": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ OpenRouter Free: Success")
        print(f"   Model used: {data['model']}")
        print(f"   Response: {data['choices'][0]['message']['content']}")
    elif response.status_code == 429:
        print(f"⚠️  OpenRouter Free: Quota exhausted")
    else:
        print(f"❌ OpenRouter Free failed: {response.status_code}")

test_openrouter_free()
```

---

## 📊 Model Comparison

| Model | Provider | Cost | Capabilities | Best For |
|-------|----------|------|--------------|----------|
| `openrouter/free` | OpenRouter | $0 | Auto-selected | General tasks, max free usage |
| `gpt-oss:120b` | Ollama Cloud | $$ | All | Large context, complex reasoning |
| `kimi-k2.5` | Ollama Cloud | $$ | Vision, thinking | RC2 Soul pillar, multimodal |
| `deepseek-v3.1:671b` | Ollama Cloud | $$$ | Thinking, tools | RC2 Guardian, deep analysis |

---

## ✅ Quick Reference

### Ollama Cloud
- **Endpoint:** `https://ollama.com/api`
- **List:** `/tags`
- **Chat:** `/chat`
- **Auth:** `Authorization: Bearer <key>`

### OpenRouter
- **Endpoint:** `https://openrouter.ai/api/v1`
- **List:** `/models`
- **Chat:** `/chat/completions`
- **Auth:** `Authorization: Bearer <key>`
- **Free:** Use model `openrouter/free`

### Environment Variables
```bash
# Ollama Cloud
export OLLAMA_API_KEY="your-key"
export OLLAMA_API_KEY_2="your-key-2"

# OpenRouter
export OPENROUTER_API_KEY_1="your-key-1"
export OPENROUTER_API_KEY_2="your-key-2"
export OPENROUTER_API_KEY_3="your-key-3"
```

---

**Status:** ✅ Complete API Reference  
**Last Updated:** 2026-02-06  
**Sources:** Official documentation

# Updated Multi-Provider Routing Strategy

**Date:** 2026-02-06  
**Version:** 2.0 (Corrected)  
**Status:** Cost-Optimized Strategy

---

## 🎯 Corrected Routing Strategy

### Key Insight: OpenRouter Free Model Router

OpenRouter provides an **automatic free model router** that:
- Automatically routes to available free tier models
- Has daily/monthly quotas per API key
- **3 keys = 3x the free quota**
- Perfect for cost optimization

### Strategic Priority

```
1st Priority: OpenRouter Free Tier (3 keys cycling)
    ↓ (only when ALL 3 exhausted OR specialized model needed)
2nd Priority: Ollama Cloud (2 keys load balanced)
```

---

## 🔄 Updated Routing Flow

### Detailed Decision Tree

```
User Request
    ↓
┌─────────────────────────────────────────┐
│ Does request need RC2 specialized model?│
└────────┬───────────────────────┬────────┘
         NO                      YES
         ↓                       ↓
    ┌────────────────┐    ┌──────────────┐
    │ OpenRouter     │    │ Ollama Cloud │
    │ Free Tier      │    │ (specialized)│
    │ (3 keys cycle) │    │ Load balanced│
    └────────┬───────┘    └──────────────┘
             ↓
    Try Key 1 → Quota OK? → Use it
             ↓ NO
    Try Key 2 → Quota OK? → Use it
             ↓ NO
    Try Key 3 → Quota OK? → Use it
             ↓ NO (all exhausted)
    ┌────────────────────────┐
    │ Notify User:           │
    │ "Free tier exhausted   │
    │  switching to paid"    │
    └────────┬───────────────┘
             ↓
    Fallback to Ollama Cloud
```

### Ollama Load Balancing

```python
ollama_key_index = 0

def get_next_ollama_key():
    """Alternate between Ollama keys for load balancing."""
    global ollama_key_index
    keys = [OLLAMA_KEY_1, OLLAMA_KEY_2]
    key = keys[ollama_key_index]
    ollama_key_index = (ollama_key_index + 1) % 2
    return key

# Results in:
# Request 1 → Ollama Key 1
# Request 2 → Ollama Key 2
# Request 3 → Ollama Key 1
# Request 4 → Ollama Key 2
# (continues alternating)
```

---

## 💰 Cost Optimization Strategy

### Stage 1: Free Tier Maximum Usage

**OpenRouter Key Cycling:**
```python
class OpenRouterFreeManager:
    def __init__(self):
        self.keys = [
            OPENROUTER_KEY_1,
            OPENROUTER_KEY_2,
            OPENROUTER_KEY_3
        ]
        self.current_index = 0
        self.quota_status = {
            OPENROUTER_KEY_1: {"exhausted": False, "reset_at": None},
            OPENROUTER_KEY_2: {"exhausted": False, "reset_at": None},
            OPENROUTER_KEY_3: {"exhausted": False, "reset_at": None},
        }
    
    def get_next_available_key(self):
        """Get next key with quota remaining."""
        # Try each key in cycle
        for _ in range(len(self.keys)):
            key = self.keys[self.current_index]
            
            if not self.quota_status[key]["exhausted"]:
                self.current_index = (self.current_index + 1) % len(self.keys)
                return key
            
            # Check if quota reset time passed
            if self.quota_status[key]["reset_at"]:
                if datetime.now() > self.quota_status[key]["reset_at"]:
                    self.quota_status[key]["exhausted"] = False
                    self.quota_status[key]["reset_at"] = None
                    return key
            
            self.current_index = (self.current_index + 1) % len(self.keys)
        
        # All keys exhausted
        return None
    
    def mark_exhausted(self, key, reset_hours=24):
        """Mark key as quota exhausted."""
        self.quota_status[key]["exhausted"] = True
        self.quota_status[key]["reset_at"] = datetime.now() + timedelta(hours=reset_hours)
```

### Stage 2: Ollama Cloud Fallback

Only used when:
1. All 3 OpenRouter keys exhausted, OR
2. Specialized RC2 model needed (kimi, deepseek, cogito, etc.)

**Cost Impact:**
- **Without optimization:** $30-50/month (Ollama primary)
- **With optimization:** $0-20/month (free tier + light Ollama)
- **Savings:** 40-70%

---

## 📊 Updated Provider Roles

### OpenRouter (3 Keys) - PRIMARY for General Tasks

**Role:** Free tier cost optimization  
**Usage:** 80-90% of general requests  
**Cost:** $0/month until quotas exhausted  

**Quota Management:**
- Each key has independent quota
- Cycle through keys to maximize usage
- Track exhaustion per key
- Auto-reset after quota refresh (24h typical)

**Best For:**
- General conversation
- Simple questions
- Code generation (non-specialized)
- Document analysis
- Any task not needing RC2 models

---

### Ollama Cloud (2 Keys) - SECONDARY for Specialized/Overflow

**Role:** Specialized models + overflow  
**Usage:** 10-20% of requests  
**Cost:** $10-30/month (lighter usage)

**Load Balancing:**
- Alternate between keys evenly
- Both keys share load 50/50
- Failover if one rate limited

**Best For:**
- RC2 8-pillar specialized models
- After OpenRouter exhausted
- Privacy-sensitive operations
- Specific model requirements

---

## 🔄 Complete Routing Logic

### Implementation

```python
class MultiProviderRouter:
    def __init__(self):
        self.openrouter_manager = OpenRouterFreeManager()
        self.ollama_manager = OllamaLoadBalancer()
        self.rc2_models = [
            "kimi-k2.5",
            "deepseek-v3.1:671b",
            "cogito-2.1:671b",
            # ... all 17 RC2 models
        ]
    
    async def route_request(self, task, privacy_level="MEDIUM"):
        """Route request to optimal provider."""
        
        # Priority 1: CRITICAL privacy = LOCAL only
        if privacy_level == "CRITICAL":
            return await self.call_local_model(task)
        
        # Priority 2: RC2 specialized model = Ollama
        if task.model in self.rc2_models:
            return await self.ollama_manager.call(task)
        
        # Priority 3: Try OpenRouter free tier (cycle keys)
        openrouter_key = self.openrouter_manager.get_next_available_key()
        
        if openrouter_key:
            try:
                result = await self.call_openrouter_free(
                    key=openrouter_key,
                    task=task
                )
                return result
                
            except QuotaExhaustedError:
                # Mark this key exhausted, try next
                self.openrouter_manager.mark_exhausted(openrouter_key)
                return await self.route_request(task, privacy_level)
        
        # Priority 4: All OpenRouter exhausted, notify and use Ollama
        logger.warning("OpenRouter free tier exhausted, switching to Ollama Cloud")
        
        # Notify user (optional, configurable)
        if self.config.notify_on_tier_switch:
            await self.notify_user(
                "Free tier quota exhausted. Switching to paid tier.\n"
                "Note: This may incur costs. Quota resets in 24 hours."
            )
        
        # Fallback to Ollama (load balanced)
        return await self.ollama_manager.call(task)
```

---

## 📈 Quota Tracking

### Per-Key Tracking

```python
class QuotaTracker:
    def __init__(self):
        self.usage = {
            "OPENROUTER_KEY_1": {
                "requests_today": 0,
                "quota_limit": 1000,  # Example
                "reset_time": "00:00 UTC",
                "exhausted": False
            },
            "OPENROUTER_KEY_2": {...},
            "OPENROUTER_KEY_3": {...},
        }
    
    def check_quota(self, key):
        """Check if key has quota remaining."""
        status = self.usage[key]
        
        # Check if reset time passed
        if datetime.now() >= status["reset_time"]:
            status["requests_today"] = 0
            status["exhausted"] = False
        
        return not status["exhausted"]
    
    def record_request(self, key):
        """Record API request and check limits."""
        self.usage[key]["requests_today"] += 1
        
        if self.usage[key]["requests_today"] >= self.usage[key]["quota_limit"]:
            self.usage[key]["exhausted"] = True
            logger.warning(f"{key} quota exhausted")
    
    def handle_quota_error(self, key, reset_hours=24):
        """Handle 429 quota exceeded response."""
        self.usage[key]["exhausted"] = True
        self.usage[key]["reset_time"] = datetime.now() + timedelta(hours=reset_hours)
```

---

## 🔔 User Notifications

### When to Notify

```python
NOTIFICATION_CONFIG = {
    "first_key_exhausted": False,      # Don't notify, just cycle
    "second_key_exhausted": False,     # Don't notify, just cycle
    "third_key_exhausted": True,       # NOTIFY: switching to paid
    "ollama_rate_limited": True,       # NOTIFY: temporary issue
    "all_providers_down": True,        # NOTIFY: critical
}

async def notify_user(message, level="info"):
    """Send notification to user."""
    if level == "info":
        return {
            "success": True,
            "response": result,
            "notice": message
        }
    elif level == "warning":
        return {
            "success": True,
            "response": result,
            "warning": message
        }
    elif level == "error":
        return {
            "success": False,
            "error": message
        }
```

### Example Messages

```python
MESSAGES = {
    "free_tier_exhausted": (
        "ℹ️ Free tier quota exhausted. Switching to paid tier.\n"
        "💡 Quota resets in ~24 hours.\n"
        "💰 Paid tier usage will incur costs."
    ),
    
    "ollama_fallback": (
        "ℹ️ Using Ollama Cloud for specialized model.\n"
        "This request requires specific capabilities."
    ),
    
    "all_exhausted": (
        "⚠️ All API quotas exhausted.\n"
        "Please wait for quota reset or check your limits."
    )
}
```

---

## 🎯 Updated Cost Projections

### Scenario 1: Light Usage (< 500 req/day)

| Stage | Provider | Requests | Cost |
|-------|----------|----------|------|
| Free Tier | OpenRouter x3 | 450 | $0 |
| Specialized | Ollama | 50 | $5-10 |
| **Total** | | **500** | **$5-10/month** |

### Scenario 2: Medium Usage (1000-2000 req/day)

| Stage | Provider | Requests | Cost |
|-------|----------|----------|------|
| Free Tier | OpenRouter x3 | 1500 | $0 |
| Overflow | Ollama | 500 | $15-25 |
| **Total** | | **2000** | **$15-25/month** |

### Scenario 3: Heavy Usage (3000+ req/day)

| Stage | Provider | Requests | Cost |
|-------|----------|----------|------|
| Free Tier | OpenRouter x3 | 2000 | $0 |
| Overflow | Ollama | 1000+ | $30-50 |
| **Total** | | **3000+** | **$30-50/month** |

**Cost Comparison:**
- **Old strategy:** $30-50/month (Ollama primary)
- **New strategy:** $5-50/month (free tier first)
- **Savings:** $10-25/month (20-50% reduction)

---

## 🔒 Updated Security Considerations

### Quota Exhaustion Attacks

```python
class RateLimitProtection:
    def __init__(self):
        self.user_limits = {}  # per-user rate limits
    
    def check_user_limit(self, user_id):
        """Prevent individual users from exhausting quotas."""
        user_usage = self.user_limits.get(user_id, 0)
        
        if user_usage > USER_DAILY_LIMIT:
            raise UserRateLimitError(
                f"User {user_id} exceeded daily limit"
            )
        
        return True
```

### Cost Control

```python
COST_LIMITS = {
    "daily_limit_usd": 50,
    "monthly_limit_usd": 500,
    "alert_at_percent": 75,
    "stop_at_percent": 100,
}

def check_budget(current_cost):
    """Enforce budget limits."""
    if current_cost >= DAILY_LIMIT * STOP_AT_PERCENT:
        raise BudgetExceededError("Daily budget exhausted")
    
    if current_cost >= DAILY_LIMIT * ALERT_AT_PERCENT:
        alert_admin("Approaching daily budget limit")
```

---

## 📋 Implementation Checklist

### Phase 1: OpenRouter Free Tier
- [ ] Implement quota tracking per key
- [ ] Implement key cycling logic
- [ ] Handle 429 responses (quota exceeded)
- [ ] Track reset times
- [ ] Test all 3 keys rotation

### Phase 2: Ollama Load Balancing
- [ ] Implement alternating key selection
- [ ] Track usage per key
- [ ] Handle rate limiting per key
- [ ] Failover between keys

### Phase 3: Unified Routing
- [ ] Implement routing decision logic
- [ ] Add RC2 model detection
- [ ] Implement fallback chain
- [ ] Add user notifications

### Phase 4: Monitoring
- [ ] Track quota usage per key
- [ ] Monitor costs per provider
- [ ] Alert on quota exhaustion
- [ ] Dashboard for quota status

---

## 🧪 Testing Strategy

### Test Cases

```python
# Test 1: OpenRouter cycling
test_openrouter_key_cycling()
  - Exhaust Key 1 → Should use Key 2
  - Exhaust Key 2 → Should use Key 3
  - Exhaust Key 3 → Should fallback to Ollama

# Test 2: Ollama load balancing
test_ollama_load_balancing()
  - Request 1 → Key 1
  - Request 2 → Key 2
  - Request 3 → Key 1 (cycle)

# Test 3: RC2 model routing
test_rc2_routing()
  - RC2 model → Should skip OpenRouter
  - Go directly to Ollama

# Test 4: Quota reset
test_quota_reset()
  - Exhaust key at 23:59
  - Wait until 00:01
  - Should reset and be available

# Test 5: User notifications
test_notifications()
  - Exhaust all OpenRouter → Should notify
  - Switch to Ollama → Should show message
```

---

## ✅ Summary of Changes

### From Previous Plan

**OLD:**
```
Ollama (primary) → OpenRouter (fallback)
Cost: $30-50/month
```

**NEW:**
```
OpenRouter Free (primary, 3 keys cycling) → 
Ollama Cloud (fallback, 2 keys load balanced)
Cost: $5-30/month (40-70% savings)
```

### Key Improvements

1. ✅ **Cost Optimization:** Free tier first saves $10-25/month
2. ✅ **Quota Maximization:** 3 keys = 3x free usage
3. ✅ **User Transparency:** Notify when switching to paid
4. ✅ **Load Balancing:** Ollama keys share load evenly
5. ✅ **Graceful Degradation:** Clear fallback chain

---

## 🚀 Next Steps

1. Update `test_all_api_keys.py` to test free tier routing
2. Implement `QuotaTracker` class
3. Implement `OpenRouterFreeManager` class
4. Implement `OllamaLoadBalancer` class
5. Update `MultiProviderRouter` with new logic
6. Add user notification system
7. Add monitoring for quota status
8. Update documentation with cost savings

---

**Version:** 2.0 (Corrected)  
**Status:** ✅ Strategy Updated  
**Cost Impact:** 40-70% reduction  
**Ready For:** Implementation

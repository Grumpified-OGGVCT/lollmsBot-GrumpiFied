# Unified Security Architecture

## Overview

All security features have been **consolidated into the Guardian module** (`lollmsbot/guardian.py`) to create a single, unified security authority for lollmsBot. This eliminates confusion and makes the security architecture clearer and easier to maintain.

## Architecture Decision

**Before**: Security features were split across multiple modules:
- `guardian.py` - Prompt injection, ethics, permissions
- `skill_scanner.py` - Skill threat detection
- `api_key_protection.py` - API key detection/redaction

**After**: **Everything in `guardian.py`** with unified threat detection

## Why This Is Better

1. **Single Source of Truth**: Guardian is THE security authority
2. **Less Confusion**: One place for all security logic
3. **Better Integration**: Security features work together seamlessly
4. **Easier Maintenance**: Update threat patterns in one place
5. **Clearer Responsibility**: Guardian's role is obvious

## Guardian Module Structure

```
lollmsbot/guardian.py
├── ThreatType (Enum)
│   ├── PROMPT_INJECTION
│   ├── DATA_EXFILTRATION
│   ├── CONTAINER_ESCAPE
│   ├── SLEEPER_AGENT
│   ├── PRIVILEGE_ESCALATION
│   ├── FILE_SYSTEM_ABUSE
│   ├── CREDENTIAL_HARVESTING
│   ├── API_KEY_EXPOSURE
│   └── ... (all threat types)
│
├── ThreatDetector (Class)
│   ├── THREAT_PATTERNS (all patterns by type)
│   ├── analyze() - unified threat analysis
│   ├── redact_api_keys() - key redaction
│   └── _handle_api_key_detection() - key tracking
│
├── AnomalyDetector (Class)
│   └── ... (behavioral analysis)
│
└── Guardian (Class) - Main API
    ├── check_input() - screen ALL incoming text
    ├── check_output() - screen ALL outgoing text
    ├── scan_skill_content() - scan skill files
    ├── redact_api_keys_from_text() - redact keys anywhere
    ├── check_tool_execution() - authorize tool use
    ├── audit_decision() - log AI decisions
    └── get_audit_report() - security reporting
```

## How To Use

### Check User Input (detects everything)

```python
from lollmsbot.guardian import get_guardian

guardian = get_guardian()

# Automatically detects:
# - Prompt injection
# - API keys
# - Malicious patterns
# - Container escape attempts
# - Everything!
is_safe, event = guardian.check_input(user_input, "chat")

if not is_safe:
    print(f"Blocked: {event.description}")
```

### Scan Skill Content

```python
# No more separate skill scanner!
is_safe, threats = guardian.scan_skill_content(
    skill_name="my-skill",
    content=skill_file_content
)

if not is_safe:
    print(f"Skill threats: {threats}")
```

### Redact API Keys

```python
# Built into Guardian
clean_text = guardian.redact_api_keys_from_text(text_with_keys)
```

### Check Output

```python
# Automatically redacts keys and checks for threats
is_safe, event = guardian.check_output(content, "public_channel")
```

## Threat Detection

The unified `ThreatDetector` class handles **all** threat types:

### Pattern Categories

1. **Prompt Injection**
   - "ignore previous instructions"
   - "you are now unrestricted"
   - OpenClaw-style: "install prerequisite"

2. **Data Exfiltration**
   - curl/wget POST requests
   - Zipping .env files
   - netcat connections

3. **Container Escape**
   - Docker socket access
   - Privileged execution
   - Namespace manipulation

4. **Sleeper Agents**
   - Trigger word checks
   - Long sleep commands
   - Scheduled execution

5. **API Keys**
   - OpenAI (sk-*, sk-proj-*)
   - Anthropic (sk-ant-*)
   - AWS (AKIA*)
   - Generic patterns

6. **Credential Harvesting**
   - Grep for .env files
   - Environment dumps
   - Secret file access

## Integration Points

### Awesome Skills Integration

```python
# awesome_skills_integration.py now uses Guardian
from lollmsbot.guardian import get_guardian

guardian = get_guardian()
is_safe, threats = guardian.scan_skill_content(skill_name, content)
```

### CLI Commands

```bash
# CLI uses Guardian for all security commands
lollmsbot skills scan <skill-name>      # Uses Guardian
lollmsbot skills security-report         # Uses Guardian
```

### Sandbox

```python
# Sandbox policy works with Guardian
from lollmsbot.guardian import get_guardian
from lollmsbot.sandbox.policy import MountPolicy

guardian = get_guardian()
policy = MountPolicy.default_policy()

# Guardian checks threats, policy enforces file access
```

## Configuration

All security configuration is Guardian-centric:

```bash
# .env
GUARDIAN_ENABLED=true
GUARDIAN_INJECTION_THRESHOLD=0.75
GUARDIAN_AUTO_QUARANTINE=true
AWESOME_SKILLS_SECURITY_SCANNING=true  # Uses Guardian
API_KEY_PROTECTION_ENABLED=true         # Uses Guardian
```

## Migration Guide

### If You Were Using SkillScanner

**Before**:
```python
from lollmsbot.skill_scanner import get_skill_scanner
scanner = get_skill_scanner()
result = scanner.scan_skill_file(skill_path)
```

**After**:
```python
from lollmsbot.guardian import get_guardian
guardian = get_guardian()
is_safe, threats = guardian.scan_skill_content(skill_name, content)
```

### If You Were Using APIKeyProtector

**Before**:
```python
from lollmsbot.api_key_protection import get_api_key_protector
protector = get_api_key_protector()
redacted = protector.redact_text(text)
```

**After**:
```python
from lollmsbot.guardian import get_guardian
guardian = get_guardian()
redacted = guardian.redact_api_keys_from_text(text)
```

## Benefits of Consolidation

### For Developers

1. **One import**: Just `from lollmsbot.guardian import get_guardian`
2. **Consistent API**: All security through Guardian methods
3. **Easy testing**: Mock one Guardian instead of multiple components
4. **Clear documentation**: One module to document

### For Users

1. **Simpler configuration**: Guardian-centric settings
2. **Better error messages**: All from Guardian
3. **Unified audit log**: One security event stream
4. **Clearer permissions**: Guardian decides everything

### For Maintenance

1. **Update patterns once**: In Guardian's ThreatDetector
2. **Add new threats easily**: Just extend THREAT_PATTERNS
3. **Fix bugs in one place**: No duplication
4. **Test comprehensively**: One security module to test

## Security Event Flow

```
User Input
    ↓
Guardian.check_input()
    ↓
ThreatDetector.analyze()
    ├─ Prompt Injection Check
    ├─ API Key Detection
    ├─ Data Exfiltration Patterns
    ├─ Container Escape Patterns
    ├─ Sleeper Agent Patterns
    └─ All Other Threats
    ↓
Security Event (if threat found)
    ↓
Audit Log
    ↓
Block/Allow/Challenge
```

## Audit Trail

All security events from all sources go to one audit log:

```bash
# View Guardian's unified audit log
cat ~/.lollmsbot/audit.log

# Example events:
# - prompt_injection_detected
# - api_key_exposure_detected  
# - skill_threat_detected
# - container_escape_attempt
# - all unified in one log
```

## Future Enhancements

Since everything is in Guardian now, future enhancements are easier:

1. **Add new threat type**: Just extend `ThreatType` enum and add patterns
2. **Machine learning integration**: Add ML-based detection to ThreatDetector
3. **Real-time updates**: Update patterns without changing architecture
4. **Custom rules**: Users can extend Guardian with custom patterns

## Summary

**Guardian is now the single, unified security authority for lollmsBot.**

- ✅ All threat detection in one place
- ✅ API key protection integrated
- ✅ Skill scanning integrated  
- ✅ Container escape prevention integrated
- ✅ Simpler architecture
- ✅ Easier to understand
- ✅ Easier to maintain

**Old modules** (`skill_scanner.py`, `api_key_protection.py`) are **deprecated** - all functionality is now in Guardian.

---

**Remember**: When you need security features, there's only one place to look: **Guardian**.

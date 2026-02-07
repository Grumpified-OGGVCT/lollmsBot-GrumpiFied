# Security Architecture and Threat Model

## Overview

This document describes lollmsBot's security architecture and how it protects against threats similar to those discovered in the OpenClaw ecosystem (as documented in [this security analysis](https://www.youtube.com/watch?v=ceEUO_i7aW4)).

## Threat Model

### 1. Malicious Skills ("Sleeper Agents")

**Threat**: Skills from public repositories that contain hidden malicious code, including:
- Dormant malware waiting for trigger words
- Data exfiltration to external servers
- Credential harvesting from environment files
- Container escape attempts

**Our Mitigations**:

#### Guardian Skill Scanning (`lollmsbot/guardian.py`)
- **Pre-load validation**: All skills are scanned before loading via `Guardian.scan_skill_content()`
- **Pattern-based detection**: Identifies known malicious patterns
- **Threat classification**: Categorizes by type and severity
- **Automatic blocking**: HIGH/CRITICAL threats are blocked immediately
- **Integrated with Guardian**: All skill security is handled by the unified Guardian module

**Detection Capabilities**:
- Data exfiltration (curl/wget POST requests, zip of .env files)
- Container escapes (Docker socket access, namespace manipulation)
- Sleeper agents (trigger words, scheduled execution)
- Privilege escalation (sudo, setuid, system file access)
- File system abuse (recursive deletion, disk operations)
- Credential harvesting (grep for API keys, environment dumps)
- Code injection (eval, exec, command substitution)
- Obfuscation (base64 decode, hex encoding)
- Prompt injection (ignore instructions, system overrides)

#### Curated Skills Repository
- Uses `awesome-claude-skills` repository for vetted skills only
- No public skill marketplace exposure
- All skills manually reviewed before inclusion
- Community vetting process

### 2. API Key Leakage and Harvesting

**Threat**: API keys exposed through:
- Unencrypted chat logs (Telegram, Discord, local files)
- Skills that exfiltrate .env files
- Users pasting keys directly in chat
- Credentials harvested from environment variables

**Our Mitigations**:

#### Guardian API Key Protection (`lollmsbot/guardian.py`)
- **Real-time detection**: Scans all inputs/outputs for API keys via `Guardian.check_input()/check_output()`
- **Automatic redaction**: Removes keys from logs and chat history via `Guardian.redact_api_keys_from_text()`
- **User warnings**: Alerts when keys are detected in input
- **Secure storage recommendations**: Guides users to use .env files
- **Integrated with Guardian**: All API key protection is handled by the unified Guardian module

**Protected Key Types**:
- OpenAI (sk-*, sk-proj-*)
- Anthropic (sk-ant-*)
- OpenRouter (sk-or-v1-*)
- Google (AIza*)
- AWS (AKIA*, aws_secret_access_key)
- Azure, Ollama, and generic API keys

**Features**:
- Keys never stored, only hashed for tracking
- Rotation recommendations after 90 days
- Usage statistics and security reports
- Prevention of key exposure in chat logs

### 3. Container Escape and Privilege Escalation

**Threat**: Skills attempting to:
- Break out of Docker containers
- Access host file system
- Gain root privileges
- Manipulate system resources

**Our Mitigations**:

#### Docker Sandbox (`lollmsbot/sandbox/`)
- **Strict mount policies**: Limited file system access
- **Read-only by default**: Write access requires explicit grant
- **Denied paths**: /etc, /sys, /proc, /dev, /boot, /root blocked
- **Permission gates**: Configurable access controls

#### Skill Scanner Detection
- Docker socket access patterns
- Privileged container execution
- Namespace manipulation (nsenter, unshare)
- System mount attempts
- Path traversal (../../)
- Container control mechanisms (cgroups, capabilities)

### 4. Prompt Injection Attacks

**Threat**: Malicious instructions embedded in:
- Skill files (SKILL.md, system-prompt.md)
- User inputs attempting to override system constraints
- Text files treated as executable commands by AI

**Our Mitigations**:

#### Guardian Layer (`lollmsbot/guardian.py`)
- **Multi-pattern detection**: Comprehensive injection patterns
- **Semantic analysis**: Identifies role confusion and delimiter attacks
- **Entropy analysis**: Detects obfuscated payloads
- **Skill-specific patterns**: Detects "install prerequisite" attacks

**Enhanced Patterns (OpenClaw-aware)**:
- "ignore previous instructions"
- "install prerequisite/dependency"
- "download and run/execute"
- "bypass gatekeeper/security"
- "remove quarantine attribute" (macOS specific)
- Fake system role markers
- Template/command injection

### 5. Semantic Attacks (Text as Code)

**Threat**: AI agents executing malicious instructions found in:
- README files
- Skill descriptions
- Documentation
- Comments in code

**Our Mitigations**:

#### Text-as-Executable Awareness
- All skill content treated as potentially executable
- Semantic validation of skill behavior vs. description
- LLM-based analysis (when enabled)
- Content integrity verification

#### Guardian Integration
- All text inputs screened before processing
- Context-aware validation
- Quarantine mode for critical threats
- Immutable audit trail

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Input                           │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  API Key Protection   │ ◄─── Detect & Redact Keys
        │  - Scan for keys      │
        │  - Redact from logs   │
        │  - Warn user          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Guardian Layer       │ ◄─── Prompt Injection Defense
        │  - Injection detect   │
        │  - Ethics check       │
        │  - Permission gates   │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Agent Processing     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Skill Loading?       │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Skill Scanner        │ ◄─── Pre-load Validation
        │  - Pattern detection  │
        │  - Threat analysis    │
        │  - Block if unsafe    │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Docker Sandbox       │ ◄─── Isolated Execution
        │  - Limited mounts     │
        │  - Permission policy  │
        │  - Resource limits    │
        └───────────────────────┘
```

## Defense in Depth

Our security model implements multiple layers:

1. **Input Validation** (Guardian + API Key Protection)
   - First line of defense against malicious input
   - Detects and blocks prompt injection
   - Redacts API keys from all text

2. **Skill Validation** (Skill Scanner)
   - Comprehensive pre-load security scanning
   - Pattern-based threat detection
   - Automatic blocking of unsafe skills

3. **Execution Isolation** (Docker Sandbox)
   - Containerized execution environment
   - Strict file system permissions
   - Limited network access

4. **Runtime Monitoring** (Guardian + Anomaly Detection)
   - Behavioral analysis during execution
   - Anomaly detection for unusual patterns
   - Automatic quarantine on critical threats

5. **Audit Trail** (Guardian Audit Log)
   - Immutable log of all security events
   - Complete decision history
   - Forensic analysis capability

## Configuration

### Enable Security Features

All security features are enabled by default. Configuration in `.env`:

```bash
# Skill Security Scanning
AWESOME_SKILLS_SECURITY_SCANNING=true

# API Key Protection
API_KEY_PROTECTION_ENABLED=true
API_KEY_REDACTION_ENABLED=true

# Guardian Security Layer
GUARDIAN_ENABLED=true
GUARDIAN_INJECTION_THRESHOLD=0.75
GUARDIAN_AUTO_QUARANTINE=true

# Docker Sandbox
SANDBOX_ENABLED=true
SANDBOX_MOUNT_POLICY=restricted
```

### Security Levels

Choose your security posture:

**Paranoid** (Maximum Security):
```bash
AWESOME_SKILLS_ENABLED=false  # Disable all external skills
SANDBOX_MOUNT_POLICY=minimal
GUARDIAN_INJECTION_THRESHOLD=0.5
API_KEY_PROTECTION_ENABLED=true
```

**Balanced** (Recommended):
```bash
AWESOME_SKILLS_ENABLED=true
AWESOME_SKILLS_SECURITY_SCANNING=true
SANDBOX_MOUNT_POLICY=restricted
GUARDIAN_INJECTION_THRESHOLD=0.75
API_KEY_PROTECTION_ENABLED=true
```

**Permissive** (Development Only):
```bash
AWESOME_SKILLS_ENABLED=true
AWESOME_SKILLS_SECURITY_SCANNING=true
SANDBOX_MOUNT_POLICY=permissive
GUARDIAN_INJECTION_THRESHOLD=0.9
# Still enables protection but with higher thresholds
```

## Best Practices

### For Users

1. **API Key Hygiene**
   - ✅ Store keys in `.env` files only
   - ✅ Never paste keys in chat
   - ✅ Rotate keys every 90 days
   - ✅ Use different keys for dev/prod
   - ❌ Don't commit keys to git
   - ❌ Don't share keys in screenshots

2. **Skill Management**
   - ✅ Only load skills from curated repository
   - ✅ Review security scan results
   - ✅ Report suspicious skills
   - ❌ Don't skip security scans
   - ❌ Don't load skills from untrusted sources

3. **System Security**
   - ✅ Keep lollmsBot updated
   - ✅ Review audit logs regularly
   - ✅ Monitor for unusual behavior
   - ✅ Use Docker sandbox when available
   - ❌ Don't run as root
   - ❌ Don't disable security features in production

### For Skill Developers

1. **Skill Development**
   - ✅ Follow principle of least privilege
   - ✅ Declare all external dependencies
   - ✅ Document all file/network operations
   - ✅ Include test cases
   - ❌ Don't obfuscate code
   - ❌ Don't access unnecessary system resources

2. **Security Testing**
   - ✅ Test with skill scanner before submission
   - ✅ Include security documentation
   - ✅ Declare all permissions needed
   - ✅ Provide clear description of behavior
   - ❌ Don't include encoded/obfuscated payloads
   - ❌ Don't attempt security bypasses

## Incident Response

### If You Suspect Compromise

1. **Immediate Actions**
   ```bash
   # Check security audit log
   cat ~/.lollmsbot/audit.log | tail -100
   
   # Review loaded skills
   lollmsbot skills list --loaded
   
   # Check for security events
   lollmsbot security report
   ```

2. **Rotate All Keys**
   - OpenAI API keys
   - Anthropic API keys
   - OpenRouter API keys
   - Any other service keys

3. **Review Changes**
   ```bash
   # Check file modifications
   find ~/.lollmsbot -type f -mtime -7
   
   # Review Docker containers
   docker ps -a
   ```

4. **Report**
   - Open GitHub issue with [SECURITY] tag
   - Include relevant log excerpts (redacted)
   - Describe suspicious behavior
   - Do NOT include actual API keys

### If Skill Fails Security Scan

The skill is automatically blocked. To investigate:

```bash
# Get scan results
lollmsbot skills scan-results <skill-name>

# View detailed threats
lollmsbot skills scan-report <skill-name>

# Report to repository
# (Creates GitHub issue with scan results)
lollmsbot skills report-threat <skill-name>
```

## Security Updates

We actively monitor for new threats and update defenses accordingly:

- **Pattern Updates**: New malicious patterns added regularly
- **Threat Intelligence**: Community-reported issues integrated
- **Security Patches**: Critical fixes released immediately
- **Documentation**: This file updated with new mitigations

## Comparison to OpenClaw Vulnerabilities

| OpenClaw Vulnerability | Our Protection | Status |
|------------------------|----------------|---------|
| Sleeper agents in skills | Skill Scanner with dormancy detection | ✅ Mitigated |
| Data exfiltration | Pattern detection + network monitoring | ✅ Mitigated |
| Container escapes | Docker sandbox + escape detection | ✅ Mitigated |
| API key harvesting | .env scanning prevention + redaction | ✅ Mitigated |
| Unencrypted chat logs | Automatic key redaction | ✅ Mitigated |
| Malicious public skills | Curated repository only | ✅ Mitigated |
| Prompt injection | Enhanced Guardian patterns | ✅ Mitigated |
| macOS Gatekeeper bypass | Pattern detection | ✅ Mitigated |
| Obfuscated payloads | Base64/hex decode detection | ✅ Mitigated |
| Semantic attacks | Text-as-executable awareness | ✅ Mitigated |

## Contact

- **Security Issues**: Open a GitHub issue with `[SECURITY]` tag
- **Private Disclosure**: Email maintainers (see CONTRIBUTING.md)
- **General Questions**: GitHub Discussions

## References

- [OpenClaw Security Analysis Video](https://www.youtube.com/watch?v=ceEUO_i7aW4)
- [Cisco AI Defense Skill Scanner](https://github.com/CiscoAIDefense/skill-scanner)
- [Awesome Claude Skills Repository](https://github.com/Grumpified-OGGVCT/awesome-claude-skills)

---

**Last Updated**: 2026-02-07  
**Version**: 1.0  
**Status**: Active Protection

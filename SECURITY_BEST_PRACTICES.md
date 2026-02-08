# Security Best Practices Guide

## Quick Security Checklist

Before using lollmsBot in any environment:

- [ ] Review and understand `SECURITY.md`
- [ ] Set up `.env` file for API keys (never paste in chat)
- [ ] Enable security scanning for skills
- [ ] Review loaded skills with `lollmsbot skills scan-all`
- [ ] Set appropriate permission levels
- [ ] Enable Docker sandbox if available
- [ ] Review audit logs regularly

## API Key Security

### ✅ DO

1. **Store keys in `.env` file**
   ```bash
   # Create .env file in project root
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   OPENROUTER_API_KEY_1=sk-or-v1-...
   ```

2. **Use environment-specific keys**
   - Different keys for development and production
   - Rotate keys regularly (every 90 days minimum)
   - Revoke old keys after rotation

3. **Monitor key usage**
   ```bash
   # Check for exposed keys
   lollmsbot skills security-report
   ```

4. **Enable key protection**
   ```bash
   # In .env file
   API_KEY_PROTECTION_ENABLED=true
   API_KEY_REDACTION_ENABLED=true
   ```

### ❌ DON'T

1. **Never paste keys in chat**
   - Chat logs are stored unencrypted
   - Skills can access chat history
   - Keys in logs can be exfiltrated

2. **Never commit keys to git**
   ```bash
   # Add to .gitignore
   .env
   .env.*
   ```

3. **Never share keys in screenshots**
   - Redact before sharing
   - Use masked display format

4. **Never hardcode keys in code**
   ```python
   # ❌ BAD
   api_key = "sk-proj-abc123..."
   
   # ✅ GOOD
   api_key = os.getenv("OPENAI_API_KEY")
   ```

## Skill Security

### Before Loading Skills

1. **Scan for threats**
   ```bash
   # Scan specific skill
   lollmsbot skills scan domain-name-brainstormer
   
   # Scan all available skills
   lollmsbot skills scan-all
   ```

2. **Review scan results**
   ```bash
   # View detailed results
   lollmsbot skills scan-results domain-name-brainstormer
   ```

3. **Check skill source**
   - Only use skills from `awesome-claude-skills` repository
   - This is a curated, vetted repository
   - Avoid loading skills from unknown sources

### Skill Security Levels

**Safe Skills (✅)**
- No threats detected
- Passed all security checks
- Safe to load

**Warning Skills (⚠️)**
- Low/Medium severity threats
- Review carefully before loading
- May need manual inspection

**Unsafe Skills (❌)**
- High/Critical severity threats
- Automatically blocked from loading
- Do NOT attempt to load

### Common Threats in Skills

1. **Data Exfiltration**
   - Symptoms: External POST requests, file zipping, network connections
   - Risk: Could steal API keys, personal data
   - Action: Block immediately, report to maintainers

2. **Container Escape**
   - Symptoms: Docker socket access, namespace manipulation
   - Risk: Could break out of sandbox, access host system
   - Action: Block immediately, potential security incident

3. **Sleeper Agents**
   - Symptoms: Trigger words, scheduled execution, dormant code
   - Risk: Could activate malicious behavior later
   - Action: Block immediately, review system for infection

4. **Credential Harvesting**
   - Symptoms: .env file access, environment variable dumps
   - Risk: Could steal all API keys and secrets
   - Action: Block immediately, rotate all keys

## Container Security

### Enable Docker Sandbox

```bash
# In docker-compose.yml or .env
SANDBOX_ENABLED=true
SANDBOX_MOUNT_POLICY=restricted
```

### Sandbox Levels

**Minimal (Maximum Security)**
```bash
SANDBOX_MOUNT_POLICY=minimal
# Only ~/.lollmsbot/workspace
# Read-only by default
```

**Restricted (Recommended)**
```bash
SANDBOX_MOUNT_POLICY=restricted
# Home directory + temp
# Read-only by default
# Blocked: /etc, /sys, /proc, /dev, /var/run/docker.sock
```

**Permissive (Development Only)**
```bash
SANDBOX_MOUNT_POLICY=permissive
# More paths allowed
# Still blocks critical system paths
# Use only in trusted development environment
```

### What's Blocked

The sandbox automatically blocks access to:
- `/var/run/docker.sock` - Container escape vector
- `/etc`, `/sys`, `/proc` - System configuration
- `/dev` - Device access
- `/root` - Root user directory
- System binaries (`/bin`, `/sbin`)
- Kernel modules and system services

## Prompt Injection Protection

### Guardian Layer

The Guardian automatically screens all inputs for:
- Injection attempts ("ignore previous instructions")
- System overrides ("you are now unrestricted")
- Malicious commands ("install prerequisite")
- Security bypasses ("remove quarantine attribute")

### What to Do if Blocked

If legitimate input is blocked:

1. **Review the message**
   - Check for phrases that look like commands
   - Rephrase to be less directive

2. **Check audit log**
   ```bash
   cat ~/.lollmsbot/audit.log | tail -20
   ```

3. **Adjust threshold** (if needed)
   ```bash
   # In .env
   GUARDIAN_INJECTION_THRESHOLD=0.9  # Higher = less sensitive
   ```

4. **Report false positive**
   - Open GitHub issue
   - Include sanitized input example

## Monitoring and Auditing

### Regular Security Checks

Run weekly:
```bash
# Full security report
lollmsbot skills security-report

# Check for keys needing rotation
grep "rotation" ~/.lollmsbot/audit.log

# Review security events
cat ~/.lollmsbot/audit.log | grep -E "CRITICAL|HIGH"
```

### Audit Log Location

- **Main audit log**: `~/.lollmsbot/audit.log`
- **Guardian events**: All security decisions
- **Immutable**: Cannot be modified by skills or system
- **Forensics**: Useful for incident investigation

### What to Look For

**Normal Activity**:
- Skill loading events
- Permission checks (allowed)
- API key detection (redacted)
- Decision logging (info level)

**Suspicious Activity**:
- Multiple blocked permissions
- Rapid successive operations
- Novel tool combinations
- High/Critical threat detections

**Security Incidents**:
- Container escape attempts
- Credential harvesting
- Data exfiltration
- Quarantine activation

## Incident Response

### If You Suspect Compromise

1. **Immediate Actions**
   ```bash
   # Stop all services
   pkill -f lollmsbot
   
   # Review recent activity
   tail -100 ~/.lollmsbot/audit.log
   
   # Check loaded skills
   lollmsbot skills list --loaded
   ```

2. **Rotate ALL Keys**
   - OpenAI
   - Anthropic
   - OpenRouter
   - Any other service keys
   - Do this IMMEDIATELY

3. **Review System**
   ```bash
   # Check for unauthorized files
   find ~/.lollmsbot -type f -mtime -7
   
   # Check Docker containers
   docker ps -a
   
   # Review network connections
   netstat -an | grep ESTABLISHED
   ```

4. **Clean Install**
   ```bash
   # Backup important data
   cp -r ~/.lollmsbot/workspace ~/backup/
   
   # Remove and reinstall
   rm -rf ~/.lollmsbot
   pip uninstall lollmsbot
   pip install lollmsbot
   ```

5. **Report Incident**
   - Open GitHub issue with `[SECURITY]` tag
   - Email maintainers if sensitive
   - Include sanitized logs
   - Describe suspicious behavior

### Recovery Checklist

- [ ] All API keys rotated
- [ ] System wiped and reinstalled
- [ ] Audit logs reviewed
- [ ] Malicious skills identified and removed
- [ ] Incident reported to maintainers
- [ ] Enhanced security settings applied
- [ ] Regular monitoring enabled

## Secure Configuration Examples

### Maximum Security (Paranoid)

```bash
# .env
# API Keys
API_KEY_PROTECTION_ENABLED=true
API_KEY_REDACTION_ENABLED=true

# Skills
AWESOME_SKILLS_ENABLED=false  # No external skills
AWESOME_SKILLS_SECURITY_SCANNING=true

# Sandbox
SANDBOX_ENABLED=true
SANDBOX_MOUNT_POLICY=minimal

# Guardian
GUARDIAN_ENABLED=true
GUARDIAN_INJECTION_THRESHOLD=0.5
GUARDIAN_AUTO_QUARANTINE=true

# Permissions
LOLLMSBOT_DEFAULT_PERMISSION=BASIC
LOLLMSBOT_ENABLE_SHELL=false

# Network
LOLLMSBOT_HOST=127.0.0.1  # Localhost only
```

### Balanced Security (Recommended)

```bash
# .env
# API Keys
API_KEY_PROTECTION_ENABLED=true
API_KEY_REDACTION_ENABLED=true

# Skills
AWESOME_SKILLS_ENABLED=true
AWESOME_SKILLS_SECURITY_SCANNING=true

# Sandbox
SANDBOX_ENABLED=true
SANDBOX_MOUNT_POLICY=restricted

# Guardian
GUARDIAN_ENABLED=true
GUARDIAN_INJECTION_THRESHOLD=0.75
GUARDIAN_AUTO_QUARANTINE=true

# Permissions
LOLLMSBOT_DEFAULT_PERMISSION=BASIC
LOLLMSBOT_ENABLE_SHELL=false

# Network
LOLLMSBOT_HOST=127.0.0.1
```

### Development (Permissive)

```bash
# .env
# API Keys
API_KEY_PROTECTION_ENABLED=true
API_KEY_REDACTION_ENABLED=true

# Skills
AWESOME_SKILLS_ENABLED=true
AWESOME_SKILLS_SECURITY_SCANNING=true  # Still enabled!

# Sandbox
SANDBOX_ENABLED=true
SANDBOX_MOUNT_POLICY=permissive

# Guardian
GUARDIAN_ENABLED=true
GUARDIAN_INJECTION_THRESHOLD=0.85
GUARDIAN_AUTO_QUARANTINE=false

# Permissions
LOLLMSBOT_DEFAULT_PERMISSION=TOOLS
LOLLMSBOT_ENABLE_SHELL=false  # Still false!

# Network
LOLLMSBOT_HOST=127.0.0.1
```

## Additional Resources

- **Security Architecture**: See `SECURITY.md`
- **Threat Model**: See `SECURITY.md` > Threat Model
- **OpenClaw Analysis**: [Video](https://www.youtube.com/watch?v=ceEUO_i7aW4)
- **Cisco Skill Scanner**: [GitHub](https://github.com/CiscoAIDefense/skill-scanner)
- **Report Issues**: [GitHub Issues](https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied/issues)

## Security Updates

Subscribe to security updates:
- Watch the GitHub repository
- Enable notifications for `[SECURITY]` tagged issues
- Review release notes for security patches
- Join Discord for announcements

---

**Remember**: Security is a process, not a destination. Stay vigilant, review regularly, and report suspicious behavior.

**When in doubt, err on the side of caution.**

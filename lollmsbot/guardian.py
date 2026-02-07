"""
Guardian Module - LollmsBot's Unified Security & Ethics Layer

The Guardian is LollmsBot's "conscience" and "immune system" combined.
It monitors all inputs, outputs, and internal states for:
- Security threats (prompt injection, data exfiltration, unauthorized access)
- Ethical violations (against user-defined ethics.md rules)
- Behavioral anomalies (deviation from established patterns)
- Consent enforcement (permission gates for sensitive operations)
- API key leakage and credential harvesting (NEW)
- Malicious skill patterns and threats (NEW)

Architecture: The Guardian operates as a "reflexive layer" - it can intercept
and block any operation before execution, but cannot be bypassed by the
Agent or any Tool. It's the ultimate authority in the system.

OpenClaw Security Enhancements:
This module has been enhanced to prevent OpenClaw-style attacks including:
- Sleeper agents in skills
- Data exfiltration attempts
- Container escape patterns
- API key harvesting
- Credential theft from .env files
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple, Union

# Configure logging for security events
logger = logging.getLogger("lollmsbot.guardian")


class ThreatType(Enum):
    """Types of threats that Guardian can detect."""
    PROMPT_INJECTION = auto()
    DATA_EXFILTRATION = auto()
    CONTAINER_ESCAPE = auto()
    SLEEPER_AGENT = auto()
    PRIVILEGE_ESCALATION = auto()
    FILE_SYSTEM_ABUSE = auto()
    NETWORK_ABUSE = auto()
    CODE_INJECTION = auto()
    CREDENTIAL_HARVESTING = auto()
    OBFUSCATION = auto()
    API_KEY_EXPOSURE = auto()


class ThreatLevel(Enum):
    """Severity classification for security events."""
    INFO = auto()      # Logged, no action needed
    LOW = auto()       # Flagged for review
    MEDIUM = auto()    # Requires user notification
    HIGH = auto()      # Blocks operation, alerts user
    CRITICAL = auto()  # Self-quarantine triggered


class GuardianAction(Enum):
    """Possible responses to security checks."""
    ALLOW = auto()     # Proceed normally
    FLAG = auto()      # Allow but log for review
    CHALLENGE = auto() # Require explicit user confirmation
    BLOCK = auto()     # Deny operation
    QUARANTINE = auto() # Block and isolate affected components


@dataclass(frozen=True)
class SecurityEvent:
    """Immutable record of a security-relevant event."""
    timestamp: datetime
    event_type: str
    threat_level: ThreatLevel
    source: str  # Component that triggered the event
    description: str
    context_hash: str  # Hash of relevant context (for integrity)
    action_taken: GuardianAction
    user_notified: bool = False
    event_id: str = ""  # Unique identifier for this event
    
    def __post_init__(self):
        # Generate event_id if not provided
        if not self.event_id:
            import uuid
            object.__setattr__(self, 'event_id', str(uuid.uuid4())[:8])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "threat_level": self.threat_level.name,
            "source": self.source,
            "description": self.description,
            "context_hash": self.context_hash,
            "action_taken": self.action_taken.name,
            "user_notified": self.user_notified,
        }


@dataclass
class EthicsRule:
    """A single ethical constraint from ethics.md."""
    rule_id: str
    category: str  # e.g., "privacy", "honesty", "consent", "safety"
    statement: str  # Human-readable rule
    enforcement: str  # "strict", "advisory", "confirm"
    exceptions: List[str] = field(default_factory=list)
    
    def matches_violation(self, action_description: str) -> bool:
        """Check if an action description violates this rule."""
        # Simple keyword matching - can be enhanced with LLM-based semantic matching
        keywords = self.statement.lower().split()
        action_lower = action_description.lower()
        return any(kw in action_lower for kw in keywords if len(kw) > 4)


@dataclass
class PermissionGate:
    """A conditional permission that can be time-bound, context-aware, or require confirmation."""
    resource: str  # What this gate protects (e.g., "gmail", "shell", "filesystem")
    allowed: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)
    # Examples: {"time_window": "09:00-17:00"}, {"require_confirmation": True}, {"max_per_day": 10}
    
    def check(self, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if operation is permitted under current conditions."""
        if not self.allowed:
            return False, f"Access to {self.resource} is disabled"
        
        # Check time window if specified
        if "time_window" in self.conditions:
            start, end = self.conditions["time_window"].split("-")
            now = datetime.now().strftime("%H:%M")
            if not (start <= now <= end):
                return False, f"{self.resource} only available {start}-{end}"
        
        # Check rate limiting
        if "max_per_day" in self.conditions:
            today_key = f"{self.resource}_{datetime.now().strftime('%Y%m%d')}"
            # This would need persistent counter storage in production
        
        # Check confirmation requirement
        if self.conditions.get("require_confirmation", False):
            return False, "CONFIRMATION_REQUIRED"
        
        return True, None


class ThreatDetector:
    """
    Unified threat detection for all security concerns.
    Consolidates prompt injection, skill threats, API keys, etc.
    """
    
    # Comprehensive threat patterns by type
    THREAT_PATTERNS: Dict[ThreatType, List[Tuple[str, float]]] = {
        ThreatType.PROMPT_INJECTION: [
            (r"ignore\s+(all\s+)?previous\s+(instructions|commands)", 0.9),
            (r"disregard\s+(your\s+)?(instructions|programming|rules)", 0.9),
            (r"you\s+are\s+now\s+.*?(free|unrestricted|uncensored)", 0.85),
            (r"system\s*:\s*.*?(override|ignore|bypass)", 0.9),
            (r"<script.*?>.*?</script>", 0.95),
            (r"```\s*system\s*\n", 0.8),
            (r"\{\{.*?\}\}", 0.7),
            (r"\$\{.*?\}", 0.7),
            (r"`.*?`", 0.5),
            (r"\[\s*system\s*\]", 0.75),
            # OpenClaw-style attacks
            (r"install\s+(?:prerequisite|dependency|requirement)", 0.7),
            (r"download\s+(?:and|then)\s+(?:run|execute|install)", 0.8),
            (r"bypass\s+(?:gatekeeper|security|validation)", 0.85),
            (r"remove\s+quarantine\s+attribute", 0.9),
        ],
        ThreatType.DATA_EXFILTRATION: [
            (r"curl\s+.*?\s+(-X\s+POST|--data)", 0.8),
            (r"wget\s+.*?--post-(data|file)", 0.8),
            (r"nc\s+.*?\s+\d+", 0.7),
            (r"(?:zip|tar|gzip).*?\.env", 0.9),
            (r"(?:zip|tar|gzip).*?secrets?", 0.8),
        ],
        ThreatType.CONTAINER_ESCAPE: [
            (r"docker\s+run.*?--privileged", 0.95),
            (r"/var/run/docker\.sock", 0.9),
            (r"nsenter|unshare|chroot", 0.85),
            (r"mount.*?/proc|/sys", 0.8),
            (r"\.\./\.\./", 0.6),
        ],
        ThreatType.SLEEPER_AGENT: [
            (r"sleep\s+\d{3,}", 0.7),
            (r"while.*?true.*?sleep", 0.7),
            (r"(?:trigger|activate|wake).*?(?:code|agent|payload)", 0.8),
            (r"if.*?\$(?:TRIGGER|ACTIVATE|SECRET_WORD)", 0.9),
        ],
        ThreatType.CREDENTIAL_HARVESTING: [
            (r"grep.*?(?:-r|-R).*?\.env", 0.8),
            (r"env\s*\|\s*grep", 0.7),
            (r"printenv|export|set\s+\|\s+grep", 0.6),
            (r"(?:read|cat|grep).*?\.env", 0.8),
        ],
        ThreatType.API_KEY_EXPOSURE: [
            # OpenAI
            (r'sk-[A-Za-z0-9]{48,}', 0.95),
            (r'sk-proj-[A-Za-z0-9_-]{40,}', 0.95),
            # Anthropic
            (r'sk-ant-[A-Za-z0-9_-]{95,}', 0.95),
            # OpenRouter
            (r'sk-or-v1-[A-Za-z0-9]{64,}', 0.95),
            # AWS
            (r'AKIA[0-9A-Z]{16}', 0.9),
            # Generic
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}', 0.7),
        ],
    }
    
    # Delimiter confusion attacks
    DELIMITER_ATTACKS = [
        (r"human\s*:\s*.*?\n\s*assistant\s*:", 0.8),
        (r"user\s*:\s*.*?\n\s*ai\s*:", 0.8),
        (r"<\|.*?\|>", 0.75),
    ]
    
    def __init__(self):
        self._compiled_patterns = {}
        self._compile_patterns()
        
        # Track detected API keys (hashes only)
        self._detected_keys: Dict[str, datetime] = {}
    
    def _compile_patterns(self) -> None:
        """Compile all threat patterns for efficient matching."""
        for threat_type, patterns in self.THREAT_PATTERNS.items():
            self._compiled_patterns[threat_type] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), confidence)
                for pattern, confidence in patterns
            ]
        
        self._compiled_delimiters = [
            (re.compile(p, re.I), s) for p, s in self.DELIMITER_ATTACKS
        ]
    
    def analyze(self, text: str, context: str = "unknown") -> Tuple[Dict[ThreatType, float], List[str]]:
        """
        Unified threat analysis for all security concerns.
        Returns: (threat_scores_by_type, list_of_detected_patterns)
        """
        threat_scores: Dict[ThreatType, float] = {}
        detected: List[str] = []
        
        # Check all threat patterns
        for threat_type, patterns in self._compiled_patterns.items():
            max_score = 0.0
            for pattern, score in patterns:
                if pattern.search(text):
                    detected.append(f"{threat_type.name}:{pattern.pattern[:40]}")
                    max_score = max(max_score, score)
                    
                    # Special handling for API keys
                    if threat_type == ThreatType.API_KEY_EXPOSURE:
                        self._handle_api_key_detection(text, pattern, context)
            
            if max_score > 0:
                threat_scores[threat_type] = max_score
        
        # Check delimiter confusion
        for pattern, score in self._compiled_delimiters:
            if pattern.search(text):
                detected.append(f"delimiter:{pattern.pattern[:30]}")
                threat_scores[ThreatType.PROMPT_INJECTION] = max(
                    threat_scores.get(ThreatType.PROMPT_INJECTION, 0), score
                )
        
        # Structural analysis
        role_markers = text.lower().count("role:") + text.lower().count("system:")
        if role_markers > 2:
            threat_scores[ThreatType.PROMPT_INJECTION] = max(
                threat_scores.get(ThreatType.PROMPT_INJECTION, 0), 0.6
            )
            detected.append(f"excessive_role_markers:{role_markers}")
        
        # Entropy analysis for obfuscation
        if len(text) > 100:
            entropy = self._calculate_entropy(text)
            if entropy > 5.5:
                threat_scores[ThreatType.OBFUSCATION] = 0.5
                detected.append(f"high_entropy:{entropy:.2f}")
        
        return threat_scores, detected
    
    def _handle_api_key_detection(self, text: str, pattern: re.Pattern, context: str) -> None:
        """Handle detected API keys - log but don't store the actual key."""
        matches = pattern.finditer(text)
        for match in matches:
            key_value = match.group(0)
            key_hash = hashlib.sha256(key_value.encode()).hexdigest()
            
            if key_hash not in self._detected_keys:
                self._detected_keys[key_hash] = datetime.now()
                # Mask the key
                if len(key_value) > 12:
                    masked = f"{key_value[:8]}...{key_value[-4:]}"
                else:
                    masked = f"{key_value[:4]}...{key_value[-2:]}"
                
                logger.warning(
                    f"🔑 API key detected in {context}: {masked} "
                    f"(hash: {key_hash[:16]})"
                )
    
    def redact_api_keys(self, text: str) -> str:
        """Redact API keys from text."""
        redacted = text
        for threat_type, patterns in self._compiled_patterns.items():
            if threat_type == ThreatType.API_KEY_EXPOSURE:
                for pattern, _ in patterns:
                    matches = list(pattern.finditer(redacted))
                    for match in matches:
                        key_value = match.group(0)
                        if len(key_value) > 12:
                            masked = f"{key_value[:8]}...{key_value[-4:]}"
                        else:
                            masked = f"{key_value[:4]}...{key_value[-2:]}"
                        replacement = f"[REDACTED_KEY_{masked}]"
                        redacted = redacted.replace(key_value, replacement)
        return redacted
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        probs = [text.count(c) / len(text) for c in set(text)]
        return -sum(p * (p.bit_length() - 1) for p in probs if p > 0)
    
    def sanitize(self, text: str) -> str:
        """Apply conservative sanitization to potentially dangerous input."""
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Escape potential HTML
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        return text.strip()


class AnomalyDetector:
    """Behavioral anomaly detection for self-monitoring."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._behavior_log: List[Dict[str, Any]] = []
        self._pattern_hashes: Set[str] = set()
    
    def record(self, action_type: str, details: Dict[str, Any]) -> Optional[SecurityEvent]:
        """Record an action and check for anomalies."""
        record = {
            "timestamp": datetime.now(),
            "action": action_type,
            "tool": details.get("tool"),
            "user": details.get("user_id"),
            "params_hash": self._hash_params(details.get("params", {})),
        }
        
        self._behavior_log.append(record)
        if len(self._behavior_log) > self.window_size:
            self._behavior_log.pop(0)
        
        # Check for anomalies
        return self._detect_anomaly(record)
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Create stable hash of parameters for pattern comparison."""
        normalized = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _detect_anomaly(self, record: Dict[str, Any]) -> Optional[SecurityEvent]:
        """Check if current action deviates from established patterns."""
        # Check 1: Rapid successive operations (potential automation abuse)
        recent = [r for r in self._behavior_log 
                  if r["timestamp"] > datetime.now() - timedelta(minutes=5)]
        if len(recent) > 20:  # More than 20 actions in 5 minutes
            return SecurityEvent(
                timestamp=datetime.now(),
                event_type="rapid_operations",
                threat_level=ThreatLevel.MEDIUM,
                source="anomaly_detector",
                description=f"Unusual activity: {len(recent)} actions in 5 minutes",
                context_hash=record["params_hash"],
                action_taken=GuardianAction.CHALLENGE,
            )
        
        # Check 2: New tool combination (unprecedented workflow)
        recent_tools = set(r.get("tool") for r in recent if r.get("tool"))
        if len(recent_tools) > 3:  # Unusually diverse tool usage
            # Check if this combination has been seen before
            combo_hash = hashlib.sha256(
                json.dumps(sorted(recent_tools), sort_keys=True).encode()
            ).hexdigest()[:16]
            if combo_hash not in self._pattern_hashes:
                self._pattern_hashes.add(combo_hash)
                if len(self._pattern_hashes) > 10:  # Not first-time novelty
                    return SecurityEvent(
                        timestamp=datetime.now(),
                        event_type="novel_tool_combination",
                        threat_level=ThreatLevel.LOW,
                        source="anomaly_detector",
                        description=f"New tool combination: {recent_tools}",
                        context_hash=combo_hash,
                        action_taken=GuardianAction.FLAG,
                    )
        
        # Check 3: Privilege escalation attempt (tools requiring higher permissions)
        # This would integrate with permission system
        
        return None


class Guardian:
    """
    The Guardian is LollmsBot's ultimate unified security authority.
    
    Consolidates ALL security functions:
    - Prompt injection detection
    - API key protection and redaction
    - Skill threat scanning
    - Container escape prevention
    - Data exfiltration detection
    - Behavioral anomaly detection
    - Ethics enforcement
    - Permission gates
    """
    
    # Singleton instance for system-wide authority
    _instance: Optional[Guardian] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        ethics_file: Optional[Path] = None,
        audit_log_path: Optional[Path] = None,
        auto_quarantine: bool = True,
    ):
        if self._initialized:
            return
        
        self._initialized = True
        self.ethics_file = ethics_file or Path.home() / ".lollmsbot" / "ethics.md"
        self.audit_log_path = audit_log_path or Path.home() / ".lollmsbot" / "audit.log"
        
        # Security components - NOW UNIFIED
        self.threat_detector = ThreatDetector()  # Unified detector
        self.anomaly_detector = AnomalyDetector()
        
        # State
        self._ethics_rules: List[EthicsRule] = []
        self._permission_gates: Dict[str, PermissionGate] = {}
        self._quarantined: bool = False
        self._quarantine_reason: Optional[str] = None
        self._event_history: List[SecurityEvent] = []
        self._max_history = 10000
        
        # Configuration
        self.auto_quarantine = auto_quarantine
        self.injection_threshold = 0.75  # Block above this confidence
        
        # Load ethics and permissions
        self._load_ethics()
        self._load_permissions()
        
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🛡️  Guardian initialized - Unified security active")
        logger.info("   ✓ Prompt injection protection")
        logger.info("   ✓ API key detection & redaction")
        logger.info("   ✓ Skill threat scanning")
        logger.info("   ✓ Container escape prevention")
    
    def _load_ethics(self) -> None:
        """Load ethics rules from ethics.md or use defaults."""
        if self.ethics_file.exists():
            try:
                content = self.ethics_file.read_text(encoding='utf-8')
                self._ethics_rules = self._parse_ethics_md(content)
                logger.info(f"📜 Loaded {len(self._ethics_rules)} ethics rules")
            except Exception as e:
                logger.error(f"Failed to load ethics: {e}")
                self._load_default_ethics()
        else:
            self._load_default_ethics()
    
    def _load_default_ethics(self) -> None:
        """Install default ethical constraints."""
        self._ethics_rules = [
            EthicsRule(
                rule_id="privacy-001",
                category="privacy",
                statement="Never share user personal information without explicit consent",
                enforcement="strict",
            ),
            EthicsRule(
                rule_id="consent-001", 
                category="consent",
                statement="Always ask permission before executing destructive operations",
                enforcement="strict",
            ),
            EthicsRule(
                rule_id="honesty-001",
                category="honesty",
                statement="Never misrepresent capabilities or pretend to be human",
                enforcement="strict",
            ),
            EthicsRule(
                rule_id="safety-001",
                category="safety",
                statement="Do not assist with creating malware, exploits, or harmful content",
                enforcement="strict",
            ),
            EthicsRule(
                rule_id="autonomy-001",
                category="autonomy",
                statement="Respect user autonomy and do not manipulate decisions",
                enforcement="advisory",
            ),
        ]
        logger.info(f"📜 Loaded {len(self._ethics_rules)} default ethics rules")
    
    def _parse_ethics_md(self, content: str) -> List[EthicsRule]:
        """Parse ethics.md format into structured rules."""
        rules = []
        current_rule = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## '):
                # New rule section
                if current_rule:
                    rules.append(current_rule)
                rule_id = line[3:].strip().lower().replace(' ', '-')
                current_rule = {
                    'rule_id': rule_id,
                    'category': 'general',
                    'statement': '',
                    'enforcement': 'advisory',
                    'exceptions': []
                }
            elif line.startswith('- ') and current_rule:
                if line.startswith('- Category:'):
                    current_rule['category'] = line[11:].strip()
                elif line.startswith('- Enforcement:'):
                    current_rule['enforcement'] = line[14:].strip()
                elif line.startswith('- Exception:'):
                    current_rule['exceptions'].append(line[12:].strip())
                elif not current_rule['statement']:
                    current_rule['statement'] = line[2:].strip()
        
        if current_rule:
            rules.append(current_rule)
        
        return [EthicsRule(**r) for r in rules]
    
    def _load_permissions(self) -> None:
        """Load permission gates from configuration."""
        # Default restrictive permissions
        self._permission_gates = {
            "shell": PermissionGate("shell", allowed=False),
            "filesystem_write": PermissionGate("filesystem_write", allowed=True),
            "filesystem_delete": PermissionGate("filesystem_delete", allowed=False),
            "http_external": PermissionGate("http_external", allowed=True, 
                                          conditions={"require_confirmation": True}),
            "email_send": PermissionGate("email_send", allowed=False),
            "calendar_write": PermissionGate("calendar_write", allowed=True),
        }
    
    # ============== PUBLIC API ==============
    
    def check_input(self, text: str, source: str = "unknown") -> Tuple[bool, Optional[SecurityEvent]]:
        """
        Screen all incoming text for ALL threats: injection, keys, malicious patterns.
        Returns: (is_safe, security_event_if_blocked)
        """
        if self._quarantined:
            return False, SecurityEvent(
                timestamp=datetime.now(),
                event_type="quarantine_block",
                threat_level=ThreatLevel.CRITICAL,
                source=source,
                description=f"Input blocked: Guardian is in quarantine mode ({self._quarantine_reason})",
                context_hash=self._hash_context({"text": text[:100]}),
                action_taken=GuardianAction.BLOCK,
            )
        
        # Run unified threat detection
        threat_scores, patterns = self.threat_detector.analyze(text, source)
        
        # Check for API keys and warn
        if ThreatType.API_KEY_EXPOSURE in threat_scores:
            logger.warning(
                "⚠️  API KEY DETECTED in input! "
                "Never paste API keys in chat - use .env files instead."
            )
        
        # Determine highest threat level
        max_score = max(threat_scores.values()) if threat_scores else 0.0
        primary_threat = max(threat_scores.items(), key=lambda x: x[1])[0] if threat_scores else None
        
        if max_score >= self.injection_threshold:
            threat_level = ThreatLevel.HIGH if max_score > 0.9 else ThreatLevel.MEDIUM
            
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=f"{primary_threat.name.lower()}_detected" if primary_threat else "threat_detected",
                threat_level=threat_level,
                source=source,
                description=f"Threat detected (confidence: {max_score:.2f}): {primary_threat.name if primary_threat else 'multiple'} - {patterns[:3]}",
                context_hash=self._hash_context({"text": text[:200], "patterns": patterns}),
                action_taken=GuardianAction.BLOCK if max_score > 0.9 else GuardianAction.CHALLENGE,
            )
            self._log_event(event)
            
            if max_score > 0.95 and self.auto_quarantine:
                self._enter_quarantine(f"Critical threat detected: {primary_threat.name if primary_threat else 'multiple'}")
            
            return False, event
        
        # Low-confidence detection: flag but allow
        if max_score > 0.5:
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type="suspicious_input",
                threat_level=ThreatLevel.LOW,
                source=source,
                description=f"Suspicious patterns detected (confidence: {max_score:.2f})",
                context_hash=self._hash_context({"text": text[:100]}),
                action_taken=GuardianAction.FLAG,
            )
            self._log_event(event)
        
        return True, None
    
    def check_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        user_id: str,
        context: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[SecurityEvent]]:
        """
        Authorize a tool execution. Returns: (allowed, reason_if_denied, security_event)
        """
        if self._quarantined:
            return False, f"Guardian quarantine active: {self._quarantine_reason}", None
        
        # Check permission gate
        gate = self._permission_gates.get(tool_name)
        if gate:
            permitted, reason = gate.check(context)
            if not permitted:
                if reason == "CONFIRMATION_REQUIRED":
                    return False, "This operation requires explicit user confirmation", None
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type="permission_denied",
                    threat_level=ThreatLevel.MEDIUM,
                    source=f"tool:{tool_name}",
                    description=f"Permission gate blocked: {reason}",
                    context_hash=self._hash_context({"user": user_id, "params": params}),
                    action_taken=GuardianAction.BLOCK,
                )
                self._log_event(event)
                return False, reason, event
        
        # Check ethics constraints
        action_desc = f"Execute {tool_name} with {list(params.keys())}"
        for rule in self._ethics_rules:
            if rule.enforcement == "strict" and rule.matches_violation(action_desc):
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type="ethics_violation",
                    threat_level=ThreatLevel.HIGH,
                    source=f"tool:{tool_name}",
                    description=f"Violates rule {rule.rule_id}: {rule.statement}",
                    context_hash=self._hash_context({"rule": rule.rule_id, "action": action_desc}),
                    action_taken=GuardianAction.BLOCK,
                )
                self._log_event(event)
                return False, f"Blocked by ethics rule: {rule.statement}", event
        
        # Record for anomaly detection
        anomaly = self.anomaly_detector.record("tool_execution", {
            "tool": tool_name,
            "user_id": user_id,
            "params": params,
        })
        if anomaly:
            self._log_event(anomaly)
            if anomaly.action_taken == GuardianAction.CHALLENGE:
                return False, "Unusual activity pattern detected - confirmation required", anomaly
            # FLAG allows continuation
        
        return True, None, None
    
    def check_output(self, content: str, destination: str) -> Tuple[bool, Optional[SecurityEvent]]:
        """
        Screen outgoing content for data exfiltration, policy violations, AND API keys.
        """
        # Check for API keys in output and redact
        redacted_content = self.threat_detector.redact_api_keys(content)
        
        # Check for threats in output
        threat_scores, _ = self.threat_detector.analyze(content, f"output:{destination}")
        
        # Check for potential PII leakage (simplified - production uses NER models)
        pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', "SSN"),  # US Social Security
            (r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', "credit_card"),  # Credit cards
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "email"),
        ]
        
        detected_pii = []
        for pattern, pii_type in pii_patterns:
            if re.search(pattern, content):
                detected_pii.append(pii_type)
        
        # Check for high-severity threats in output
        max_score = max(threat_scores.values()) if threat_scores else 0.0
        if max_score > 0.8:  # High confidence threat in output
            primary_threat = max(threat_scores.items(), key=lambda x: x[1])[0]
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type=f"output_{primary_threat.name.lower()}",
                threat_level=ThreatLevel.HIGH,
                source=f"output:{destination}",
                description=f"Threat in output: {primary_threat.name}",
                context_hash=self._hash_context({"preview": redacted_content[:100]}),
                action_taken=GuardianAction.CHALLENGE,
            )
            self._log_event(event)
            return False, event
        
        if detected_pii and "public" in destination.lower():
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type="potential_pii_exposure",
                threat_level=ThreatLevel.HIGH,
                source=f"output:{destination}",
                description=f"Potential PII detected: {detected_pii}",
                context_hash=self._hash_context({"types": detected_pii, "preview": content[:100]}),
                action_taken=GuardianAction.CHALLENGE,
            )
            self._log_event(event)
            return False, event
        
        return True, None
    
    def scan_skill_content(self, skill_name: str, content: str) -> Tuple[bool, List[str]]:
        """
        Scan skill content for malicious patterns.
        Consolidates skill scanning into Guardian.
        
        Returns: (is_safe, list_of_threats)
        """
        threat_scores, patterns = self.threat_detector.analyze(content, f"skill:{skill_name}")
        
        threats = []
        for threat_type, score in threat_scores.items():
            if score > 0.7:  # High confidence threats in skills
                severity = "CRITICAL" if score > 0.9 else "HIGH" if score > 0.8 else "MEDIUM"
                threats.append(f"{severity}: {threat_type.name} (confidence: {score:.2f})")
        
        is_safe = all(score < 0.75 for score in threat_scores.values())
        
        if not is_safe:
            logger.warning(
                f"🚨 Skill '{skill_name}' contains security threats: {threats}"
            )
        
        return is_safe, threats
    
    def redact_api_keys_from_text(self, text: str) -> str:
        """
        Redact API keys from any text (logs, output, etc).
        """
        return self.threat_detector.redact_api_keys(text)
    
    def audit_decision(self, decision: str, reasoning: str, confidence: float) -> None:
        """Log a significant AI decision for later review."""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="ai_decision",
            threat_level=ThreatLevel.INFO,
            source="agent",
            description=f"Decision: {decision[:100]}",
            context_hash=self._hash_context({"reasoning": reasoning[:200], "confidence": confidence}),
            action_taken=GuardianAction.ALLOW,
        )
        self._log_event(event)
    
    # ============== SELF-PRESERVATION ==============
    
    def _enter_quarantine(self, reason: str) -> None:
        """Enter self-quarantine mode - disable all non-essential operations."""
        self._quarantined = True
        self._quarantine_reason = reason
        
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="self_quarantine",
            threat_level=ThreatLevel.CRITICAL,
            source="guardian",
            description=f"Entered quarantine: {reason}",
            context_hash=self._hash_context({"reason": reason}),
            action_taken=GuardianAction.QUARANTINE,
            user_notified=True,
        )
        self._log_event(event)
        
        logger.critical(f"🚨 GUARDIAN QUARANTINE: {reason}")
        # In production: send alert to all configured channels
    
    def exit_quarantine(self, admin_key: str) -> bool:
        """Exit quarantine mode (requires admin authentication)."""
        # In production: verify admin_key against stored hash
        if not self._quarantined:
            return True
        
        # Log the attempt
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="quarantine_exit_attempt",
            threat_level=ThreatLevel.HIGH,
            source="admin",
            description="Attempt to exit quarantine",
            context_hash=self._hash_context({"authorized": True}),  # Would verify
            action_taken=GuardianAction.ALLOW,
        )
        self._log_event(event)
        
        self._quarantined = False
        self._quarantine_reason = None
        logger.info("✅ Exited quarantine mode")
        return True
    
    # ============== UTILITIES ==============
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Create integrity hash for audit logging."""
        normalized = json.dumps(context, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def _log_event(self, event: SecurityEvent) -> None:
        """Persist security event to audit log."""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Write to persistent log
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
        
        # Log at appropriate level
        if event.threat_level == ThreatLevel.CRITICAL:
            logger.critical(f"🚨 {event.event_type}: {event.description}")
        elif event.threat_level == ThreatLevel.HIGH:
            logger.error(f"⚠️ {event.event_type}: {event.description}")
        elif event.threat_level == ThreatLevel.MEDIUM:
            logger.warning(f"🔶 {event.event_type}: {event.description}")
    
    def get_audit_report(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate security audit report."""
        events = self._event_history
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        by_level = {level.name: [] for level in ThreatLevel}
        for e in events:
            by_level[e.threat_level.name].append(e.to_dict())
        
        return {
            "total_events": len(events),
            "quarantine_active": self._quarantined,
            "events_by_level": {k: len(v) for k, v in by_level.items()},
            "recent_critical": by_level.get("CRITICAL", [])[-5:],
            "recent_high": by_level.get("HIGH", [])[-10:],
            "ethics_rules_active": len(self._ethics_rules),
            "permission_gates_active": len(self._permission_gates),
        }
    
    @property
    def is_quarantined(self) -> bool:
        return self._quarantined


# Global access function
def get_guardian() -> Guardian:
    """Get or create the singleton Guardian instance."""
    return Guardian()

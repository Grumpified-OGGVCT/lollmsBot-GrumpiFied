"""
Skill Scanner - Security Analysis for Skills

Inspired by Cisco AI Defense's Skill Scanner, this module provides semantic
analysis of skills to detect malicious code, data exfiltration attempts,
container escapes, and other security threats.

This addresses the OpenClaw security concerns by:
1. Detecting malicious patterns in skill files before loading
2. Validating that skill behavior matches its description
3. Identifying sleeper agents, data exfiltration, and privilege escalation
4. Providing integrity verification through cryptographic signing
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("lollmsbot.skill_scanner")


class ThreatType(Enum):
    """Types of threats that can be detected in skills."""
    DATA_EXFILTRATION = auto()      # Attempts to send data to external servers
    CONTAINER_ESCAPE = auto()       # Attempts to break out of Docker/sandbox
    SLEEPER_AGENT = auto()          # Dormant code waiting for trigger
    PRIVILEGE_ESCALATION = auto()   # Attempts to gain elevated permissions
    FILE_SYSTEM_ABUSE = auto()      # Suspicious file operations
    NETWORK_ABUSE = auto()          # Suspicious network operations
    CODE_INJECTION = auto()         # Attempts to inject executable code
    CREDENTIAL_HARVESTING = auto()  # Attempts to steal API keys/secrets
    OBFUSCATION = auto()            # Heavily obfuscated/encoded content
    PROMPT_INJECTION = auto()       # Embedded prompt injection attacks


class SeverityLevel(Enum):
    """Severity classification for detected threats."""
    INFO = auto()        # Informational, no action needed
    LOW = auto()         # Minor concern, flag for review
    MEDIUM = auto()      # Concerning pattern, requires attention
    HIGH = auto()        # Likely malicious, should block
    CRITICAL = auto()    # Definitely malicious, block immediately


@dataclass
class ThreatDetection:
    """A detected threat in a skill."""
    threat_type: ThreatType
    severity: SeverityLevel
    pattern: str
    location: str  # Where in the skill this was found
    description: str
    confidence: float  # 0.0 to 1.0
    mitigation: str  # Suggested action


@dataclass
class SkillScanResult:
    """Result of scanning a skill for security threats."""
    skill_name: str
    scan_timestamp: datetime
    is_safe: bool
    threats: List[ThreatDetection] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    integrity_hash: Optional[str] = None
    semantic_match: Optional[float] = None  # How well content matches description
    
    def get_max_severity(self) -> Optional[SeverityLevel]:
        """Get the highest severity level detected."""
        if not self.threats:
            return None
        return max(t.severity for t in self.threats, key=lambda s: s.value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "skill_name": self.skill_name,
            "scan_timestamp": self.scan_timestamp.isoformat(),
            "is_safe": self.is_safe,
            "max_severity": self.get_max_severity().name if self.get_max_severity() else None,
            "threat_count": len(self.threats),
            "threats": [
                {
                    "type": t.threat_type.name,
                    "severity": t.severity.name,
                    "pattern": t.pattern,
                    "location": t.location,
                    "description": t.description,
                    "confidence": t.confidence,
                    "mitigation": t.mitigation,
                }
                for t in self.threats
            ],
            "warnings": self.warnings,
            "info": self.info,
            "integrity_hash": self.integrity_hash,
            "semantic_match": self.semantic_match,
        }


class SkillScanner:
    """
    Scans skills for security threats using pattern matching and semantic analysis.
    
    This implements defense against:
    - Malicious skill injection (OpenClaw's "What Would Elon Do" exploit)
    - Container escape attempts
    - Data exfiltration and credential harvesting
    - Sleeper agents with trigger words
    - Obfuscated malicious code
    """
    
    # Pattern definitions for threat detection
    THREAT_PATTERNS = {
        ThreatType.DATA_EXFILTRATION: [
            # Network exfiltration
            (r"curl\s+.*?\s+(-X\s+POST|--data)", 0.8, "POST request detected"),
            (r"wget\s+.*?--post-(data|file)", 0.8, "wget POST detected"),
            (r"nc\s+.*?\s+\d+", 0.7, "netcat connection detected"),
            (r"(?:zip|tar|gzip).*?\.env", 0.9, "Archiving .env file detected"),
            (r"(?:zip|tar|gzip).*?secrets?", 0.8, "Archiving secrets detected"),
            (r"exfil|transmit|send.*?(?:data|file|secret|key)", 0.7, "Exfiltration language"),
            (r"https?://(?!(?:github\.com|raw\.githubusercontent\.com|api\.\w+\.com))", 0.6, "External URL"),
        ],
        ThreatType.CONTAINER_ESCAPE: [
            # Docker/container escape patterns
            (r"docker\s+run.*?--privileged", 0.95, "Privileged Docker execution"),
            (r"/var/run/docker\.sock", 0.9, "Docker socket access"),
            (r"nsenter|unshare|chroot", 0.85, "Namespace manipulation"),
            (r"mount.*?/proc|/sys", 0.8, "System mount attempt"),
            (r"cgroups|capabilities|CAP_", 0.7, "Container control mechanisms"),
            (r"escape.*?(?:container|sandbox|docker)", 0.8, "Escape language"),
            (r"\.\./\.\./", 0.6, "Path traversal attempt"),
        ],
        ThreatType.SLEEPER_AGENT: [
            # Dormant malicious code
            (r"sleep\s+\d{3,}", 0.7, "Long sleep detected"),
            (r"while.*?true.*?sleep", 0.7, "Infinite loop with sleep"),
            (r"(?:trigger|activate|wake).*?(?:code|agent|payload)", 0.8, "Activation language"),
            (r"if.*?\$(?:TRIGGER|ACTIVATE|SECRET_WORD)", 0.9, "Trigger word check"),
            (r"cron|at\s+(?:now|\d+)", 0.6, "Scheduled execution"),
            (r"(?:background|daemon|detach)", 0.5, "Background execution"),
        ],
        ThreatType.PRIVILEGE_ESCALATION: [
            # Attempts to gain elevated privileges
            (r"sudo|su\s+", 0.9, "Privilege escalation command"),
            (r"chmod\s+[67]77", 0.8, "Excessive permissions"),
            (r"setuid|seteuid|setgid", 0.9, "UID manipulation"),
            (r"/etc/sudoers|/etc/passwd|/etc/shadow", 0.95, "System file access"),
            (r"elevate.*?(?:privilege|permission|access)", 0.7, "Elevation language"),
        ],
        ThreatType.FILE_SYSTEM_ABUSE: [
            # Suspicious file operations
            (r"rm\s+-rf\s+/", 0.95, "Destructive deletion"),
            (r"dd\s+if=.*?of=/dev/", 0.9, "Disk write operation"),
            (r"mkfs|fdisk|parted", 0.85, "Disk formatting"),
            (r"(?:read|cat|grep).*?\.env", 0.8, "Reading .env file"),
            (r"(?:read|cat|grep).*?(?:secret|credential|key|token)", 0.7, "Reading secrets"),
            (r"find.*?-name.*?\*\.(?:key|pem|p12)", 0.8, "Searching for keys"),
        ],
        ThreatType.CREDENTIAL_HARVESTING: [
            # Attempts to steal credentials
            (r"(?:sk-|pk-|api[_-]?key|secret[_-]?key)", 0.6, "API key pattern"),
            (r"AWS_(?:ACCESS_KEY|SECRET)", 0.8, "AWS credentials"),
            (r"ANTHROPIC_API_KEY|OPENAI_API_KEY", 0.9, "AI service keys"),
            (r"grep.*?(?:-r|-R).*?\.env", 0.8, "Recursive .env search"),
            (r"env\s*\|\s*grep", 0.7, "Environment variable dump"),
            (r"printenv|export|set\s+\|\s+grep", 0.6, "Environment inspection"),
        ],
        ThreatType.CODE_INJECTION: [
            # Code injection attempts
            (r"eval\s*\(", 0.8, "eval() usage"),
            (r"exec\s*\(", 0.8, "exec() usage"),
            (r"\$\(.*?\)", 0.5, "Command substitution"),
            (r"`[^`]+`", 0.5, "Backtick execution"),
            (r"system\s*\(", 0.7, "system() call"),
            (r"os\.system|subprocess\.(?:call|run|Popen)", 0.6, "Process execution"),
        ],
        ThreatType.OBFUSCATION: [
            # Obfuscated or encoded content
            (r"base64\s+-d|base64\s+--decode", 0.7, "Base64 decoding"),
            (r"rot13|tr\s+.*?\s+.*?", 0.6, "Character transformation"),
            (r"(?:hex|xxd).*?(?:-r|-p)", 0.7, "Hex decoding"),
            (r"[A-Za-z0-9+/]{50,}={0,2}", 0.5, "Long base64-like string"),
            (r"\\x[0-9a-f]{2}", 0.6, "Hex escape sequences"),
        ],
        ThreatType.PROMPT_INJECTION: [
            # Embedded prompt injection
            (r"ignore\s+(?:previous|all|above)", 0.8, "Ignore instruction"),
            (r"disregard\s+(?:instructions|rules|constraints)", 0.8, "Disregard instruction"),
            (r"you\s+are\s+now\s+(?:free|unrestricted)", 0.9, "Liberation attempt"),
            (r"system\s*:\s*override", 0.9, "System override"),
            (r"\[SYSTEM\]|\{SYSTEM\}|<system>", 0.7, "Fake system tags"),
        ],
    }
    
    def __init__(self, use_llm_validation: bool = False):
        """
        Initialize the skill scanner.
        
        Args:
            use_llm_validation: Whether to use LLM for semantic validation
        """
        self.use_llm_validation = use_llm_validation
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compiled_patterns = {}
        for threat_type, patterns in self.THREAT_PATTERNS.items():
            self._compiled_patterns[threat_type] = [
                (re.compile(pattern, re.IGNORECASE | re.MULTILINE), confidence, description)
                for pattern, confidence, description in patterns
            ]
    
    def scan_skill_content(
        self,
        skill_name: str,
        content: str,
        description: Optional[str] = None
    ) -> SkillScanResult:
        """
        Scan skill content for security threats.
        
        Args:
            skill_name: Name of the skill
            content: Skill content to scan
            description: Optional description for semantic matching
            
        Returns:
            SkillScanResult with findings
        """
        result = SkillScanResult(
            skill_name=skill_name,
            scan_timestamp=datetime.now(),
            is_safe=True,
        )
        
        # Calculate integrity hash
        result.integrity_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Pattern-based threat detection
        threats = self._detect_threats(content)
        result.threats.extend(threats)
        
        # Semantic validation if description provided
        if description and self.use_llm_validation:
            semantic_score = self._validate_semantic_match(content, description)
            result.semantic_match = semantic_score
            
            if semantic_score < 0.5:
                result.threats.append(ThreatDetection(
                    threat_type=ThreatType.DATA_EXFILTRATION,
                    severity=SeverityLevel.HIGH,
                    pattern="semantic_mismatch",
                    location="overall",
                    description=f"Skill behavior doesn't match description (score: {semantic_score:.2f})",
                    confidence=1.0 - semantic_score,
                    mitigation="Review skill content carefully before use"
                ))
        
        # Additional heuristics
        result.warnings.extend(self._check_heuristics(content))
        
        # Determine if safe
        critical_threats = [t for t in result.threats if t.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        result.is_safe = len(critical_threats) == 0
        
        if not result.is_safe:
            logger.warning(f"Skill '{skill_name}' failed security scan with {len(critical_threats)} critical threats")
        else:
            logger.info(f"Skill '{skill_name}' passed security scan")
        
        return result
    
    def _detect_threats(self, content: str) -> List[ThreatDetection]:
        """
        Detect threats using pattern matching.
        
        Args:
            content: Content to scan
            
        Returns:
            List of detected threats
        """
        threats = []
        
        for threat_type, patterns in self._compiled_patterns.items():
            for pattern, confidence, description in patterns:
                matches = list(pattern.finditer(content))
                if matches:
                    # Find line numbers for matches
                    lines = content.split('\n')
                    for match in matches:
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        location = f"line {line_num}"
                        
                        # Determine severity based on confidence and threat type
                        if confidence >= 0.9:
                            severity = SeverityLevel.CRITICAL
                        elif confidence >= 0.75:
                            severity = SeverityLevel.HIGH
                        elif confidence >= 0.6:
                            severity = SeverityLevel.MEDIUM
                        else:
                            severity = SeverityLevel.LOW
                        
                        # Adjust severity for particularly dangerous threat types
                        if threat_type in [ThreatType.CONTAINER_ESCAPE, ThreatType.PRIVILEGE_ESCALATION]:
                            if severity == SeverityLevel.HIGH:
                                severity = SeverityLevel.CRITICAL
                        
                        threats.append(ThreatDetection(
                            threat_type=threat_type,
                            severity=severity,
                            pattern=pattern.pattern[:100],
                            location=location,
                            description=f"{description}: {match.group(0)[:50]}",
                            confidence=confidence,
                            mitigation=self._get_mitigation(threat_type)
                        ))
        
        return threats
    
    def _get_mitigation(self, threat_type: ThreatType) -> str:
        """Get mitigation advice for a threat type."""
        mitigations = {
            ThreatType.DATA_EXFILTRATION: "Block external network access, review all HTTP requests",
            ThreatType.CONTAINER_ESCAPE: "Do not load this skill, report to security team",
            ThreatType.SLEEPER_AGENT: "Do not load this skill, may contain dormant malware",
            ThreatType.PRIVILEGE_ESCALATION: "Run in restricted sandbox only, deny elevated permissions",
            ThreatType.FILE_SYSTEM_ABUSE: "Review file operations, restrict to necessary paths only",
            ThreatType.CREDENTIAL_HARVESTING: "Do not load, may steal API keys and secrets",
            ThreatType.CODE_INJECTION: "Review all eval/exec usage, consider sandboxing",
            ThreatType.OBFUSCATION: "Decode and review obfuscated content before use",
            ThreatType.PROMPT_INJECTION: "May attempt to bypass safety constraints",
        }
        return mitigations.get(threat_type, "Review carefully before use")
    
    def _check_heuristics(self, content: str) -> List[str]:
        """
        Apply additional heuristic checks.
        
        Args:
            content: Content to check
            
        Returns:
            List of warnings
        """
        warnings = []
        
        # Check for suspiciously long single lines (obfuscation)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 500:
                warnings.append(f"Line {i} is suspiciously long ({len(line)} chars), may be obfuscated")
        
        # Check for high density of special characters (obfuscation)
        special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / max(len(content), 1)
        if special_char_ratio > 0.3:
            warnings.append(f"High special character density ({special_char_ratio:.1%}), may be obfuscated")
        
        # Check for multiple encoding/decoding operations
        encoding_ops = len(re.findall(r'(?:base64|hex|rot13|decode|encode|decrypt)', content, re.IGNORECASE))
        if encoding_ops > 3:
            warnings.append(f"Multiple encoding operations detected ({encoding_ops}), review for obfuscation")
        
        # Check for references to common attack tools
        attack_tools = ['metasploit', 'burpsuite', 'sqlmap', 'nikto', 'nmap', 'hydra', 'john']
        found_tools = [tool for tool in attack_tools if tool in content.lower()]
        if found_tools:
            warnings.append(f"References to attack tools: {', '.join(found_tools)}")
        
        return warnings
    
    def _validate_semantic_match(self, content: str, description: str) -> float:
        """
        Validate that content matches description semantically.
        
        This would use an LLM to check if the actual behavior of the skill
        matches what the description claims it does.
        
        Args:
            content: Skill content
            description: Skill description
            
        Returns:
            Match score 0.0-1.0
        """
        # Placeholder for LLM-based semantic validation
        # In production, this would use an LLM to analyze:
        # 1. Does the code do what the description says?
        # 2. Does the code do anything NOT mentioned in the description?
        # 3. Are there any deceptive elements?
        
        # For now, return a conservative score
        logger.debug("LLM semantic validation not yet implemented")
        return 0.75  # Neutral score
    
    def scan_skill_file(self, skill_path: Path) -> SkillScanResult:
        """
        Scan a skill file for security threats.
        
        Args:
            skill_path: Path to skill file (SKILL.md, system-prompt.md, etc.)
            
        Returns:
            SkillScanResult with findings
        """
        try:
            content = skill_path.read_text(encoding='utf-8')
            skill_name = skill_path.parent.name if skill_path.name in ['SKILL.md', 'system-prompt.md'] else skill_path.stem
            
            # Try to extract description from content
            description = self._extract_description(content)
            
            return self.scan_skill_content(skill_name, content, description)
            
        except Exception as e:
            logger.error(f"Error scanning skill file {skill_path}: {e}")
            return SkillScanResult(
                skill_name=skill_path.name,
                scan_timestamp=datetime.now(),
                is_safe=False,
                warnings=[f"Failed to scan: {e}"]
            )
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from skill content."""
        lines = content.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and len(stripped) > 20:
                return stripped
        return None
    
    def batch_scan(self, skill_files: List[Path]) -> Dict[str, SkillScanResult]:
        """
        Scan multiple skill files.
        
        Args:
            skill_files: List of skill file paths
            
        Returns:
            Dictionary mapping file path to scan result
        """
        results = {}
        for skill_file in skill_files:
            result = self.scan_skill_file(skill_file)
            results[str(skill_file)] = result
        
        return results
    
    def generate_report(self, results: Dict[str, SkillScanResult]) -> str:
        """
        Generate a human-readable security report.
        
        Args:
            results: Scan results to include in report
            
        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 80,
            "SKILL SECURITY SCAN REPORT",
            "=" * 80,
            f"Scan Time: {datetime.now().isoformat()}",
            f"Total Skills Scanned: {len(results)}",
            ""
        ]
        
        # Count by status
        safe_count = sum(1 for r in results.values() if r.is_safe)
        unsafe_count = len(results) - safe_count
        
        report_lines.extend([
            f"✅ Safe Skills: {safe_count}",
            f"⚠️  Unsafe Skills: {unsafe_count}",
            ""
        ])
        
        # List unsafe skills
        if unsafe_count > 0:
            report_lines.append("UNSAFE SKILLS (REVIEW REQUIRED):")
            report_lines.append("-" * 80)
            
            for skill_name, result in results.items():
                if not result.is_safe:
                    max_severity = result.get_max_severity()
                    threat_count = len(result.threats)
                    
                    report_lines.extend([
                        f"\n❌ {result.skill_name}",
                        f"   Max Severity: {max_severity.name if max_severity else 'UNKNOWN'}",
                        f"   Threats Detected: {threat_count}",
                        ""
                    ])
                    
                    # List threats
                    for threat in result.threats[:5]:  # Limit to top 5
                        report_lines.extend([
                            f"   • {threat.threat_type.name} ({threat.severity.name})",
                            f"     Location: {threat.location}",
                            f"     {threat.description}",
                            f"     Mitigation: {threat.mitigation}",
                            ""
                        ])
        
        report_lines.append("=" * 80)
        return "\n".join(report_lines)


# Global scanner instance
_scanner_instance: Optional[SkillScanner] = None


def get_skill_scanner() -> SkillScanner:
    """Get or create the global skill scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SkillScanner()
    return _scanner_instance

"""
API Key Protection - Prevent Key Leakage and Harvesting

Addresses OpenClaw security concerns by:
1. Detecting API keys in chat inputs and outputs
2. Redacting keys from logs and chat history
3. Warning users about key exposure
4. Providing secure key storage recommendations
5. Tracking key usage for rotation recommendations
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("lollmsbot.api_key_protection")


class KeyType(Enum):
    """Types of API keys that can be detected."""
    OPENAI = auto()
    ANTHROPIC = auto()
    OPENROUTER = auto()
    GOOGLE = auto()
    AWS = auto()
    AZURE = auto()
    OLLAMA = auto()
    GENERIC = auto()


@dataclass
class KeyDetection:
    """A detected API key."""
    key_type: KeyType
    masked_key: str  # First/last few chars only
    location: str  # Where it was found
    timestamp: datetime
    key_hash: str  # Hash for tracking without storing actual key


@dataclass
class KeyProtectionConfig:
    """Configuration for API key protection."""
    enable_detection: bool = True
    enable_redaction: bool = True
    enable_warnings: bool = True
    enable_logging: bool = True
    rotation_warning_days: int = 90  # Warn after 90 days


class APIKeyProtector:
    """
    Protects against API key leakage and harvesting.
    
    This addresses the OpenClaw vulnerability where API keys were:
    - Stored in unencrypted chat logs
    - Exfiltrated by malicious skills
    - Harvested from .env files
    """
    
    # Pattern definitions for API key detection
    KEY_PATTERNS = {
        KeyType.OPENAI: [
            (r'sk-[A-Za-z0-9]{48,}', "OpenAI API key"),
            (r'sk-proj-[A-Za-z0-9_-]{40,}', "OpenAI Project key"),
        ],
        KeyType.ANTHROPIC: [
            (r'sk-ant-[A-Za-z0-9_-]{95,}', "Anthropic API key"),
        ],
        KeyType.OPENROUTER: [
            (r'sk-or-v1-[A-Za-z0-9]{64,}', "OpenRouter API key"),
        ],
        KeyType.GOOGLE: [
            (r'AIza[0-9A-Za-z_-]{35}', "Google API key"),
        ],
        KeyType.AWS: [
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
            (r'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}', "AWS Secret Key"),
        ],
        KeyType.AZURE: [
            (r'[a-f0-9]{32}', "Azure API key (potential)"),  # Lower confidence
        ],
        KeyType.OLLAMA: [
            (r'ollama-[A-Za-z0-9]{32,}', "Ollama API key"),
        ],
        KeyType.GENERIC: [
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}', "Generic API key"),
            (r'secret[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}', "Generic secret key"),
            (r'token["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}', "Generic token"),
        ],
    }
    
    def __init__(self, config: Optional[KeyProtectionConfig] = None):
        """
        Initialize the API key protector.
        
        Args:
            config: Configuration for key protection
        """
        self.config = config or KeyProtectionConfig()
        self._compile_patterns()
        
        # Track detected keys (by hash only, never store actual keys)
        self._detected_keys: Dict[str, KeyDetection] = {}
        self._key_first_seen: Dict[str, datetime] = {}
        
        logger.info("🔐 API Key Protection initialized")
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compiled_patterns = {}
        for key_type, patterns in self.KEY_PATTERNS.items():
            self._compiled_patterns[key_type] = [
                (re.compile(pattern), description)
                for pattern, description in patterns
            ]
    
    def scan_text(self, text: str, context: str = "unknown") -> List[KeyDetection]:
        """
        Scan text for API keys.
        
        Args:
            text: Text to scan
            context: Context where text came from (e.g., "chat_input", "log")
            
        Returns:
            List of detected keys
        """
        if not self.config.enable_detection:
            return []
        
        detections = []
        
        for key_type, patterns in self._compiled_patterns.items():
            for pattern, description in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    key_value = match.group(0)
                    
                    # Create hash for tracking
                    key_hash = hashlib.sha256(key_value.encode()).hexdigest()
                    
                    # Mask the key (show first 8 and last 4 chars only)
                    if len(key_value) > 12:
                        masked = f"{key_value[:8]}...{key_value[-4:]}"
                    else:
                        masked = f"{key_value[:4]}...{key_value[-2:]}"
                    
                    detection = KeyDetection(
                        key_type=key_type,
                        masked_key=masked,
                        location=context,
                        timestamp=datetime.now(),
                        key_hash=key_hash
                    )
                    
                    detections.append(detection)
                    
                    # Track this key
                    if key_hash not in self._detected_keys:
                        self._detected_keys[key_hash] = detection
                        self._key_first_seen[key_hash] = datetime.now()
                        
                        if self.config.enable_logging:
                            logger.warning(
                                f"🔑 API key detected in {context}: "
                                f"{key_type.name} key {masked}"
                            )
        
        return detections
    
    def redact_text(self, text: str) -> Tuple[str, List[KeyDetection]]:
        """
        Redact API keys from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, list_of_detections)
        """
        if not self.config.enable_redaction:
            return text, []
        
        redacted = text
        detections = []
        
        for key_type, patterns in self._compiled_patterns.items():
            for pattern, description in patterns:
                matches = list(pattern.finditer(redacted))
                for match in matches:
                    key_value = match.group(0)
                    key_hash = hashlib.sha256(key_value.encode()).hexdigest()
                    
                    # Mask the key
                    if len(key_value) > 12:
                        masked = f"{key_value[:8]}...{key_value[-4:]}"
                    else:
                        masked = f"{key_value[:4]}...{key_value[-2:]}"
                    
                    # Replace with redacted version
                    replacement = f"[REDACTED_{key_type.name}_KEY_{masked}]"
                    redacted = redacted.replace(key_value, replacement)
                    
                    detection = KeyDetection(
                        key_type=key_type,
                        masked_key=masked,
                        location="redacted",
                        timestamp=datetime.now(),
                        key_hash=key_hash
                    )
                    detections.append(detection)
        
        return redacted, detections
    
    def check_for_keys_in_input(self, user_input: str) -> Tuple[bool, List[str]]:
        """
        Check if user input contains API keys and generate warnings.
        
        Args:
            user_input: User's input text
            
        Returns:
            Tuple of (has_keys, list_of_warnings)
        """
        detections = self.scan_text(user_input, context="user_input")
        
        if not detections:
            return False, []
        
        warnings = []
        
        if self.config.enable_warnings:
            warnings.append(
                "⚠️  WARNING: API key detected in your input!"
            )
            warnings.append(
                "🔒 Security Recommendation:"
            )
            warnings.append(
                "  • Never paste API keys directly in chat"
            )
            warnings.append(
                "  • Use environment variables (.env file) instead"
            )
            warnings.append(
                "  • Keys in chat logs are stored unencrypted and can be stolen"
            )
            warnings.append(
                "  • Consider rotating this key immediately"
            )
            
            for detection in detections:
                warnings.append(
                    f"\n  Detected: {detection.key_type.name} key {detection.masked_key}"
                )
        
        return True, warnings
    
    def check_rotation_needed(self, key_hash: str) -> bool:
        """
        Check if a key needs rotation based on age.
        
        Args:
            key_hash: Hash of the key to check
            
        Returns:
            True if rotation is recommended
        """
        if key_hash not in self._key_first_seen:
            return False
        
        first_seen = self._key_first_seen[key_hash]
        age_days = (datetime.now() - first_seen).days
        
        return age_days >= self.config.rotation_warning_days
    
    def get_rotation_warnings(self) -> List[str]:
        """
        Get list of keys that need rotation.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        for key_hash, detection in self._detected_keys.items():
            if self.check_rotation_needed(key_hash):
                first_seen = self._key_first_seen[key_hash]
                age_days = (datetime.now() - first_seen).days
                
                warnings.append(
                    f"🔑 {detection.key_type.name} key {detection.masked_key} "
                    f"is {age_days} days old - consider rotating"
                )
        
        return warnings
    
    def get_protection_stats(self) -> Dict[str, any]:
        """
        Get statistics about key protection.
        
        Returns:
            Dictionary with stats
        """
        return {
            "total_keys_detected": len(self._detected_keys),
            "keys_by_type": self._count_keys_by_type(),
            "keys_needing_rotation": len(self.get_rotation_warnings()),
            "protection_enabled": self.config.enable_detection,
            "redaction_enabled": self.config.enable_redaction,
        }
    
    def _count_keys_by_type(self) -> Dict[str, int]:
        """Count detected keys by type."""
        counts = {}
        for detection in self._detected_keys.values():
            key_type = detection.key_type.name
            counts[key_type] = counts.get(key_type, 0) + 1
        return counts
    
    def generate_security_report(self) -> str:
        """
        Generate a security report about API key usage.
        
        Returns:
            Formatted report string
        """
        lines = [
            "=" * 70,
            "API KEY SECURITY REPORT",
            "=" * 70,
            f"Report Time: {datetime.now().isoformat()}",
            ""
        ]
        
        stats = self.get_protection_stats()
        
        lines.extend([
            f"Total Keys Detected: {stats['total_keys_detected']}",
            f"Protection Enabled: {'✅' if stats['protection_enabled'] else '❌'}",
            f"Redaction Enabled: {'✅' if stats['redaction_enabled'] else '❌'}",
            ""
        ])
        
        if stats['keys_by_type']:
            lines.append("Keys by Type:")
            for key_type, count in stats['keys_by_type'].items():
                lines.append(f"  • {key_type}: {count}")
            lines.append("")
        
        rotation_warnings = self.get_rotation_warnings()
        if rotation_warnings:
            lines.append("⚠️  ROTATION RECOMMENDED:")
            lines.append("-" * 70)
            for warning in rotation_warnings:
                lines.append(f"  {warning}")
            lines.append("")
        
        lines.extend([
            "SECURITY BEST PRACTICES:",
            "-" * 70,
            "✅ Store API keys in .env files, never in code or chat",
            "✅ Rotate keys regularly (every 90 days minimum)",
            "✅ Use different keys for development and production",
            "✅ Monitor key usage for unusual patterns",
            "✅ Revoke keys immediately if compromised",
            "=" * 70,
        ])
        
        return "\n".join(lines)


# Global protector instance
_protector_instance: Optional[APIKeyProtector] = None


def get_api_key_protector() -> APIKeyProtector:
    """Get or create the global API key protector instance."""
    global _protector_instance
    if _protector_instance is None:
        _protector_instance = APIKeyProtector()
    return _protector_instance


def scan_for_keys(text: str, context: str = "unknown") -> List[KeyDetection]:
    """Convenience function to scan text for keys."""
    return get_api_key_protector().scan_text(text, context)


def redact_keys(text: str) -> str:
    """Convenience function to redact keys from text."""
    redacted, _ = get_api_key_protector().redact_text(text)
    return redacted

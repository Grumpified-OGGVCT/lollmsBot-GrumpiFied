"""
JSONL Store - Append-Only Immutable Storage

Implements OpenClaw's "Pearl Logs" - append-only audit trails that enable
time travel and point-in-time recovery. Unlike mutable databases, every
write is a new line appended to the file, preserving complete history.

Benefits:
- Complete audit trail of all operations
- Time travel: replay from any point in history
- Fork memory states to recover from bad updates
- Crash-safe: no partial writes
- Human-readable format (newline-delimited JSON)

This runs alongside the existing SQLite storage, providing:
- SQLite: Fast queries and active memory
- JSONL: Immutable audit log and time travel
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger("lollmsbot.storage.jsonl_store")


@dataclass
class LogEntry:
    """A single entry in the JSONL log.
    
    Attributes:
        timestamp: When this entry was written
        event_type: Type of event (message, memory_update, skill_execution, etc.)
        data: The actual event data
        metadata: Additional context (user_id, session_id, etc.)
    """
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_json(self) -> str:
        """Convert to JSON string for JSONL storage."""
        return json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "data": self.data,
            "metadata": self.metadata,
        })
    
    @classmethod
    def from_json(cls, line: str) -> LogEntry:
        """Parse from JSON string."""
        obj = json.loads(line)
        return cls(
            timestamp=datetime.fromisoformat(obj["timestamp"]),
            event_type=obj["event_type"],
            data=obj["data"],
            metadata=obj.get("metadata", {}),
        )


class JSONLStore:
    """Append-only storage using newline-delimited JSON.
    
    Each line is a complete JSON object. The file is only appended to,
    never modified, ensuring complete audit history.
    
    Usage:
        store = JSONLStore(Path("history.jsonl"))
        
        # Append events
        store.append("user_message", {
            "user_id": "alice",
            "message": "Hello!"
        })
        
        # Read all events
        for entry in store.read_all():
            print(entry.event_type, entry.timestamp)
        
        # Time travel: replay from specific time
        checkpoint = datetime(2024, 1, 1)
        for entry in store.read_since(checkpoint):
            replay_event(entry)
    """
    
    def __init__(self, filepath: Path):
        """Initialize JSONL store.
        
        Args:
            filepath: Path to JSONL file
        """
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.filepath.exists():
            self.filepath.touch()
            logger.info(f"Created new JSONL store: {self.filepath}")
        else:
            logger.info(f"Using existing JSONL store: {self.filepath}")
    
    def append(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a new entry to the log.
        
        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata (user_id, session_id, etc.)
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            data=data,
            metadata=metadata or {},
        )
        
        # Append to file (atomic write with newline)
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(entry.to_json() + '\n')
    
    def read_all(self) -> Iterator[LogEntry]:
        """Read all entries from the log.
        
        Yields:
            LogEntry objects in order
        """
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield LogEntry.from_json(line)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSONL line: {e}")
    
    def read_since(self, timestamp: datetime) -> Iterator[LogEntry]:
        """Read entries since a specific timestamp.
        
        Args:
            timestamp: Start time (inclusive)
            
        Yields:
            LogEntry objects after timestamp
        """
        for entry in self.read_all():
            if entry.timestamp >= timestamp:
                yield entry
    
    def read_range(
        self,
        start: datetime,
        end: datetime
    ) -> Iterator[LogEntry]:
        """Read entries in a time range.
        
        Args:
            start: Start time (inclusive)
            end: End time (inclusive)
            
        Yields:
            LogEntry objects in the time range
        """
        for entry in self.read_all():
            if start <= entry.timestamp <= end:
                yield entry
    
    def read_by_type(self, event_type: str) -> Iterator[LogEntry]:
        """Read entries of a specific type.
        
        Args:
            event_type: Event type to filter by
            
        Yields:
            LogEntry objects matching the type
        """
        for entry in self.read_all():
            if entry.event_type == event_type:
                yield entry
    
    def get_checkpoint_times(self) -> List[datetime]:
        """Get list of all entry timestamps (for time travel).
        
        Returns:
            List of timestamps that can be used as checkpoints
        """
        timestamps = []
        for entry in self.read_all():
            timestamps.append(entry.timestamp)
        return timestamps
    
    def replay_from(
        self,
        checkpoint: datetime,
        event_types: Optional[List[str]] = None
    ) -> Iterator[LogEntry]:
        """Replay events from a checkpoint (time travel).
        
        This allows recovering from a known good state by replaying
        all events after that checkpoint.
        
        Args:
            checkpoint: Time to replay from
            event_types: Optional list of event types to replay
            
        Yields:
            LogEntry objects to replay
        """
        for entry in self.read_since(checkpoint):
            if event_types is None or entry.event_type in event_types:
                yield entry
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the log file.
        
        Returns:
            Dict with stats (entry count, size, date range, etc.)
        """
        entry_count = 0
        event_types = set()
        first_timestamp = None
        last_timestamp = None
        
        for entry in self.read_all():
            entry_count += 1
            event_types.add(entry.event_type)
            
            if first_timestamp is None:
                first_timestamp = entry.timestamp
            last_timestamp = entry.timestamp
        
        return {
            "filepath": str(self.filepath),
            "entry_count": entry_count,
            "event_types": list(event_types),
            "first_entry": first_timestamp.isoformat() if first_timestamp else None,
            "last_entry": last_timestamp.isoformat() if last_timestamp else None,
            "file_size_kb": self.filepath.stat().st_size / 1024,
        }
    
    def compact(
        self,
        output_path: Optional[Path] = None,
        remove_before: Optional[datetime] = None,
        event_types_to_keep: Optional[List[str]] = None,
    ) -> int:
        """Create a compacted version of the log.
        
        Note: This creates a new file. The original remains immutable.
        
        Args:
            output_path: Path for compacted file (default: adds .compact suffix)
            remove_before: Remove entries before this timestamp
            event_types_to_keep: Only keep these event types
            
        Returns:
            Number of entries in compacted file
        """
        if output_path is None:
            output_path = self.filepath.with_suffix(self.filepath.suffix + '.compact')
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        kept_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in self.read_all():
                # Apply filters
                if remove_before and entry.timestamp < remove_before:
                    continue
                if event_types_to_keep and entry.event_type not in event_types_to_keep:
                    continue
                
                f.write(entry.to_json() + '\n')
                kept_count += 1
        
        logger.info(f"Compacted {self.filepath} -> {output_path}: {kept_count} entries")
        return kept_count


# Global audit log instance
_audit_log: Optional[JSONLStore] = None


def get_audit_log(filepath: Optional[Path] = None) -> JSONLStore:
    """Get or create the global audit log instance.
    
    Args:
        filepath: Optional custom path (default: ~/.lollmsbot/audit.jsonl)
        
    Returns:
        JSONLStore instance
    """
    global _audit_log
    if _audit_log is None:
        default_path = Path.home() / ".lollmsbot" / "audit.jsonl"
        _audit_log = JSONLStore(filepath or default_path)
    return _audit_log


def log_event(
    event_type: str,
    data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience function to log an event to the global audit log.
    
    Args:
        event_type: Type of event
        data: Event data
        metadata: Optional metadata
    """
    audit_log = get_audit_log()
    audit_log.append(event_type, data, metadata)

"""
Phase 3E: Activity Archival

This module handles long-term storage of hobby activities with compression
and provides historical analysis capabilities.
"""

import json
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class ArchiveStats:
    """Statistics about archived activities"""
    total_archived: int
    compressed_size_bytes: int
    original_size_bytes: int
    compression_ratio: float
    oldest_activity: str
    newest_activity: str
    activities_by_type: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActivityArchiveManager:
    """Manages long-term archival of hobby activities"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize archive manager
        
        Args:
            storage_path: Path for archive storage
        """
        self.storage_path = storage_path or Path.home() / ".lollmsbot" / "archive"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.archive_index: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        self._load_index()
        
        logger.info(f"Activity Archive Manager initialized at {self.storage_path}")
    
    def archive_activities(
        self,
        activities: List[Dict[str, Any]],
        archive_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archive a list of activities with compression
        
        Args:
            activities: List of activity dictionaries
            archive_name: Optional archive name (default: timestamp-based)
            
        Returns:
            Archive statistics
        """
        if not activities:
            return {"archived": 0, "error": "No activities to archive"}
        
        # Generate archive name
        if not archive_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"activities_{timestamp}"
        
        # Sort activities by date
        sorted_activities = sorted(
            activities,
            key=lambda a: a.get("started_at", "2000-01-01")
        )
        
        # Prepare archive data
        archive_data = {
            "archive_name": archive_name,
            "created_at": datetime.now().isoformat(),
            "activity_count": len(sorted_activities),
            "activities": sorted_activities
        }
        
        # Serialize to JSON
        json_data = json.dumps(archive_data, indent=2)
        original_size = len(json_data.encode('utf-8'))
        
        # Compress with gzip
        compressed_data = gzip.compress(json_data.encode('utf-8'), compresslevel=9)
        compressed_size = len(compressed_data)
        
        # Save compressed archive
        archive_file = self.storage_path / f"{archive_name}.json.gz"
        with open(archive_file, 'wb') as f:
            f.write(compressed_data)
        
        # Calculate statistics
        activities_by_type = {}
        for activity in sorted_activities:
            hobby_type = activity.get("hobby_type", "UNKNOWN")
            activities_by_type[hobby_type] = activities_by_type.get(hobby_type, 0) + 1
        
        oldest = sorted_activities[0].get("started_at", "unknown")
        newest = sorted_activities[-1].get("started_at", "unknown")
        
        # Update index
        with self._lock:
            self.archive_index[archive_name] = {
                "archive_file": str(archive_file),
                "created_at": archive_data["created_at"],
                "activity_count": len(sorted_activities),
                "compressed_size_bytes": compressed_size,
                "original_size_bytes": original_size,
                "compression_ratio": original_size / compressed_size if compressed_size > 0 else 0,
                "oldest_activity": oldest,
                "newest_activity": newest,
                "activities_by_type": activities_by_type
            }
            self._save_index()
        
        logger.info(f"Archived {len(sorted_activities)} activities to {archive_file}")
        logger.info(f"Compression: {original_size} -> {compressed_size} bytes ({original_size/compressed_size:.1f}x)")
        
        return {
            "archive_name": archive_name,
            "archived": len(sorted_activities),
            "compressed_size_bytes": compressed_size,
            "original_size_bytes": original_size,
            "compression_ratio": original_size / compressed_size,
            "archive_file": str(archive_file)
        }
    
    def list_archives(self) -> List[Dict[str, Any]]:
        """
        List all archives
        
        Returns:
            List of archive metadata
        """
        archives = []
        for name, metadata in self.archive_index.items():
            archives.append({
                "archive_name": name,
                **metadata
            })
        
        # Sort by created_at (most recent first)
        archives.sort(key=lambda a: a.get("created_at", ""), reverse=True)
        
        return archives
    
    def get_archive_stats(self, archive_name: str) -> Optional[ArchiveStats]:
        """
        Get statistics for a specific archive
        
        Args:
            archive_name: Archive name
            
        Returns:
            ArchiveStats or None if not found
        """
        metadata = self.archive_index.get(archive_name)
        if not metadata:
            return None
        
        return ArchiveStats(
            total_archived=metadata["activity_count"],
            compressed_size_bytes=metadata["compressed_size_bytes"],
            original_size_bytes=metadata["original_size_bytes"],
            compression_ratio=metadata["compression_ratio"],
            oldest_activity=metadata["oldest_activity"],
            newest_activity=metadata["newest_activity"],
            activities_by_type=metadata["activities_by_type"]
        )
    
    def load_archive(self, archive_name: str) -> List[Dict[str, Any]]:
        """
        Load and decompress an archive
        
        Args:
            archive_name: Archive name
            
        Returns:
            List of activities
        """
        metadata = self.archive_index.get(archive_name)
        if not metadata:
            raise ValueError(f"Archive {archive_name} not found")
        
        archive_file = Path(metadata["archive_file"])
        if not archive_file.exists():
            raise FileNotFoundError(f"Archive file {archive_file} not found")
        
        # Load and decompress
        with open(archive_file, 'rb') as f:
            compressed_data = f.read()
        
        json_data = gzip.decompress(compressed_data).decode('utf-8')
        archive_data = json.loads(json_data)
        
        activities = archive_data.get("activities", [])
        
        logger.info(f"Loaded {len(activities)} activities from archive {archive_name}")
        return activities
    
    def query_archive(
        self,
        archive_name: str,
        hobby_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query activities from an archive with filters
        
        Args:
            archive_name: Archive name
            hobby_type: Filter by hobby type
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum results
            
        Returns:
            Filtered list of activities
        """
        activities = self.load_archive(archive_name)
        
        # Apply filters
        if hobby_type:
            activities = [a for a in activities if a.get("hobby_type") == hobby_type]
        
        if start_date:
            activities = [a for a in activities if a.get("started_at", "") >= start_date]
        
        if end_date:
            activities = [a for a in activities if a.get("started_at", "") <= end_date]
        
        return activities[:limit]
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall archival statistics"""
        if not self.archive_index:
            return {
                "total_archives": 0,
                "total_activities": 0,
                "total_compressed_size": 0,
                "total_original_size": 0,
                "average_compression_ratio": 0
            }
        
        total_activities = sum(m["activity_count"] for m in self.archive_index.values())
        total_compressed = sum(m["compressed_size_bytes"] for m in self.archive_index.values())
        total_original = sum(m["original_size_bytes"] for m in self.archive_index.values())
        
        return {
            "total_archives": len(self.archive_index),
            "total_activities": total_activities,
            "total_compressed_size_bytes": total_compressed,
            "total_original_size_bytes": total_original,
            "average_compression_ratio": total_original / total_compressed if total_compressed > 0 else 0,
            "storage_saved_bytes": total_original - total_compressed
        }
    
    def auto_archive_old_activities(
        self,
        hobby_manager,
        days_old: int = 90
    ) -> Dict[str, Any]:
        """
        Automatically archive activities older than specified days
        
        Args:
            hobby_manager: HobbyManager instance
            days_old: Archive activities older than this many days
            
        Returns:
            Archive result
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Get all activities
        all_activities = hobby_manager.get_recent_activities(count=10000)
        
        # Filter old activities
        old_activities = [
            act for act in all_activities
            if datetime.fromisoformat(act.get("started_at", "2099-01-01")) < cutoff_date
        ]
        
        if not old_activities:
            return {"archived": 0, "message": "No old activities to archive"}
        
        # Create archive
        archive_name = f"auto_archive_{datetime.now().strftime('%Y%m%d')}"
        result = self.archive_activities(old_activities, archive_name)
        
        logger.info(f"Auto-archived {len(old_activities)} activities older than {days_old} days")
        
        return result
    
    def _save_index(self) -> None:
        """Save archive index to disk"""
        index_file = self.storage_path / "archive_index.json"
        
        try:
            with open(index_file, 'w') as f:
                json.dump(self.archive_index, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save archive index: {e}")
    
    def _load_index(self) -> None:
        """Load archive index from disk"""
        index_file = self.storage_path / "archive_index.json"
        
        if not index_file.exists():
            return
        
        try:
            with open(index_file, 'r') as f:
                self.archive_index = json.load(f)
            
            logger.info(f"Loaded archive index: {len(self.archive_index)} archives")
            
        except Exception as e:
            logger.warning(f"Failed to load archive index: {e}")


# Global instance
_archive_manager: Optional[ActivityArchiveManager] = None
_archive_lock = threading.Lock()


def get_archive_manager(storage_path: Optional[Path] = None) -> ActivityArchiveManager:
    """
    Get or create global archive manager
    
    Args:
        storage_path: Optional storage path
        
    Returns:
        ActivityArchiveManager instance
    """
    global _archive_manager
    
    if _archive_manager is not None:
        return _archive_manager
    
    with _archive_lock:
        if _archive_manager is None:
            _archive_manager = ActivityArchiveManager(storage_path)
        return _archive_manager

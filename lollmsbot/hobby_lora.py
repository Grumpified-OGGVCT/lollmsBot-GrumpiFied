"""
Phase 3B: LoRA Training Pipeline

This module manages the LoRA fine-tuning pipeline for continuous model improvement
based on insights gathered from hobby activities.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class TrainingStatus(str, Enum):
    """Training job statuses"""
    PENDING = "pending"
    PREPARING_DATA = "preparing_data"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AdapterStatus(str, Enum):
    """LoRA adapter statuses"""
    ACTIVE = "active"
    TESTING = "testing"
    ARCHIVED = "archived"
    FAILED = "failed"


@dataclass
class TrainingConfig:
    """Configuration for LoRA training"""
    model_name: str = "base_model"
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    learning_rate: float = 3e-4
    num_epochs: int = 3
    batch_size: int = 4
    max_seq_length: int = 512
    warmup_steps: int = 100
    save_steps: int = 100
    logging_steps: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrainingJob:
    """Represents a LoRA training job"""
    job_id: str
    status: TrainingStatus
    config: TrainingConfig
    data_path: Optional[Path]
    output_path: Optional[Path]
    num_examples: int
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    metrics: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "config": self.config.to_dict(),
            "data_path": str(self.data_path) if self.data_path else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "num_examples": self.num_examples,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "metadata": self.metadata
        }


@dataclass
class LoRAAdapter:
    """Represents a trained LoRA adapter"""
    adapter_id: str
    adapter_name: str
    status: AdapterStatus
    model_base: str
    adapter_path: Path
    training_job_id: str
    created_at: str
    metrics: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "status": self.status,
            "model_base": self.model_base,
            "adapter_path": str(self.adapter_path),
            "training_job_id": self.training_job_id,
            "created_at": self.created_at,
            "metrics": self.metrics,
            "metadata": self.metadata
        }


class LoRATrainingManager:
    """Manages LoRA training pipeline and adapters"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize LoRA training manager
        
        Args:
            storage_path: Path for storing training data and adapters
        """
        self.storage_path = storage_path or Path.home() / ".lollmsbot" / "lora"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.adapters: Dict[str, LoRAAdapter] = {}
        self.active_adapter_id: Optional[str] = None
        
        self._job_counter = 0
        self._adapter_counter = 0
        self._lock = threading.Lock()
        
        self._load_state()
        
        logger.info(f"LoRA Training Manager initialized at {self.storage_path}")
    
    def create_training_job(
        self,
        data_path: Path,
        num_examples: int,
        config: Optional[TrainingConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TrainingJob:
        """
        Create a new training job
        
        Args:
            data_path: Path to training data JSON
            num_examples: Number of training examples
            config: Training configuration
            metadata: Additional metadata
            
        Returns:
            Created TrainingJob
        """
        with self._lock:
            self._job_counter += 1
            job_id = f"job_{self._job_counter}_{int(datetime.now().timestamp())}"
        
        if config is None:
            config = TrainingConfig()
        
        output_path = self.storage_path / "adapters" / job_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        job = TrainingJob(
            job_id=job_id,
            status=TrainingStatus.PENDING,
            config=config,
            data_path=data_path,
            output_path=output_path,
            num_examples=num_examples,
            started_at=None,
            completed_at=None,
            error_message=None,
            metrics={},
            metadata=metadata or {}
        )
        
        self.training_jobs[job_id] = job
        self._save_state()
        
        logger.info(f"Created training job {job_id} with {num_examples} examples")
        return job
    
    async def start_training(self, job_id: str) -> None:
        """
        Start a training job (simulated for now)
        
        Args:
            job_id: Training job ID
        """
        job = self.training_jobs.get(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        if job.status != TrainingStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in PENDING status")
        
        logger.info(f"Starting training job {job_id}")
        
        try:
            # Update status
            job.status = TrainingStatus.PREPARING_DATA
            job.started_at = datetime.now().isoformat()
            self._save_state()
            
            # Simulate data preparation
            await asyncio.sleep(2)
            
            # Update to training
            job.status = TrainingStatus.TRAINING
            self._save_state()
            
            # Simulate training (in production, this would call actual training code)
            await self._simulate_training(job)
            
            # Update to evaluating
            job.status = TrainingStatus.EVALUATING
            self._save_state()
            
            # Simulate evaluation
            await asyncio.sleep(1)
            metrics = self._simulate_evaluation(job)
            job.metrics = metrics
            
            # Complete
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            self._save_state()
            
            # Create adapter
            adapter = self._create_adapter_from_job(job)
            self.adapters[adapter.adapter_id] = adapter
            self._save_state()
            
            logger.info(f"Training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}")
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            self._save_state()
            raise
    
    async def _simulate_training(self, job: TrainingJob) -> None:
        """Simulate training process"""
        config = job.config
        total_steps = (job.num_examples // config.batch_size) * config.num_epochs
        
        for step in range(0, total_steps, config.logging_steps):
            await asyncio.sleep(0.1)  # Simulate training time
            
            # Simulated metrics
            progress = step / total_steps
            job.metrics = {
                "step": step,
                "total_steps": total_steps,
                "progress": progress,
                "loss": 2.5 * (1 - progress * 0.8),  # Decreasing loss
                "learning_rate": config.learning_rate
            }
    
    def _simulate_evaluation(self, job: TrainingJob) -> Dict[str, Any]:
        """Simulate model evaluation"""
        return {
            "eval_loss": 0.85,
            "eval_accuracy": 0.78,
            "perplexity": 2.34,
            "training_time_seconds": 120,
            "num_examples": job.num_examples,
            "num_epochs": job.config.num_epochs
        }
    
    def _create_adapter_from_job(self, job: TrainingJob) -> LoRAAdapter:
        """Create LoRA adapter from completed training job"""
        with self._lock:
            self._adapter_counter += 1
            adapter_id = f"adapter_{self._adapter_counter}_{int(datetime.now().timestamp())}"
        
        adapter_name = f"hobby_lora_{job.job_id}"
        
        return LoRAAdapter(
            adapter_id=adapter_id,
            adapter_name=adapter_name,
            status=AdapterStatus.ACTIVE,
            model_base=job.config.model_name,
            adapter_path=job.output_path,
            training_job_id=job.job_id,
            created_at=datetime.now().isoformat(),
            metrics=job.metrics,
            metadata=job.metadata
        )
    
    def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID"""
        return self.training_jobs.get(job_id)
    
    def list_training_jobs(
        self,
        status: Optional[TrainingStatus] = None,
        limit: int = 50
    ) -> List[TrainingJob]:
        """
        List training jobs
        
        Args:
            status: Filter by status
            limit: Maximum number to return
            
        Returns:
            List of training jobs
        """
        jobs = list(self.training_jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by started_at (most recent first)
        jobs.sort(key=lambda j: j.started_at or "1970-01-01", reverse=True)
        
        return jobs[:limit]
    
    def get_adapter(self, adapter_id: str) -> Optional[LoRAAdapter]:
        """Get adapter by ID"""
        return self.adapters.get(adapter_id)
    
    def list_adapters(
        self,
        status: Optional[AdapterStatus] = None,
        limit: int = 50
    ) -> List[LoRAAdapter]:
        """
        List LoRA adapters
        
        Args:
            status: Filter by status
            limit: Maximum number to return
            
        Returns:
            List of adapters
        """
        adapters = list(self.adapters.values())
        
        if status:
            adapters = [a for a in adapters if a.status == status]
        
        # Sort by created_at (most recent first)
        adapters.sort(key=lambda a: a.created_at, reverse=True)
        
        return adapters[:limit]
    
    def set_active_adapter(self, adapter_id: str) -> None:
        """
        Set the active adapter
        
        Args:
            adapter_id: Adapter ID to activate
        """
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        adapter = self.adapters[adapter_id]
        if adapter.status != AdapterStatus.ACTIVE:
            raise ValueError(f"Adapter {adapter_id} is not in ACTIVE status")
        
        self.active_adapter_id = adapter_id
        self._save_state()
        
        logger.info(f"Set active adapter to {adapter_id}")
    
    def get_active_adapter(self) -> Optional[LoRAAdapter]:
        """Get the currently active adapter"""
        if self.active_adapter_id:
            return self.adapters.get(self.active_adapter_id)
        return None
    
    def archive_adapter(self, adapter_id: str) -> None:
        """
        Archive an adapter
        
        Args:
            adapter_id: Adapter ID to archive
        """
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter {adapter_id} not found")
        
        adapter = self.adapters[adapter_id]
        adapter.status = AdapterStatus.ARCHIVED
        
        if self.active_adapter_id == adapter_id:
            self.active_adapter_id = None
        
        self._save_state()
        logger.info(f"Archived adapter {adapter_id}")
    
    def compare_adapters(
        self,
        adapter_id_1: str,
        adapter_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two adapters (A/B testing)
        
        Args:
            adapter_id_1: First adapter ID
            adapter_id_2: Second adapter ID
            
        Returns:
            Comparison results
        """
        adapter1 = self.adapters.get(adapter_id_1)
        adapter2 = self.adapters.get(adapter_id_2)
        
        if not adapter1 or not adapter2:
            raise ValueError("One or both adapters not found")
        
        # In production, this would run actual A/B tests
        # For now, return simulated comparison
        return {
            "adapter_1": {
                "adapter_id": adapter_id_1,
                "adapter_name": adapter1.adapter_name,
                "metrics": adapter1.metrics
            },
            "adapter_2": {
                "adapter_id": adapter_id_2,
                "adapter_name": adapter2.adapter_name,
                "metrics": adapter2.metrics
            },
            "comparison": {
                "accuracy_diff": 0.02,  # Simulated
                "loss_diff": -0.15,  # Simulated
                "recommendation": "adapter_1" if adapter1.created_at > adapter2.created_at else "adapter_2"
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall training statistics"""
        jobs = list(self.training_jobs.values())
        adapters = list(self.adapters.values())
        
        return {
            "training_jobs": {
                "total": len(jobs),
                "by_status": {
                    status: len([j for j in jobs if j.status == status])
                    for status in TrainingStatus
                }
            },
            "adapters": {
                "total": len(adapters),
                "active": len([a for a in adapters if a.status == AdapterStatus.ACTIVE]),
                "archived": len([a for a in adapters if a.status == AdapterStatus.ARCHIVED]),
                "active_adapter_id": self.active_adapter_id
            }
        }
    
    def _save_state(self) -> None:
        """Save state to disk"""
        state_file = self.storage_path / "lora_state.json"
        
        state = {
            "training_jobs": {k: v.to_dict() for k, v in self.training_jobs.items()},
            "adapters": {k: v.to_dict() for k, v in self.adapters.items()},
            "active_adapter_id": self.active_adapter_id,
            "counters": {
                "job": self._job_counter,
                "adapter": self._adapter_counter
            }
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save LoRA state: {e}")
    
    def _load_state(self) -> None:
        """Load state from disk"""
        state_file = self.storage_path / "lora_state.json"
        
        if not state_file.exists():
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Load training jobs
            for job_data in state.get("training_jobs", {}).values():
                config = TrainingConfig(**job_data["config"])
                job = TrainingJob(
                    job_id=job_data["job_id"],
                    status=TrainingStatus(job_data["status"]),
                    config=config,
                    data_path=Path(job_data["data_path"]) if job_data["data_path"] else None,
                    output_path=Path(job_data["output_path"]) if job_data["output_path"] else None,
                    num_examples=job_data["num_examples"],
                    started_at=job_data["started_at"],
                    completed_at=job_data["completed_at"],
                    error_message=job_data["error_message"],
                    metrics=job_data["metrics"],
                    metadata=job_data["metadata"]
                )
                self.training_jobs[job.job_id] = job
            
            # Load adapters
            for adapter_data in state.get("adapters", {}).values():
                adapter = LoRAAdapter(
                    adapter_id=adapter_data["adapter_id"],
                    adapter_name=adapter_data["adapter_name"],
                    status=AdapterStatus(adapter_data["status"]),
                    model_base=adapter_data["model_base"],
                    adapter_path=Path(adapter_data["adapter_path"]),
                    training_job_id=adapter_data["training_job_id"],
                    created_at=adapter_data["created_at"],
                    metrics=adapter_data["metrics"],
                    metadata=adapter_data["metadata"]
                )
                self.adapters[adapter.adapter_id] = adapter
            
            self.active_adapter_id = state.get("active_adapter_id")
            
            # Load counters
            counters = state.get("counters", {})
            self._job_counter = counters.get("job", 0)
            self._adapter_counter = counters.get("adapter", 0)
            
            logger.info(f"Loaded LoRA state: {len(self.training_jobs)} jobs, {len(self.adapters)} adapters")
            
        except Exception as e:
            logger.warning(f"Failed to load LoRA state: {e}")


# Global instance
_lora_manager: Optional[LoRATrainingManager] = None
_lora_lock = threading.Lock()


def get_lora_manager(storage_path: Optional[Path] = None) -> LoRATrainingManager:
    """
    Get or create global LoRA training manager
    
    Args:
        storage_path: Optional storage path
        
    Returns:
        LoRATrainingManager instance
    """
    global _lora_manager
    
    if _lora_manager is not None:
        return _lora_manager
    
    with _lora_lock:
        if _lora_manager is None:
            _lora_manager = LoRATrainingManager(storage_path)
        return _lora_manager

"""Progress tracking for processing tasks across the pipeline."""

import json
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.models import ProcessingTask, TaskStatus


class ProgressManager:
    """Manages and persists progress of all processing tasks."""

    def __init__(self, progress_dir: str = "./state"):
        """
        Initialize progress manager.
        
        Args:
            progress_dir: Directory to store task progress JSON
        """
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.progress_dir / "tasks.json"
        self.tasks_in_memory: Dict[str, ProcessingTask] = {}
        self._load_tasks()

    def create_task(
        self,
        filename: str,
        source: str,
        file_size_bytes: int = 0,
        mode: str = "creative",
    ) -> ProcessingTask:
        """
        Create a new processing task.
        
        Args:
            filename: Name of the audio file
            source: "phone", "laptop", or "api"
            file_size_bytes: Size of uploaded file
            mode: "creative" or "distillation"
        
        Returns:
            Created ProcessingTask
        """
        task_id = str(uuid.uuid4())[:8]  # Short ID for readability
        task = ProcessingTask(
            task_id=task_id,
            filename=filename,
            source=source,
            status=TaskStatus.QUEUED,
            file_size_bytes=file_size_bytes,
            mode=mode,
        )
        self.tasks_in_memory[task_id] = task
        self._persist_tasks()
        print(f"[Progress] Task {task_id} created for {filename}")
        return task

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        **kwargs: Any,
    ) -> Optional[ProcessingTask]:
        """
        Update task status and optional metadata.
        
        Args:
            task_id: Task ID to update
            status: New TaskStatus
            **kwargs: Additional fields to update (error_message, transcript_text, etc.)
        
        Returns:
            Updated ProcessingTask or None if not found
        """
        if task_id not in self.tasks_in_memory:
            return None

        task = self.tasks_in_memory[task_id]
        task.status = status
        
        # Update timestamps
        if status == TaskStatus.UPLOADING and not task.started_at:
            task.started_at = datetime.now().isoformat()
        
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = datetime.now().isoformat()
        
        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self._persist_tasks()
        print(f"[Progress] Task {task_id}: {status.value}")
        return task

    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """Get task by ID."""
        return self.tasks_in_memory.get(task_id)

    def list_tasks(self, source: Optional[str] = None, limit: int = 100) -> List[ProcessingTask]:
        """
        List all tasks, optionally filtered by source.
        
        Args:
            source: Filter by "phone", "laptop", or "api" (optional)
            limit: Max number of recent tasks to return
        
        Returns:
            List of ProcessingTasks, most recent first
        """
        tasks = list(self.tasks_in_memory.values())
        
        if source:
            tasks = [t for t in tasks if t.source == source]
        
        # Sort by created_at descending (most recent first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]

    def get_active_tasks(self) -> List[ProcessingTask]:
        """Get tasks that are still processing (not completed/failed)."""
        return [
            t for t in self.tasks_in_memory.values()
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about all tasks."""
        tasks = list(self.tasks_in_memory.values())
        
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        active = self.get_active_tasks()
        
        total_transcript_chars = sum(t.transcript_length for t in completed)
        avg_duration = (
            sum(t.duration_seconds for t in completed) / len(completed)
            if completed
            else 0
        )
        
        return {
            "total_tasks": len(tasks),
            "completed": len(completed),
            "failed": len(failed),
            "active": len(active),
            "total_transcript_characters": total_transcript_chars,
            "average_audio_duration_seconds": avg_duration,
            "sources": {
                "phone": len([t for t in tasks if t.source == "phone"]),
                "laptop": len([t for t in tasks if t.source == "laptop"]),
                "api": len([t for t in tasks if t.source == "api"]),
            },
        }

    def _load_tasks(self) -> None:
        """Load tasks from disk."""
        if not self.progress_file.exists():
            return
        
        try:
            with open(self.progress_file, "r") as f:
                data = json.load(f)
            
            for task_data in data.get("tasks", []):
                task = ProcessingTask.from_dict(task_data)
                self.tasks_in_memory[task.task_id] = task
            
            print(f"[Progress] Loaded {len(self.tasks_in_memory)} tasks from disk")
        except Exception as e:
            print(f"[Progress] Warning: Failed to load tasks: {e}")

    def _persist_tasks(self) -> None:
        """Persist all tasks to disk."""
        tasks_data = [task.to_dict() for task in self.tasks_in_memory.values()]
        
        temp_file = self.progress_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump({"tasks": tasks_data}, f, indent=2)
        
        temp_file.replace(self.progress_file)

"""Data models for Block 1 system state."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum
import json


class Mode(str, Enum):
    CREATIVE = "creative"
    DISTILLATION = "distillation"


@dataclass
class TranscriptChunk:
    """A single transcript chunk with metadata."""
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "user"  # "user" or "system"
    duration_seconds: float = 0.0

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TranscriptChunk":
        return TranscriptChunk(**data)


@dataclass
class SystemState:
    """Complete system state: transcript buffer, spec, mode, metadata."""
    transcript_buffer: List[TranscriptChunk] = field(default_factory=list)
    current_spec_markdown: str = ""
    mode: Mode = Mode.CREATIVE
    version: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "transcript_buffer": [chunk.to_dict() for chunk in self.transcript_buffer],
            "current_spec_markdown": self.current_spec_markdown,
            "mode": self.mode.value,
            "version": self.version,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SystemState":
        transcript_buffer = [
            TranscriptChunk.from_dict(chunk) for chunk in data.get("transcript_buffer", [])
        ]
        return SystemState(
            transcript_buffer=transcript_buffer,
            current_spec_markdown=data.get("current_spec_markdown", ""),
            mode=Mode(data.get("mode", "creative")),
            version=data.get("version", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            session_id=data.get("session_id", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SpecDelta:
    """Represents changes to the markdown spec (section-level granularity)."""
    section: str  # e.g., "## Objective", "## Ideas"
    old_content: str = ""
    new_content: str = ""
    action: str = "update"  # "update", "create", "delete"

    def to_dict(self):
        return asdict(self)

"""State persistence layer for Block 1 system."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.models import SystemState, TranscriptChunk, Mode


class StateManager:
    """Manages atomic read/write of system state (JSON + Markdown)."""

    def __init__(self, state_dir: str = "./state", specs_dir: str = "./specs"):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory for JSON state files
            specs_dir: Directory for markdown spec files
        """
        self.state_dir = Path(state_dir)
        self.specs_dir = Path(specs_dir)
        
        # Create directories if they don't exist
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / "current.json"
        self.spec_file = self.specs_dir / "spec.md"

    def load_state(self) -> SystemState:
        """Load system state from disk. Return empty state if not found."""
        if not self.state_file.exists():
            return self._create_default_state()
        
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
            return SystemState.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load state ({e}), creating new state")
            return self._create_default_state()

    def load_spec(self) -> str:
        """Load markdown spec from disk. Return default template if not found."""
        if not self.spec_file.exists():
            return self._create_default_spec()
        
        with open(self.spec_file, "r", encoding="utf-8") as f:
            return f.read()

    def save_state(self, state: SystemState) -> None:
        """Atomically save state JSON to disk."""
        state.last_updated = datetime.now().isoformat()
        state.version += 1
        
        # Write to temporary file first, then rename (atomic)
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        
        temp_file.replace(self.state_file)

    def save_spec(self, spec_markdown: str) -> None:
        """Atomically save markdown spec to disk."""
        # Write to temporary file first, then rename (atomic)
        temp_file = self.spec_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(spec_markdown)
        
        temp_file.replace(self.spec_file)

    def append_transcript(self, text: str, source: str = "user", duration: float = 0.0) -> None:
        """Append a transcript chunk and save state."""
        state = self.load_state()
        chunk = TranscriptChunk(text=text, source=source, duration_seconds=duration)
        state.transcript_buffer.append(chunk)
        self.save_state(state)

    def get_transcript_history(self) -> str:
        """Get full transcript history as formatted string."""
        state = self.load_state()
        if not state.transcript_buffer:
            return "No transcript history"
        
        lines = []
        for chunk in state.transcript_buffer:
            lines.append(f"[{chunk.timestamp}] {chunk.source}: {chunk.text}")
        return "\n".join(lines)

    def update_spec_section(self, section_header: str, new_content: str) -> None:
        """
        Update a single markdown section in the spec.
        
        Args:
            section_header: Section header without ## (e.g., "Objective")
            new_content: New content for that section (without header)
        """
        spec = self.load_spec()
        section_marker = f"## {section_header}"
        
        # Check if section exists
        if section_marker not in spec:
            # Section doesn't exist, append it
            spec += f"\n\n{section_marker}\n{new_content}"
        else:
            # Find and replace section content
            lines = spec.split("\n")
            section_start = None
            section_end = None
            
            for i, line in enumerate(lines):
                if line.strip().startswith(section_marker):
                    section_start = i
                    # Find the next section or end of file
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith("##"):
                            section_end = j
                            break
                    if section_end is None:
                        section_end = len(lines)
                    break
            
            if section_start is not None:
                # Replace section content
                new_lines = (
                    lines[:section_start + 1] +
                    [new_content] +
                    lines[section_end:]
                )
                spec = "\n".join(new_lines)
        
        self.save_spec(spec)

    def get_spec_section(self, section_header: str) -> str:
        """Get content of a specific section from markdown spec."""
        spec = self.load_spec()
        section_marker = f"## {section_header}"
        
        if section_marker not in spec:
            return ""
        
        lines = spec.split("\n")
        section_start = None
        section_end = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith(section_marker):
                section_start = i + 1
                # Find next section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("##"):
                        section_end = j
                        break
                if section_end is None:
                    section_end = len(lines)
                break
        
        if section_start is not None:
            return "\n".join(lines[section_start:section_end]).strip()
        
        return ""

    def switch_mode(self, mode: Mode) -> None:
        """Switch system mode (Creative or Distillation)."""
        state = self.load_state()
        state.mode = mode
        self.save_state(state)

    def get_mode(self) -> Mode:
        """Get current system mode."""
        state = self.load_state()
        return state.mode

    def _create_default_state(self) -> SystemState:
        """Create a default/empty system state."""
        import uuid
        return SystemState(
            session_id=str(uuid.uuid4())[:8],
            mode=Mode.CREATIVE,
            current_spec_markdown=self._create_default_spec(),
        )

    @staticmethod
    def _create_default_spec() -> str:
        """Create default markdown spec template."""
        return """# Block 1: Research Ideation & Distillation Specification

## Objective


## Context


## Ideas


## Hypotheses


## Constraints


## Assumptions


## Requirements


## Conceptual Plan


## Open Questions

"""

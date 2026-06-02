# Data Models & Expected Structures

## Overview

This document describes all data structures used throughout Block 1 system. Each model is persisted or transferred in the specified format. These are the "contracts" for communication between components.

## Core System Models (src/models.py)

### Mode Enum

**Purpose**: Current operating mode of the system

**Values**:
- `"creative"` - Divergent thinking mode (brainstorming, idea generation)
- `"distillation"` - Convergent thinking mode (consolidation, structure building)

**Usage**: 
```python
from src.models import Mode
current_mode = Mode.CREATIVE
mode_value = current_mode.value  # "creative"
```

---

### TranscriptChunk

**Purpose**: Single piece of transcript with metadata

**Structure**:
```python
{
    "text": "the actual transcript text here",
    "timestamp": "2026-06-02T10:15:23.456789",  # ISO 8601
    "source": "phone",  # "phone", "laptop", "api", "whisper", or "user"
    "duration_seconds": 45.2
}
```

**Fields**:
- `text` (str): The actual transcript content
- `timestamp` (str): ISO 8601 timestamp of when chunk was created
- `source` (str): Where the transcript came from
- `duration_seconds` (float): Duration of audio for this chunk

**JSON Representation**:
```json
{
  "text": "let's explore the semantic planning system",
  "timestamp": "2026-06-02T10:15:23.123456",
  "source": "phone",
  "duration_seconds": 8.5
}
```

---

### SystemState

**Purpose**: Complete system state (single source of truth)

**Structure**:
```python
{
    "transcript_buffer": [
        TranscriptChunk,  # List of all transcript chunks
        TranscriptChunk,
        ...
    ],
    "current_spec_markdown": "# Block 1 Specification\n\n...",
    "mode": "creative",  # or "distillation"
    "version": 42,
    "created_at": "2026-06-01T08:00:00.000000",
    "last_updated": "2026-06-02T10:15:45.123456",
    "session_id": "sess-abc123xyz789",
    "metadata": {
        "custom_key": "custom_value",
        "tags": ["important", "phase-1"]
    }
}
```

**Persistence**: Stored as `./state/current.json`

**Fields**:
- `transcript_buffer` (List[TranscriptChunk]): Ordered history of all transcripts
- `current_spec_markdown` (str): The living markdown specification
- `mode` (str): Current system mode
- `version` (int): Incremented on every save (for concurrency detection)
- `created_at` (str): When this session started
- `last_updated` (str): Last modification timestamp
- `session_id` (str): Unique identifier for this session
- `metadata` (dict): Extensible key-value store for custom data

**Example JSON File**:
```json
{
  "transcript_buffer": [
    {
      "text": "first recording about the system design",
      "timestamp": "2026-06-02T10:15:23.123456",
      "source": "phone",
      "duration_seconds": 45.2
    },
    {
      "text": "second recording on implementation details",
      "timestamp": "2026-06-02T10:45:12.654321",
      "source": "laptop",
      "duration_seconds": 32.8
    }
  ],
  "current_spec_markdown": "# Block 1\n\n## Overview\n...",
  "mode": "creative",
  "version": 15,
  "created_at": "2026-06-01T08:00:00.000000",
  "last_updated": "2026-06-02T10:45:13.654321",
  "session_id": "sess-abc123xyz789",
  "metadata": {}
}
```

---

### TaskStatus Enum

**Purpose**: Progress status of a processing task

**Values**:
- `"queued"` - Task created, waiting to start
- `"uploading"` - File upload in progress
- `"transcribing"` - Whisper transcription in progress
- `"processing"` - Semantic engine processing
- `"completed"` - Successfully finished
- `"failed"` - Error occurred

**Transitions**:
```
queued → uploading → transcribing → processing → completed
  ↘                                              ↗
   (can fail at any stage)                  failed
```

---

### ProcessingTask

**Purpose**: Track a single file through the entire pipeline

**Structure**:
```python
{
    "task_id": "a1b2c3d4",
    "filename": "research_notes.wav",
    "source": "phone",  # "phone", "laptop", or "api"
    "status": "completed",  # one of TaskStatus values
    "created_at": "2026-06-02T10:15:23.123456",
    "started_at": "2026-06-02T10:15:24.234567",
    "completed_at": "2026-06-02T10:16:45.456789",
    
    # File metadata
    "file_size_bytes": 2456789,
    "duration_seconds": 45.2,
    
    # Processing results
    "transcript_text": "the actual transcript content here...",
    "transcript_length": 4521,  # character count
    "spec_updated": true,
    "error_message": "",  # empty if successful
    
    # Processing metadata
    "mode": "creative",
    "backend_used": "claude"  # "claude" or "dgx"
}
```

**Persistence**: Stored in `./state/tasks.json` as array

**Fields**:
- `task_id` (str): 8-character unique identifier
- `filename` (str): Original audio filename
- `source` (str): "phone", "laptop", or "api"
- `status` (str): Current progress status
- `created_at` (str): When task was created
- `started_at` (str): When processing began
- `completed_at` (str): When task finished (empty if still running)
- `file_size_bytes` (int): Size of uploaded audio
- `duration_seconds` (float): Estimated duration from metadata
- `transcript_text` (str): The actual transcript text
- `transcript_length` (int): Character count of transcript
- `spec_updated` (bool): Whether spec was updated as result
- `error_message` (str): Error details if failed, empty if successful
- `mode` (str): Creative or distillation mode used
- `backend_used` (str): Which LLM backend processed it

**Example JSON in tasks.json**:
```json
{
  "tasks": [
    {
      "task_id": "a1b2c3d4",
      "filename": "research_notes.wav",
      "source": "phone",
      "status": "completed",
      "created_at": "2026-06-02T10:15:23.123456",
      "started_at": "2026-06-02T10:15:24.234567",
      "completed_at": "2026-06-02T10:16:45.456789",
      "file_size_bytes": 2456789,
      "duration_seconds": 45.2,
      "transcript_text": "let's explore semantic planning...",
      "transcript_length": 4521,
      "spec_updated": true,
      "error_message": "",
      "mode": "creative",
      "backend_used": "claude"
    },
    {
      "task_id": "b2c3d4e5",
      "filename": "brainstorm.m4a",
      "source": "laptop",
      "status": "failed",
      "created_at": "2026-06-02T10:30:15.111111",
      "started_at": "2026-06-02T10:30:16.222222",
      "completed_at": "2026-06-02T10:30:18.333333",
      "file_size_bytes": 1234567,
      "duration_seconds": 28.5,
      "transcript_text": "",
      "transcript_length": 0,
      "spec_updated": false,
      "error_message": "Transcription service timeout after 30 seconds",
      "mode": "creative",
      "backend_used": ""
    }
  ]
}
```

---

## API Request/Response Models (src/api_server.py)

### ProcessRequest

**Purpose**: Request text processing via HTTP

**HTTP Method**: `POST /process`

**Request Body**:
```json
{
    "text": "the transcript text to process",
    "mode": "creative"
}
```

**Fields**:
- `text` (str): Transcript content to process
- `mode` (str, optional): "creative" or "distillation" (default: "creative")

---

### TranscribeResponse

**Purpose**: Response from transcription endpoint

**HTTP Method**: `POST /transcribe` response

**Response Body**:
```json
{
    "text": "the transcribed text",
    "duration": 45.2,
    "task_id": "a1b2c3d4"
}
```

**Fields**:
- `text` (str): Transcribed content
- `duration` (float): Audio duration in seconds
- `task_id` (str): Task ID for tracking progress

---

### TaskProgressResponse

**Purpose**: Status of a single task

**HTTP Method**: `GET /progress/{task_id}` response

**Response Body**:
```json
{
    "task_id": "a1b2c3d4",
    "filename": "research_notes.wav",
    "source": "phone",
    "status": "completed",
    "created_at": "2026-06-02T10:15:23.123456",
    "started_at": "2026-06-02T10:15:24.234567",
    "completed_at": "2026-06-02T10:16:45.456789",
    "file_size_bytes": 2456789,
    "duration_seconds": 45.2,
    "error_message": "",
    "transcript_length": 4521,
    "spec_updated": true,
    "backend_used": "claude"
}
```

---

### TasksListResponse

**Purpose**: List of recent tasks with metadata

**HTTP Method**: `GET /progress` response

**Response Body**:
```json
{
    "tasks": [
        {
            "task_id": "a1b2c3d4",
            "filename": "research_notes.wav",
            "source": "phone",
            "status": "completed",
            ...
        },
        {
            "task_id": "b2c3d4e5",
            "filename": "brainstorm.m4a",
            "source": "laptop",
            "status": "processing",
            ...
        }
    ],
    "total": 2,
    "active_count": 1
}
```

**Fields**:
- `tasks` (list): Array of TaskProgressResponse
- `total` (int): Total tasks in result set
- `active_count` (int): Tasks currently processing (not completed/failed)

**Query Parameters**:
- `source` (str, optional): Filter by "phone", "laptop", or "api"
- `limit` (int, optional): Max results (default 50, max 200)

---

### ProgressStatsResponse

**Purpose**: Aggregate statistics about all tasks

**HTTP Method**: `GET /progress/stats` response

**Response Body**:
```json
{
    "total_tasks": 156,
    "completed": 148,
    "failed": 2,
    "active": 6,
    "total_transcript_characters": 847539,
    "average_audio_duration_seconds": 42.3,
    "sources": {
        "phone": 89,
        "laptop": 54,
        "api": 13
    }
}
```

**Fields**:
- `total_tasks` (int): Total tasks created
- `completed` (int): Successfully completed
- `failed` (int): Failed with error
- `active` (int): Currently processing
- `total_transcript_characters` (int): Sum of all transcript lengths
- `average_audio_duration_seconds` (float): Mean duration of audio files
- `sources` (dict): Breakdown by source (phone/laptop/api)

---

## File Formats

### state/current.json

**Format**: JSON

**Structure**: SystemState (see above)

**Purpose**: Single source of truth for system state

**Update Frequency**: After every transcript or spec change

**Atomic Operations**: Uses temp file + rename to prevent corruption

---

### state/tasks.json

**Format**: JSON array wrapped in object

**Structure**:
```json
{
  "tasks": [ProcessingTask, ProcessingTask, ...]
}
```

**Purpose**: Persistent record of all processing tasks

**Update Frequency**: When task status changes

**Atomic Operations**: Uses temp file + rename

---

### specs/spec.md

**Format**: Markdown

**Structure**: Living specification with sections

**Example Content**:
```markdown
# Block 1 Specification

## 1. Overview
Research ideation and distillation system...

## 2. Key Concepts
- Creative mode
- Distillation mode
- ...

## 3. Requirements
- Auto-transcription
- Progress tracking
- ...
```

**Purpose**: Versioned, human-readable specification

**Update Frequency**: After semantic processing of transcripts

**Access**: OneDrive synced, accessible offline

---

## Service Integration Points

### TranscriptionService → SystemState

**Input**: Audio file path
**Output**: Transcript text added to SystemState.transcript_buffer

### SemanticEngine → SystemState

**Input**: 
- Current transcript
- Transcript history
- Current spec
- Mode

**Output**: 
- Updated spec markdown
- Backend used (claude/dgx)

### ProgressManager → JSON Files

**Input**: Task updates
**Output**: Persisted to state/tasks.json

### StateManager → File System

**Input**: SystemState, Markdown spec
**Output**: JSON and Markdown files

---

## Data Validation Rules

### transcript_buffer
- Each chunk must have non-empty "text"
- Timestamps must be valid ISO 8601
- Source must be one of: phone, laptop, api, whisper, user
- Duration cannot be negative

### SystemState
- version must increment on save
- session_id must be unique per session
- mode must be valid Mode enum
- last_updated always updated on save

### ProcessingTask
- task_id must be unique
- filename must be non-empty
- status must be valid TaskStatus
- timestamps must be in chronological order (created < started < completed)
- transcript_length must match len(transcript_text)

### API Responses
- All string fields should use consistent JSON encoding
- Timestamps always ISO 8601
- Enums returned as lowercase strings

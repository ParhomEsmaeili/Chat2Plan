# Script Purposes & Expected Outputs

## Overview

This document describes each Python script in the codebase, what it does, how it's invoked, and what output you can expect.

---

## main.py

**Purpose**: Entry point for the Block 1 system

**Invocation**:
```bash
python main.py
```

**What It Does**:
1. Imports the CLI main() function from src.cli
2. Runs the interactive command-line interface
3. Blocks until user exits (Ctrl+C)

**Expected Output**:
```
Block 1 Research Ideation System
==================================================
Mode: CREATIVE
Type 'help' for commands

>>> 
```

**Then waits for user input** (see CLI section for commands)

**Exit Behavior**:
```
>>> exit
Exiting...
(program terminates)
```

---

## src/api_server.py

**Purpose**: FastAPI REST server for remote access to Block 1

**Invocation**:
```bash
python -m src.api_server
```

Or from code:
```python
from src.api_server import run_server
run_server(host="0.0.0.0", port=8001)
```

**What It Does**:
1. Initializes FastAPI application
2. Sets up all service instances (state_manager, semantic_engine, transcription_service, progress_manager)
3. Starts uvicorn server on specified host:port
4. Listens for HTTP requests on endpoints

**Expected Output** (startup):
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Then serves HTTP requests indefinitely**

**Exit Behavior**:
```
(Ctrl+C pressed)
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
(program terminates)
```

**Endpoints Served**:
- GET /health → {"status": "ok", "session": "sess-xxx"}
- GET /status → SystemState summary
- GET /spec → {"spec": "markdown..."}
- GET /transcript → {"transcript": "text..."}
- POST /process → {"spec": "updated...", "backend": "claude"}
- POST /transcribe → {"text": "...", "task_id": "xxxx"}
- GET /progress/{task_id} → TaskProgressResponse
- GET /progress → TasksListResponse
- GET /progress/stats → ProgressStatsResponse
- POST /mode/{mode} → {"mode": "creative", "status": "switched"}

---

## src/file_watcher.py (run as module)

**Purpose**: Background daemon that monitors OneDrive recordings folder for new files

**Invocation**:
```bash
python -m src.file_watcher
```

Or from code:
```python
from src.file_watcher import run_file_watcher
run_file_watcher()  # Blocks indefinitely
```

**What It Does**:
1. Initializes all services (state_manager, semantic_engine, transcription_service, progress_manager)
2. Creates FileWatcher instance pointing to OneDrive/recordings folder
3. Starts watchdog observer to monitor folder
4. When new audio file appears:
   - Creates ProcessingTask with task_id
   - Waits 1 second for file write to complete
   - Calls transcription service (status: transcribing)
   - Adds transcript to buffer (status: processing)
   - Calls semantic engine to process
   - Updates spec markdown
   - Marks task completed

**Expected Output** (startup):
```
[Progress] Loaded 42 tasks from disk
File watcher running. Press Ctrl+C to stop.
Starting file watcher on C:\Users\pe23\OneDrive\Chat2Plan\recordings
```

**When file is detected**:
```
[Progress] Task a1b2c3d4 created for research_notes.wav
[FileWatcher] New audio file detected: research_notes.wav
[Progress] Task a1b2c3d4: uploading
[Progress] Task a1b2c3d4: transcribing
[FileWatcher] Transcribing research_notes.wav...
[FileWatcher] Transcription complete: 4521 characters
[Progress] Task a1b2c3d4: processing
[FileWatcher] Processing in CREATIVE mode...
[Progress] Task a1b2c3d4: completed
[FileWatcher] Spec updated (backend: claude)
```

**Exit Behavior**:
```
(Ctrl+C pressed)
Shutting down...
(program terminates)
```

**Files Created/Modified**:
- `./state/tasks.json` - New task added, status updated
- `./state/current.json` - Transcript appended, spec updated
- `./specs/spec.md` - Markdown spec updated
- `./recordings/research_notes.wav` - Copy of audio file

---

## src/cli.py (via main.py)

**Purpose**: Interactive command-line interface for Block 1

**Invocation**: Via `python main.py` or:
```python
from src.cli import Block1CLI
cli = Block1CLI()
cli.run()
```

**What It Does**:
1. Initializes state_manager, semantic_engine, transcription_service
2. Enters command loop
3. Parses user commands and routes to handlers
4. Displays results back to user

**Expected Commands & Outputs**:

### help
```
>>> help

Commands:
  help                - Show this help message
  status              - Show current system status
  mode [creative|distillation] - Switch mode
  
  transcript          - Show full transcript history
  spec                - Show current markdown spec
  section <name>      - Show specific section (e.g., 'Objective')
  
  transcribe <path>   - Transcribe audio file and add to buffer
  process [text]      - Process transcript/text through semantic engine
                        If no text provided, uses latest transcript chunk
  
  exit                - Exit the system
```

### status
```
>>> status
Session ID: sess-abc123xyz789
Mode: CREATIVE
Transcript chunks: 5
Spec size: 2845
Last updated: 2026-06-02T10:15:45.123456
```

### transcript
```
>>> transcript

--- Transcript History ---
[2026-06-02T10:15:23] (phone, 45.2s):
the first recording about system design

[2026-06-02T10:45:12] (laptop, 32.8s):
second recording on implementation details
```

### spec
```
>>> spec

--- Current Specification ---
# Block 1 Specification

## Overview
Research ideation and distillation system...

## Key Concepts
...
(entire markdown spec)
```

### transcribe
```
>>> transcribe /path/to/audio.wav
Transcribing /path/to/audio.wav...
Added to transcript buffer:
the transcribed text from the audio file
```

Or if file not found:
```
>>> transcribe /nonexistent/file.wav
File not found: /nonexistent/file.wav
```

### process
```
>>> process some text to process
Processing "some text to process" in CREATIVE mode...
Processing complete (backend: claude)
Spec updated.
```

### mode
```
>>> mode distillation
Switched to DISTILLATION mode
```

### exit
```
>>> exit
(program terminates)
```

---

## src/client.py (Interactive mode)

**Purpose**: Remote HTTP client for accessing DGX API from laptop

**Invocation**:
```bash
python -m src.client <dgx-hostname>
```

Example:
```bash
python -m src.client dgx-spark.example.com
```

**What It Does**:
1. Creates Block1Client instance pointing to DGX host
2. Checks connection to /health endpoint
3. Enters interactive loop
4. Sends HTTP requests to DGX server
5. Displays responses to user

**Expected Output** (startup):
```
Block 1 Remote Client
==================================================
Connected to DGX (sess-abc123xyz789)
Mode: CREATIVE
Transcript chunks: 5
```

Then shows command prompt (implementation depends on cli.py)

**If connection fails**:
```
Block 1 Remote Client
==================================================
Failed to connect to DGX at dgx-spark.example.com: Connection refused
```

**File Access**:
- Can be imported as client library:
```python
from src.client import Block1Client
client = Block1Client("dgx-host", 8001)
status = client.status()
tasks = client.list_progress(source="phone")
```

---

## src/state_manager.py (Used by other scripts)

**Purpose**: Manage reading/writing system state and specs

**Invocation** (not typically run directly):
```python
from src.state_manager import StateManager

state_mgr = StateManager(
    state_dir="./state",
    specs_dir="./specs"
)

# Load current state
state = state_mgr.load_state()

# Add transcript
state_mgr.append_transcript("text", source="phone", duration=45.2)

# Save spec
state_mgr.save_spec("# New Spec\n...")
```

**What It Does**:
- Loads/saves `./state/current.json` (SystemState)
- Loads/saves `./specs/spec.md` (markdown)
- Appends transcript chunks atomically
- Manages session state persistence

**Files Created** (if don't exist):
- `./state/current.json` - Default empty state
- `./specs/spec.md` - Default empty spec
- `./state/` and `./specs/` directories

**Expected Behavior**:
- On first load: creates directories and default files
- On subsequent loads: reads existing JSON/Markdown
- On save: writes temp file first, renames atomically (no partial writes)

---

## src/progress_manager.py (Used by other scripts)

**Purpose**: Track processing tasks through the pipeline

**Invocation** (not typically run directly):
```python
from src.progress_manager import ProgressManager

prog_mgr = ProgressManager(progress_dir="./state")

# Create task
task = prog_mgr.create_task(
    filename="audio.wav",
    source="phone",
    file_size_bytes=2456789,
    mode="creative"
)

# Update status
prog_mgr.update_task_status(task.task_id, TaskStatus.TRANSCRIBING)

# Get stats
stats = prog_mgr.get_statistics()
```

**What It Does**:
- Creates ProcessingTask with unique ID
- Updates task status through pipeline
- Persists tasks to `./state/tasks.json`
- Provides filtering and statistics

**Files Created**:
- `./state/tasks.json` - Array of ProcessingTask objects

**Expected Behavior**:
- Loads existing tasks on init
- Creates/updates on operation
- All changes saved atomically to disk

---

## src/semantic_engine.py (Used by other scripts)

**Purpose**: Process transcripts through LLM (Claude or DGX)

**Invocation** (not typically run directly):
```python
from src.semantic_engine import SemanticEngine

engine = SemanticEngine(
    claude_api_key="sk-...",
    claude_model="claude-3-5-haiku-20241022",
    dgx_base_url="http://dgx:8000",
    dgx_model="local-llm"
)

# Process transcript
updated_spec, backend = engine.process_transcript(
    mode="creative",
    transcript_text="the new transcript",
    current_spec="# Current spec",
    transcript_history="history of all transcripts"
)
```

**What It Does**:
1. Tries Claude API first (with configured API key)
2. On failure or rate-limit, falls back to DGX LLM
3. Sends mode-specific system prompt
4. Returns updated spec + backend name

**Expected Output**:
- Returns tuple: (updated_spec_markdown, backend_name)
- backend_name is either "claude" or "dgx"

**Failure Modes**:
- Raises exception if both Claude and DGX fail
- Logs error with details

---

## src/transcription_service.py (Used by other scripts)

**Purpose**: Call DGX Whisper API to transcribe audio

**Invocation** (not typically run directly):
```python
from src.transcription_service import TranscriptionService

service = TranscriptionService(
    dgx_base_url="http://dgx:8000",
    whisper_model="whisper-1"
)

# Transcribe file
text = service.transcribe("/path/to/audio.wav")
```

**What It Does**:
1. Reads audio file from disk
2. Makes HTTP POST to `{dgx_base_url}/v1/audio/transcriptions`
3. Sends file content
4. Returns transcribed text

**Expected Output**:
- Returns string with transcribed text
- Returns None if file not found or request fails
- Logs errors with details

---

## src/__init__.py

**Purpose**: Makes src/ a Python package

**Invocation**: Not invoked directly (automatic import)

**What It Does**: 
- Empty file that allows `from src.module import ...`

---

## Expected File Structure After Running

After running various scripts, you should see:

```
Chat2Plan/
├── state/
│   ├── current.json          (SystemState)
│   ├── current.json.tmp      (temp, gets cleaned up)
│   ├── tasks.json            (ProcessingTask array)
│   └── tasks.json.tmp        (temp, gets cleaned up)
│
├── specs/
│   ├── spec.md               (Living markdown spec)
│   └── spec.md.tmp           (temp, gets cleaned up)
│
└── recordings/
    ├── audio1.wav            (Downloaded/temporary)
    ├── research_notes.m4a
    └── brainstorm.mp3
```

---

## Summary Table

| Script | Invocation | Mode | Output Type | Main Files |
|--------|-----------|------|------------|-----------|
| main.py | `python main.py` | Sync | CLI loop | None (uses existing) |
| api_server.py | `python -m src.api_server` | Sync | HTTP server | Modifies via API |
| file_watcher.py | `python -m src.file_watcher` | Async | Logs | state/, specs/ |
| cli.py | Via main.py | Sync | Interactive | Modifies via CLI |
| client.py | `python -m src.client HOST` | Sync | Remote CLI | None (reads from API) |
| state_manager.py | Import only | N/A | API | state/, specs/ |
| progress_manager.py | Import only | N/A | API | state/tasks.json |
| semantic_engine.py | Import only | N/A | API | None (returns text) |
| transcription_service.py | Import only | N/A | API | recordings/ |

---

## Typical Deployment

**DGX (Production)**:
```bash
# Terminal 1: API Server
python -m src.api_server

# Terminal 2: File Watcher
python -m src.file_watcher
```

**Laptop (Interactive)**:
```bash
# Local testing
python main.py

# Remote access when online
python -m src.client dgx-hostname
```

**Phone**:
- Record audio
- Upload to OneDrive `Chat2Plan/recordings/`
- (DGX auto-processes via file watcher)

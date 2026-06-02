# Service Interactions

## Overview

This document describes how the different services interact with each other, the order of operations, and dependencies between components.

---

## Service Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│               EXTERNAL DEPENDENCIES                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Claude API (Anthropic)                                │
│  DGX Whisper API (vLLM)                                │
│  DGX LLM API (vLLM)                                    │
│  OneDrive Sync                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
            ↓                    ↓              ↓
     ┌──────────────┐    ┌──────────────┐    ┌────────────┐
     │ Transcription│    │   Semantic   │    │   File     │
     │  Service     │    │   Engine     │    │  System    │
     └──────────────┘    └──────────────┘    └────────────┘
            ↓                    ↓              ↓
     ┌──────────────────────────────────────────────────┐
     │            STATE MANAGER                         │
     │  (Reads/Writes JSON & Markdown)                  │
     └──────────────────────────────────────────────────┘
            ↓                    ↓
     ┌──────────────┐    ┌──────────────┐
     │  Progress    │    │  API Server  │
     │  Manager     │    │ (FastAPI)    │
     └──────────────┘    └──────────────┘
            ↓                    ↓
     ┌──────────────────────────────────────────────────┐
     │          CLIENTS & FILE WATCHER                  │
     │  (CLI, HTTP Client, File Watcher)                │
     └──────────────────────────────────────────────────┘
```

---

## Component Interactions

### 1. TranscriptionService

**Responsibilities**:
- Call DGX Whisper API
- Receive audio files
- Return transcribed text

**Dependencies**:
- `DGX_BASE_URL` configuration
- `DGX_API_KEY` configuration
- `WHISPER_MODEL` configuration

**Interaction Points**:
- Called by: FileWatcher, API Server, CLI
- Calls: DGX `/v1/audio/transcriptions` endpoint

**Method**: `TranscriptionService.transcribe(audio_file_path)`

**Input**: File path to .wav, .mp3, .m4a, .ogg, or .flac

**Output**: String with transcribed text, or None if failed

**Side Effects**: None (read-only)

**Example Flow**:
```
audio.wav → TranscriptionService.transcribe() 
         → HTTP POST /v1/audio/transcriptions
         → DGX returns {"text": "..."}
         → Returns text to caller
```

---

### 2. SemanticEngine

**Responsibilities**:
- Process transcripts through LLM
- Determine which backend to use (Claude vs DGX)
- Update specification markdown
- Apply mode-specific logic

**Dependencies**:
- `CLAUDE_API_KEY` configuration
- `CLAUDE_MODEL` configuration
- `DGX_BASE_URL` configuration
- `DGX_MODEL` configuration

**Interaction Points**:
- Called by: FileWatcher, API Server, CLI
- Calls: Claude API or DGX LLM API

**Method**: `SemanticEngine.process_transcript(mode, transcript_text, current_spec, transcript_history)`

**Inputs**:
- `mode` (str): "creative" or "distillation"
- `transcript_text` (str): New transcript to process
- `current_spec` (str): Existing markdown spec
- `transcript_history` (str): Full history of transcripts

**Output**: Tuple of (updated_spec_markdown, backend_name)

**Backend Selection**:
1. Try Claude API first
2. If Claude fails/times out, fall back to DGX LLM
3. Return which backend was used

**Example Flow**:
```
transcript → SemanticEngine.process_transcript()
          → Try Claude API
          → Success? Return (new_spec, "claude")
          → Timeout/error? Try DGX fallback
          → Return (new_spec, "dgx")
```

---

### 3. StateManager

**Responsibilities**:
- Load/save SystemState (JSON)
- Load/save Markdown spec
- Append transcript chunks
- Manage atomic file operations

**Dependencies**:
- File system access
- `STATE_DIR` and `SPECS_DIR` configuration

**Interaction Points**:
- Called by: All components that modify state
- Reads/writes: `./state/current.json`, `./specs/spec.md`

**Key Methods**:
- `load_state()` → SystemState
- `save_state(state)` → None
- `load_spec()` → str (markdown)
- `save_spec(markdown)` → None
- `append_transcript(text, source, duration)` → None

**Atomic Operations**:
```
Write to temp file (.tmp)
    ↓
Verify write successful
    ↓
Rename temp → original (atomic on OS level)
    ↓
Return success
```

This prevents partial/corrupted writes.

**Example Flow**:
```
FileWatcher detected audio
    → TranscriptionService.transcribe() → "text"
    → StateManager.append_transcript("text", "phone")
       → Load current state
       → Add chunk to buffer
       → Save state with temp+rename
    → SemanticEngine.process_transcript()
       → StateManager.load_spec()
       → Returns updated spec
    → StateManager.save_spec(new_spec)
       → Write temp → rename
```

---

### 4. ProgressManager

**Responsibilities**:
- Create ProcessingTask objects
- Update task status through pipeline
- Persist tasks to disk
- Provide statistics and filtering

**Dependencies**:
- File system access
- `STATE_DIR` configuration

**Interaction Points**:
- Called by: FileWatcher, API Server
- Reads/writes: `./state/tasks.json`

**Key Methods**:
- `create_task(filename, source, ...)` → ProcessingTask
- `update_task_status(task_id, status, **metadata)` → ProcessingTask
- `get_task(task_id)` → ProcessingTask
- `list_tasks(source, limit)` → List[ProcessingTask]
- `get_statistics()` → Dict

**Example Flow**:
```
FileWatcher detects audio.wav
    → ProgressManager.create_task("audio.wav", "phone")
       → task_id = "a1b2c3d4"
       → Write to tasks.json
    → ProgressManager.update_task_status(task_id, TRANSCRIBING)
    → (transcription happens)
    → ProgressManager.update_task_status(task_id, PROCESSING, transcript_text="...", transcript_length=4521)
    → (semantic processing happens)
    → ProgressManager.update_task_status(task_id, COMPLETED, spec_updated=True, backend_used="claude")
```

---

### 5. FileWatcher

**Responsibilities**:
- Monitor OneDrive recordings folder
- Detect new audio files
- Orchestrate full processing pipeline
- Update progress and state

**Dependencies**:
- `ONEDRIVE_RECORDINGS_PATH` configuration
- TranscriptionService
- StateManager
- SemanticEngine
- ProgressManager

**Interaction Points**:
- Runs continuously (daemon)
- Reads: Audio files from OneDrive
- Writes: State via StateManager, Progress via ProgressManager

**Orchestration Sequence**:
```
1. File appears in OneDrive/recordings/
2. FileWatcher.on_created() triggered
3. Create task (ProgressManager)
4. Wait 1 second (file write completion)
5. Update status: UPLOADING
6. Update status: TRANSCRIBING
7. Call TranscriptionService.transcribe()
8. Update status: PROCESSING
9. Add to StateManager transcript buffer
10. Call SemanticEngine.process_transcript()
11. Call StateManager.save_spec()
12. Update status: COMPLETED (or FAILED)
```

---

### 6. API Server

**Responsibilities**:
- Expose HTTP endpoints
- Route requests to appropriate services
- Return JSON responses
- Create tasks for uploads
- Serve state data

**Dependencies**:
- FastAPI framework
- All other services (state_manager, semantic_engine, etc.)

**Interaction Points**:
- Listens on port 8001
- Calls: StateManager, SemanticEngine, TranscriptionService, ProgressManager

**Endpoints & Service Calls**:

```
GET /health
    → StateManager.load_state()
    → Return session_id

GET /status
    → StateManager.load_state()
    → StateManager.load_spec()
    → Return summary

GET /spec
    → StateManager.load_spec()
    → Return markdown

POST /transcribe (upload)
    → ProgressManager.create_task()
    → ProgressManager.update_task_status(UPLOADING)
    → Save file
    → TranscriptionService.transcribe()
    → ProgressManager.update_task_status(PROCESSING)
    → StateManager.append_transcript()
    → SemanticEngine.process_transcript()
    → ProgressManager.update_task_status(COMPLETED)
    → Return task_id + transcript

POST /process
    → StateManager.append_transcript()
    → SemanticEngine.process_transcript()
    → StateManager.save_spec()
    → Return updated spec

GET /progress/{task_id}
    → ProgressManager.get_task()
    → Return task details

GET /progress
    → ProgressManager.list_tasks()
    → Return filtered list

GET /progress/stats
    → ProgressManager.get_statistics()
    → Return aggregate stats
```

---

### 7. CLI & Clients

**Responsibilities**:
- Provide user interface (interactive or HTTP)
- Call appropriate services
- Display results

**Dependencies**:
- StateManager, SemanticEngine, etc. (CLI)
- Network access to API Server (HTTP client)

**Interaction Points**:

**CLI (main.py)**:
```
User input "process some text"
    → StateManager.append_transcript()
    → SemanticEngine.process_transcript()
    → StateManager.save_spec()
    → Display results
```

**HTTP Client**:
```
User input "process some text"
    → HTTP POST /process
    → API Server routes to endpoints above
    → Return response
    → Display results
```

---

## Data Flow Scenarios

### Scenario 1: Phone Recording via OneDrive

```
Phone                               DGX
 │                                  │
 ├─ Record audio                    │
 │  "research_notes.m4a"            │
 │                                  │
 ├─ Upload to OneDrive              │
 │  /Chat2Plan/recordings/          │
 │                                  │
 │  ┌────────────────────────────→  │ FileWatcher
 │  │                               │ ├─ on_created()
 │  │                               │ ├─ ProgressManager.create_task()
 │  │                               │ ├─ TranscriptionService.transcribe()
 │  │                               │ │  → DGX Whisper API
 │  │                               │ ├─ StateManager.append_transcript()
 │  │                               │ ├─ SemanticEngine.process_transcript()
 │  │                               │ │  → Claude API
 │  │                               │ ├─ StateManager.save_spec()
 │  │                               │ ├─ ProgressManager.update_task()
 │  │                               │
 │  ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ← OneDrive syncs results
 │
 └─ Read /Chat2Plan/specs/spec.md
    (Updated spec available offline)
```

### Scenario 2: Laptop Upload via API

```
Laptop                              DGX
 │                                  │
 ├─ Record audio                    │
 │  "brainstorm.wav"                │
 │                                  │
 ├─ HTTP POST /transcribe           │
 │  (multipart file upload)         │
 │                 ┌────────────→   │ API Server
 │                 │                │ ├─ ProgressManager.create_task()
 │                 │                │ ├─ ProgressManager.update_task(UPLOADING)
 │                 │                │ ├─ Save to ./recordings/
 │                 │                │ ├─ ProgressManager.update_task(TRANSCRIBING)
 │                 │                │ ├─ TranscriptionService.transcribe()
 │                 │                │ ├─ StateManager.append_transcript()
 │                 │                │ ├─ ProgressManager.update_task(PROCESSING)
 │                 │                │ ├─ SemanticEngine.process_transcript()
 │                 │                │ ├─ StateManager.save_spec()
 │                 │                │ ├─ ProgressManager.update_task(COMPLETED)
 │                 │                │
 │ ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
 │ {task_id, transcript, duration}  │
 │                                  │
 ├─ Poll GET /progress/{task_id}    │
 │  (check if still processing)     │
 │                 ┌────────────→   │
 │ ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
 │ {status, backend_used, ...}      │
 │                                  │
 └─ When online, sync with OneDrive
    and pull spec
```

### Scenario 3: Client Checking Progress

```
Laptop (offline)                    DGX
 │                                  │
 ├─ (Later, when online)            │
 │ GET /progress/stats              │
 │              ┌──────────────→    │
 │ ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
 │ {total: 156, completed: 148, ...}│
 │                                  │
 ├─ GET /progress?source=laptop     │
 │              ┌──────────────→    │
 │ ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
 │ {tasks: [...], active_count: 2}  │
 │                                  │
 └─ GET /spec                       │
    (pull latest spec)              │
```

---

## Error Handling Flow

### Transcription Failure

```
TranscriptionService.transcribe()
    → DGX Whisper API call fails (timeout, etc.)
    → Returns None
    ↓
FileWatcher.on_created() catches exception
    → ProgressManager.update_task_status(FAILED, error_message="Transcription timeout")
    ↓
Task marked FAILED in tasks.json
Error visible in GET /progress/{task_id}
```

### LLM Processing Failure

```
SemanticEngine.process_transcript()
    → Try Claude API
    → Claude fails (rate limit, API error, etc.)
    → Fall back to DGX LLM
    → DGX fails (timeout, model not available)
    → Both fail
    ↓
Exception raised
    ↓
Caller (FileWatcher or API) catches
    → ProgressManager.update_task_status(FAILED, error_message="Both Claude and DGX failed")
    ↓
Task marked FAILED
Spec NOT updated
```

### File System Failure

```
StateManager.save_state()
    → Write to temp file
    → File system full / permission error
    → Exception raised
    ↓
Caller catches and logs
    ↓
State NOT persisted
Next reload gets stale data
(Consider adding retry logic or alerts)
```

---

## Service Lifetimes

### API Server (`src/api_server.py`)
- **Lifetime**: Long-running (days/weeks)
- **Startup**: Initialize all services once
- **Shutdown**: Clean up gracefully
- **Concurrency**: Handles multiple concurrent requests

### File Watcher (`src/file_watcher.py`)
- **Lifetime**: Long-running (days/weeks)
- **Startup**: Load tasks from disk, start observer
- **Shutdown**: Stop observer, flush pending tasks
- **Concurrency**: Processes files sequentially (one at a time)

### CLI (`python main.py`)
- **Lifetime**: User session (minutes to hours)
- **Startup**: Initialize services, show prompt
- **Shutdown**: User types exit or Ctrl+C
- **Concurrency**: Synchronous user input/output

### HTTP Client (`python -m src.client`)
- **Lifetime**: User session (minutes to hours)
- **Startup**: Connect to API server
- **Shutdown**: User types exit or Ctrl+C
- **Concurrency**: Sequential requests

---

## Consistency & Race Conditions

### State Consistency

**Strategy**: Atomic file operations (temp file + rename)

```
Save state:
  1. Write all data to ./state/current.json.tmp
  2. If write successful, rename .tmp → .json (atomic)
  3. If write fails, .tmp is deleted, .json untouched

This prevents:
  - Partial writes (crash during write)
  - Corrupted state (concurrent writes)
  - Data loss on power failure
```

### Task Ordering

**Potential Issue**: File watcher processes two recordings simultaneously?

**Current**: Watchdog is single-threaded per directory, so files processed sequentially.

**Recommendation**: If enabling async processing, use task queue (Redis, Celery) to ensure FIFO.

### Progress Tracking

**Race Condition**: FileWatcher and API both update same task?

**Current**: No - tasks created by one source (phone via watcher OR laptop via API).

**Recommendation**: Still safe to handle concurrent updates (last-write-wins on task.json).

---

## Performance Characteristics

### Service Response Times

| Service | Operation | Typical Duration |
|---------|-----------|-----------------|
| TranscriptionService | 1 min audio | 10-15 sec |
| SemanticEngine (Claude) | 4KB transcript | 15-45 sec |
| SemanticEngine (DGX LLM) | 4KB transcript | 20-60 sec |
| StateManager | Save state | <100 ms |
| ProgressManager | Update task | <100 ms |
| FileWatcher | End-to-end | 1-3 min |
| API Server | /health | <10 ms |
| API Server | /progress/stats | <50 ms |

### Concurrency Limits

- **API Server**: Limited by uvicorn worker count (configurable, default 4)
- **File Watcher**: Single-threaded (one file at a time)
- **StateManager**: Atomic writes prevent corruption, but not optimized for high write frequency
- **ProgressManager**: Same as StateManager

**Bottleneck**: If many files arrive simultaneously, file watcher will queue them sequentially.

---

## Future Enhancement Points

1. **Async Processing**: Use task queue (Celery/RQ) for parallel transcription/processing
2. **Caching**: Cache LLM responses for similar transcripts
3. **Webhooks**: Notify clients when tasks complete instead of polling
4. **Database**: Replace JSON files with proper database (SQLite/PostgreSQL)
5. **Metrics**: Add Prometheus metrics for monitoring
6. **Batching**: Group multiple short transcripts into single LLM call
7. **Load Balancing**: Distribute across multiple DGX instances

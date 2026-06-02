# Block 1 System Architecture

## System Overview

Block 1 is a dual-phase semantic planning system that transforms voice/text ideation into structured evolving specifications. The system separates creative exploration from structured consolidation, with automatic processing of recordings from both phone and laptop devices.

## Core Principles

1. **Separation of Concerns**: Creative thinking (divergence) vs. Consolidation (convergence)
2. **Automated Pipeline**: File detection → Transcription → Processing → Spec Update
3. **Hybrid Processing**: Cloud (Claude API) primary, Local LLM (DGX) fallback
4. **Central Hub**: OneDrive as sync point for all recordings across devices
5. **Progress Tracking**: Full visibility into processing pipeline for each file

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phone (iOS/Android)    Laptop (Windows/Mac)    Direct API     │
│  Voice Memos            Voice Recorder          HTTP Upload     │
│       ↓                        ↓                       ↓        │
│  OneDrive Auto-Sync    OneDrive Save         /transcribe POST  │
│       └──────────────────────┬──────────────────────┘          │
│                              ↓                                  │
│                 OneDrive/Chat2Plan/recordings/                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│              DETECTION & TRACKING LAYER (DGX)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  File Watcher (watchdog)                                       │
│       ↓                                                         │
│  Progress Manager → Create Task with ID                        │
│       ↓                                                         │
│  State Persistence (./state/tasks.json)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│            PROCESSING PIPELINE LAYER (DGX)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Transcription Service (Whisper)                            │
│     Audio File → Text Transcript                              │
│                  ↓                                             │
│  2. Semantic Engine                                            │
│     Transcript → Process → LLM Decision                       │
│                  ↓                                             │
│     Primary: Claude API (Haiku)                               │
│     Fallback: DGX Local LLM                                   │
│                  ↓                                             │
│  3. State Manager                                              │
│     Update Spec + Save State                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│              OUTPUT & SYNC LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  State Files (./state/)                                        │
│  ├─ current.json (system state)                               │
│  ├─ tasks.json (progress tracking)                            │
│                                                                 │
│  Spec Files (./specs/)                                         │
│  └─ spec.md (living markdown spec)                            │
│                                                                 │
│  OneDrive Sync (auto)                                          │
│  └─ Results available on all devices                          │
│                                                                 │
│  FastAPI Server (port 8001)                                    │
│  ├─ /progress endpoints                                       │
│  ├─ /spec, /transcript endpoints                              │
│  └─ /transcribe upload endpoint                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│               CLIENT ACCESS LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phone & Laptop (offline access)                               │
│  └─ OneDrive/Chat2Plan/specs/spec.md                          │
│                                                                 │
│  Laptop (when online)                                          │
│  └─ Client CLI → HTTP → DGX API Server                        │
│                                                                 │
│  External Agents                                               │
│  └─ Read docs/ markdown → Modify codebase                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Input Layer
- **Phone/Laptop**: Capture audio via device apps
- **OneDrive**: Auto-sync recordings to cloud storage
- **File System**: Mount OneDrive folder on DGX for monitoring

### Detection & Tracking Layer
- **FileWatcher**: Monitor for new audio files (watchdog library)
- **ProgressManager**: Create task records, persist to disk
- **Task IDs**: Unique identifier for each file through pipeline

### Processing Pipeline
- **TranscriptionService**: Call DGX Whisper API to convert audio → text
- **StateManager**: Manage transcript buffer, spec markdown, system state
- **SemanticEngine**: Process transcript through Claude or DGX LLM
- **Mode Logic**: Apply Creative vs Distillation mode rules

### Output & Sync
- **State Persistence**: JSON files in ./state/ directory
- **Spec Management**: Living markdown in ./specs/spec.md
- **API Server**: FastAPI for remote access and uploads
- **OneDrive Sync**: Files sync automatically to devices

### Client Access
- **CLI Client**: Interactive terminal interface for laptop
- **API Client**: HTTP requests from remote devices
- **File Access**: Direct OneDrive access for offline reading

## Data Flow

### Synchronous Flow (Direct API Upload)
```
HTTP POST /transcribe
    ↓
Create Task (status: queued)
    ↓
Save to recordings/ dir
    ↓
Transcribe (status: transcribing)
    ↓
Process through semantic engine (status: processing)
    ↓
Update spec (status: completed)
    ↓
Return response with task_id
```

### Asynchronous Flow (OneDrive File Watcher)
```
New file detected in OneDrive/recordings/
    ↓
Create Task (status: queued)
    ↓
Wait for file to finish writing (1 sec)
    ↓
Transcribe (status: transcribing)
    ↓
Add to transcript buffer
    ↓
Process through semantic engine (status: processing)
    ↓
Update spec
    ↓
Update task status (completed/failed)
    ↓
OneDrive syncs results back to devices
```

## Key Design Decisions

1. **OneDrive as Hub**: Centralizes recordings, handles sync, enables offline access
2. **Local Transcription**: Audio stays private, only sends text to Claude
3. **Task-Based Tracking**: Each file gets unique ID, full state tracking
4. **Persistent Progress**: Tasks saved to disk, survive server restarts
5. **Hybrid Processing**: Cost efficiency (Haiku) with fallback reliability
6. **Stateless LLM**: Semantic engine doesn't maintain state, uses transcript buffer
7. **Atomic File Operations**: State changes use temp files + rename for durability

## File Organization

```
Chat2Plan/
├── src/
│   ├── __init__.py
│   ├── api_server.py           # FastAPI server (HTTP endpoints)
│   ├── cli.py                  # CLI interactive loop
│   ├── client.py               # Client for remote access
│   ├── file_watcher.py         # File detection & processing
│   ├── models.py               # Data structures
│   ├── progress_manager.py     # Task tracking
│   ├── semantic_engine.py      # LLM processing
│   ├── state_manager.py        # JSON + Markdown persistence
│   ├── transcription_service.py # Whisper API client
│   └── docs/                   # DOCUMENTATION (YOU ARE HERE)
│       ├── ARCHITECTURE.md     # System design
│       ├── DATA_MODELS.md      # Expected structures
│       ├── SCRIPTS.md          # Script purposes & outputs
│       ├── API_SPEC.md         # API endpoints
│       ├── SERVICES.md         # Service interactions
│       └── WORKFLOWS.md        # Complete workflows
│
├── state/                      # Runtime state (git-ignored)
│   ├── current.json           # System state
│   └── tasks.json             # Task progress
│
├── specs/                      # Output specifications
│   └── spec.md                # Living markdown spec
│
├── recordings/                 # Downloaded/temporary audio
│   └── <audio-files>
│
├── main.py                     # Entry point
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # User-facing documentation
```

## Configuration

All system configuration via `.env` file:

**DGX Endpoints**
- `DGX_BASE_URL` - Whisper API location
- `DGX_API_KEY` - Authentication
- `DGX_TIMEOUT` - Request timeout (seconds)

**Claude API (Primary)**
- `CLAUDE_API_KEY` - Anthropic API key
- `CLAUDE_MODEL` - Model name (claude-3-5-haiku-20241022)
- `CLAUDE_TIMEOUT` - Request timeout (seconds)

**Whisper Transcription**
- `WHISPER_MODEL` - Model identifier
- `WHISPER_ENDPOINT` - API path

**Local Paths**
- `STATE_DIR` - Where to save JSON state
- `SPECS_DIR` - Where to save markdown specs
- `RECORDINGS_DIR` - Temp audio storage
- `ONEDRIVE_RECORDINGS_PATH` - OneDrive folder to watch

**Server**
- `API_HOST` - FastAPI bind address
- `API_PORT` - FastAPI port (default 8001)

## Deployment Modes

### Mode 1: CLI Only (Local Testing)
```bash
python main.py
```
Interactive terminal loop on development machine.

### Mode 2: File Watcher + API (Production DGX)
**Terminal 1:**
```bash
python -m src.api_server
```
REST API server on port 8001.

**Terminal 2:**
```bash
python -m src.file_watcher
```
Background file monitoring and auto-processing.

### Mode 3: Client Remote Access (Laptop)
```bash
python -m src.client <dgx-hostname>
```
Connect to DGX API server from online device.

## Performance Targets

| Operation | Target Duration |
|-----------|-----------------|
| Phone → OneDrive sync | 1-3 min |
| File detection | 5-10 sec |
| Transcription (1 min audio) | 10-15 sec |
| Semantic processing | 15-45 sec |
| **Total pipeline** | **1-3 minutes** |

## Security Considerations

1. **API Key Management**: Store in .env, never commit
2. **Audio Privacy**: Local transcription, no external audio upload
3. **OneDrive Access**: Requires configured sync, credential-based
4. **API Authentication**: DGX API key optional (local dummy-key for dev)
5. **State Files**: Local file system, no encryption (recommended for future)

## Error Handling & Recovery

- **Transcription Failure**: Task marked failed, error captured, continues
- **LLM Failure**: Automatic fallback (Claude → DGX), error logged
- **File Sync Timeout**: Retried by watchdog, task updated when successful
- **Spec Collision**: Atomic operations (temp file + rename) prevent corruption
- **Task Persistence**: Survives server restart, can retry from last state

# Complete Workflows

## Overview

This document describes end-to-end workflows showing how all components work together to accomplish specific tasks. Each workflow shows the sequence of operations, services involved, state changes, and expected outputs.

---

## Workflow 1: Phone Recording Detection & Auto-Processing

**Goal**: Record audio on phone, upload to OneDrive, automatically process and update spec

**Participants**: Phone, OneDrive, DGX File Watcher, Services, State Files

**Duration**: 1-3 minutes (phone sync + DGX processing)

### Step-by-Step Flow

**Phase 1: Phone Recording (User)**

```
1. Open Voice Memos app
2. Press record
3. Speak research ideas (45 seconds)
4. Press stop
5. Name recording "research_notes"
6. Export to OneDrive
   - Menu → Share → OneDrive
   - Navigate to: Chat2Plan/recordings/
   - Upload
```

**Expected Phone State**:
- Recording file: `research_notes.m4a`
- Location: `OneDrive/Chat2Plan/recordings/`
- Status: Syncing to DGX

**Phase 2: OneDrive Sync (Automatic)**

```
Time: T + 1-3 minutes (depending on file size & network)

File present on DGX at:
/mnt/onedrive/Chat2Plan/recordings/research_notes.m4a
```

**Phase 3: File Watcher Detection**

```
Time: T + 1-3 min 5-10 sec

File watcher observing: /mnt/onedrive/Chat2Plan/recordings/

1. Watchdog detects new file
2. Event handler triggered: on_created()
3. Parse filename: "research_notes.m4a"

STATE CHANGE:
  ProgressManager.create_task(
    filename="research_notes.m4a",
    source="phone",
    file_size_bytes=2456789,
    mode="creative"
  )
  → task_id = "a1b2c3d4"

ACTION: Write to ./state/tasks.json
{
  "task_id": "a1b2c3d4",
  "filename": "research_notes.m4a",
  "source": "phone",
  "status": "queued",
  "created_at": "2026-06-02T10:15:23.123456",
  ...
}

OUTPUT: Logged to console
[Progress] Task a1b2c3d4 created for research_notes.m4a
[FileWatcher] New audio file detected: research_notes.m4a
```

**Phase 4: Wait for File Write**

```
Time: T + 1-3 min 6 sec

File is still being written to disk
→ Wait 1 second for sync to complete
```

**Phase 5: Transcription**

```
Time: T + 1-3 min 7 sec

STATE CHANGE:
  ProgressManager.update_task_status(
    task_id="a1b2c3d4",
    status=TRANSCRIBING
  )

ACTION: Update ./state/tasks.json
  status: "transcribing"
  started_at: "2026-06-02T10:15:24.234567"

OUTPUT:
[Progress] Task a1b2c3d4: transcribing
[FileWatcher] Transcribing research_notes.m4a...

OPERATION: TranscriptionService.transcribe()
  Input: /mnt/onedrive/Chat2Plan/recordings/research_notes.m4a
  
  HTTP POST http://dgx:8000/v1/audio/transcriptions
  {
    "file": <binary audio data>,
    "model": "whisper-1"
  }
  
  DGX Whisper processes (10-15 seconds)
  
  Response:
  {
    "text": "we need to think about how to structure the semantic planning system..."
  }

OUTPUT:
[FileWatcher] Transcription complete: 4521 characters
```

**Phase 6: Semantic Processing**

```
Time: T + 1-3 min 22 sec

STATE CHANGE:
  StateManager.append_transcript(
    text="we need to think about...",
    source="phone",
    duration=45.2
  )

ACTION: Update ./state/current.json
  transcript_buffer:
    [
      {...existing chunks...},
      {
        "text": "we need to think about...",
        "source": "phone",
        "timestamp": "2026-06-02T10:15:24.567890",
        "duration_seconds": 45.2
      }
    ]

STATE CHANGE:
  ProgressManager.update_task_status(
    task_id="a1b2c3d4",
    status=PROCESSING,
    transcript_text="we need to think about...",
    transcript_length=4521
  )

ACTION: Update ./state/tasks.json
  status: "processing"
  transcript_text: "we need to think about..."
  transcript_length: 4521

OUTPUT:
[Progress] Task a1b2c3d4: processing
[FileWatcher] Processing in CREATIVE mode...

OPERATION: SemanticEngine.process_transcript()
  Input:
    mode: "creative"
    transcript_text: "we need to think about..."
    current_spec: "# Block 1 Specification\n..."
    transcript_history: "full history of all transcripts"
  
  Try Claude API:
    HTTP POST https://api.anthropic.com/v1/messages
    {
      "model": "claude-3-5-haiku-20241022",
      "system": "You are a semantic planning engine in CREATIVE mode...",
      "messages": [{...}]
    }
    
    Claude processes (15-45 seconds)
    
    Response: Updated markdown spec
  
  Output:
    updated_spec: "# Block 1 Specification\n\n## Overview\n...\n\n## New Ideas\nFrom latest recording:\n- system structure considerations\n- semantic planning approach\n..."
    backend: "claude"

OUTPUT:
[FileWatcher] Processing in CREATIVE mode...
```

**Phase 7: Spec Update**

```
Time: T + 1-3 min 52 sec

STATE CHANGE:
  StateManager.save_spec(updated_spec)

ACTION: Write to ./specs/spec.md
  Content: Updated markdown from semantic engine
  Method: Write temp file → Rename atomically

Simultaneously:
  StateManager.save_state(updated_state)
  
ACTION: Update ./state/current.json
  current_spec_markdown: (updated)
  version: 16 (incremented)
  last_updated: "2026-06-02T10:16:45.456789"

STATE CHANGE:
  ProgressManager.update_task_status(
    task_id="a1b2c3d4",
    status=COMPLETED,
    spec_updated=True,
    backend_used="claude"
  )

ACTION: Update ./state/tasks.json
  status: "completed"
  completed_at: "2026-06-02T10:16:45.456789"
  spec_updated: true
  backend_used: "claude"

OUTPUT:
[FileWatcher] Spec updated (backend: claude)
[Progress] Task a1b2c3d4: completed
```

**Phase 8: Sync Back to Phone**

```
Time: T + 1-3 min 55 sec - T + 5 min

OneDrive automatically syncs updated files back:

Updated files:
  /OneDrive/Chat2Plan/specs/spec.md (new content)
  /OneDrive/Chat2Plan/state/tasks.json (new task entry)

Available on phone for:
  - Offline reading of spec.md
  - Checking task status (via tasks.json)
```

### Summary of State Changes

```
State File: ./state/current.json
  - transcript_buffer: Added new chunk
  - current_spec_markdown: Updated with new ideas
  - version: Incremented to 16
  - last_updated: Updated timestamp

State File: ./state/tasks.json
  - New entry added:
    {
      "task_id": "a1b2c3d4",
      "filename": "research_notes.m4a",
      "source": "phone",
      "status": "completed",
      "created_at": "2026-06-02T10:15:23.123456",
      "started_at": "2026-06-02T10:15:24.234567",
      "completed_at": "2026-06-02T10:16:45.456789",
      "file_size_bytes": 2456789,
      "duration_seconds": 45.2,
      "transcript_text": "we need to think about...",
      "transcript_length": 4521,
      "spec_updated": true,
      "error_message": "",
      "mode": "creative",
      "backend_used": "claude"
    }

Spec File: ./specs/spec.md
  - Entire content replaced with updated version
  - Now includes ideas from this recording
  - Version history: Manual (use git for tracking)

Recording Files: ./recordings/ (optional)
  - Copy of downloaded m4a file
```

### How to Monitor Progress

**Real-time Monitoring (on DGX)**:
```bash
# Terminal 1: Watch logs
tail -f <file_watcher_output>

# Terminal 2: Check task status
curl http://localhost:8001/progress/a1b2c3d4

# Terminal 3: Watch state file
watch -n 1 'cat ./state/tasks.json | tail -20'
```

**Remote Monitoring (from Laptop)**:
```bash
# Poll task status every 2 seconds
curl http://dgx:8001/progress/a1b2c3d4

# Check stats
curl http://dgx:8001/progress/stats

# List recent phone recordings
curl "http://dgx:8001/progress?source=phone&limit=5"
```

**Offline Access (from Phone)**:
```
OneDrive → Chat2Plan folder
  - specs/spec.md: Read updated spec
  - state/tasks.json: See task history
```

---

## Workflow 2: Laptop Recording via API

**Goal**: Record audio on laptop, upload via HTTP API, track progress

**Participants**: Laptop, DGX API Server, Services

**Duration**: 30-90 seconds (much faster than OneDrive sync)

### Step-by-Step Flow

**Phase 1: Record Audio (User)**

```
1. Open Windows Voice Recorder
2. Press record
3. Speak ideas (30 seconds)
4. Press stop
5. Export as .wav file
   → C:\Users\user\Downloads\brainstorm.wav
```

**Phase 2: Direct Upload via API**

```
curl -X POST http://dgx:8001/transcribe \
  -F "file=@C:\Users\user\Downloads\brainstorm.wav"

OR programmatically:

import requests

with open("brainstorm.wav", "rb") as f:
    response = requests.post(
        "http://dgx:8001/transcribe",
        files={"file": f}
    )

result = response.json()
task_id = result["task_id"]
transcript = result["text"]
```

**Phase 3: API Server Processing**

```
Time: T + 0 sec

HTTP Request arrives:
  POST /transcribe
  Content-Type: multipart/form-data
  [binary wav file]

STATE CHANGE:
  ProgressManager.create_task(
    filename="brainstorm.wav",
    source="api",
    file_size_bytes=1234567,
    mode="creative"
  )
  → task_id = "b2c3d4e5"

ACTION: Write to ./state/tasks.json
  status: "queued"

STATE CHANGE:
  ProgressManager.update_task_status(
    task_id="b2c3d4e5",
    status=UPLOADING
  )

ACTION: Save file to ./recordings/brainstorm.wav

STATE CHANGE:
  ProgressManager.update_task_status(
    task_id="b2c3d4e5",
    status=TRANSCRIBING
  )

OPERATION: TranscriptionService.transcribe()
  (Same as workflow 1: 10-15 seconds)
  
STATE CHANGE:
  StateManager.append_transcript()
  
  ProgressManager.update_task_status(
    status=PROCESSING,
    transcript_length=3456
  )

OPERATION: SemanticEngine.process_transcript()
  (Same as workflow 1: 15-45 seconds)

STATE CHANGE:
  StateManager.save_spec()
  
  ProgressManager.update_task_status(
    status=COMPLETED,
    spec_updated=True,
    backend_used="claude"
  )

OUTPUT: HTTP Response (200 OK)
{
  "text": "we should focus on...",
  "duration": 30.5,
  "task_id": "b2c3d4e5"
}
```

**Phase 4: Track Progress (Laptop)**

```
Immediate (synchronous response):
{
  "text": "we should focus on...",
  "duration": 30.5,
  "task_id": "b2c3d4e5"
}

Client-side polling:

while True:
    response = requests.get(f"http://dgx:8001/progress/{task_id}")
    task = response.json()
    
    print(f"Status: {task['status']}")
    print(f"Backend: {task['backend_used']}")
    
    if task['status'] in ("completed", "failed"):
        break
    
    time.sleep(2)

Output:
Status: uploading
Status: transcribing
Status: processing
Status: completed
Backend: claude
```

### Comparison: OneDrive vs API Upload

```
OneDrive (Phone):
  - Pros: Works offline, auto-sync, no client code needed
  - Cons: 1-3 minute sync delay
  - Good for: Async batch processing

API (Laptop):
  - Pros: Fast (30-90 sec), real-time feedback, trackable
  - Cons: Requires online, client code, direct access to DGX
  - Good for: Interactive workflows
```

---

## Workflow 3: Interactive CLI Mode

**Goal**: Manual interaction with Block 1 system on same machine

**Participants**: CLI, StateManager, SemanticEngine

**Duration**: User-paced (seconds per command)

### Step-by-Step Commands

```
$ python main.py

Block 1 Research Ideation System
==================================================
Mode: CREATIVE
Type 'help' for commands

>>> status
Session ID: sess-abc123xyz789
Mode: CREATIVE
Transcript chunks: 5
Spec size: 2845
Last updated: 2026-06-02T10:15:45.123456

>>> transcript
--- Transcript History ---
[2026-06-02T10:15:23] (phone, 45.2s):
first recording about system design

[2026-06-02T10:45:12] (laptop, 32.8s):
second recording on implementation details

>>> spec
--- Current Specification ---
# Block 1 Specification

## Overview
...
(entire markdown)

>>> transcribe /path/to/audio.wav
Transcribing /path/to/audio.wav...
Transcription complete: 4521 characters

Added to transcript buffer:
we need to explore...

>>> process we need to explore the system architecture in detail
Processing "we need to explore..." in CREATIVE mode...

STATE CHANGE:
  StateManager.append_transcript()
  SemanticEngine.process_transcript()
  StateManager.save_spec()

Processing complete (backend: claude)
Spec updated.

>>> mode distillation
Switched to DISTILLATION mode

>>> exit
(program terminates)
```

---

## Workflow 4: Remote Client Access

**Goal**: Access DGX from laptop when online, retrieve spec and track progress

**Participants**: Laptop, DGX API Server

**Duration**: User-paced

### Step-by-Step Flow

```
$ python -m src.client dgx-spark.example.com

Block 1 Remote Client
==================================================
Connected to DGX (sess-abc123xyz789)
Mode: CREATIVE
Transcript chunks: 5

>>> status
Session ID: sess-abc123xyz789
Mode: CREATIVE
Transcript chunks: 5
Spec size: 2845
Last updated: 2026-06-02T10:15:45.123456

(Makes HTTP GET /status request)

>>> spec
[Makes HTTP GET /spec request]
Displays full markdown

>>> progress
[Makes HTTP GET /progress request]
Lists recent tasks with statuses

Task a1b2c3d4: research_notes.m4a (phone) - completed
Task b2c3d4e5: brainstorm.wav (laptop) - completed

>>> progress --source phone
Task a1b2c3d4: research_notes.m4a - completed
Task c3d4e5f6: planning_notes.m4a - completed

>>> stats
[Makes HTTP GET /progress/stats request]
Total tasks: 156
Completed: 148
Failed: 2
Active: 6

Phone: 89 tasks
Laptop: 54 tasks
API: 13 tasks

>>> exit
```

---

## Workflow 5: Error Recovery

**Goal**: Handle transcription failure and continue

**Participants**: Phone, DGX, File Watcher, Services

### Scenario: Transcription Timeout

```
1. Phone uploads large audio (3 minutes)
2. File watcher detects
3. Create task a1b2c3d4
4. Wait 1 second
5. Update: TRANSCRIBING
6. Call TranscriptionService.transcribe()
7. Whisper API timeout (>30 seconds)
8. TranscriptionService returns None
9. Exception caught

RECOVERY:
  ProgressManager.update_task_status(
    task_id="a1b2c3d4",
    status=FAILED,
    error_message="Transcription service timeout after 30 seconds"
  )

ACTION: Update ./state/tasks.json
  status: "failed"
  error_message: "Transcription service timeout..."
  completed_at: "2026-06-02T10:15:35.123456"

STATE:
  - Spec NOT updated
  - Transcript NOT added
  - Task marked FAILED

VISIBILITY:
  curl http://dgx:8001/progress/a1b2c3d4
  
  {
    "status": "failed",
    "error_message": "Transcription service timeout after 30 seconds",
    "completed_at": "..."
  }

USER ACTION (Options):
  a) Retry: Re-upload or shorten audio file
  b) Check: Verify DGX Whisper service running
  c) Skip: Move to next recording
```

### Scenario: Claude API Unavailable, DGX Fallback

```
1. Phone uploads audio
2. File watcher processes
3. Transcription succeeds: "new ideas about..."
4. Update: PROCESSING
5. Call SemanticEngine.process_transcript()
6. Try Claude API
   → Connection refused (API down/rate-limited)
7. Fall back to DGX LLM
   → DGX LLM available
   → Returns updated spec
8. Success

OUTPUT:
  backend_used: "dgx" (not "claude")
  
VISIBILITY:
  curl http://dgx:8001/progress/a1b2c3d4
  
  {
    "status": "completed",
    "backend_used": "dgx",
    "spec_updated": true
  }

NOTE: Spec was updated via fallback, but using local LLM instead of Claude
```

---

## Workflow 6: Batch Processing Multiple Recordings

**Goal**: Phone user uploads multiple recordings, they process sequentially

**Timeline**:

```
T+0:00    Upload file1.m4a to OneDrive/recordings/
T+1:00    OneDrive syncs file1
T+1:10    File watcher detects file1 → Processing starts
T+2:30    file1 processing completes, spec updated

T+0:30    (Meanwhile on phone) Upload file2.m4a
T+1:30    OneDrive syncs file2
T+2:45    file2 done processing (processing started after file1 finished)
T+4:00    file2 processing completes, spec updated again

T+1:00    Upload file3.m4a
T+2:00    OneDrive syncs
T+4:15    file3 processing starts
T+5:30    file3 completes

Final state:
  - spec.md contains all ideas from file1, file2, file3
  - tasks.json has 3 entries:
    - file1: completed
    - file2: completed
    - file3: completed
  - transcript_buffer has 3 chunks (all transcripts)
```

**Status Check**:

```
curl "http://dgx:8001/progress?source=phone&limit=10"

{
  "tasks": [
    {"task_id": "a1b2c3d4", "filename": "file3.m4a", "status": "completed"},
    {"task_id": "a1b2c3d3", "filename": "file2.m4a", "status": "completed"},
    {"task_id": "a1b2c3d2", "filename": "file1.m4a", "status": "completed"}
  ],
  "total": 3,
  "active_count": 0
}
```

---

## Workflow 7: Mode Switching for Consolidation

**Goal**: Record ideas in CREATIVE mode, then switch to DISTILLATION for consolidation

**Duration**: Spans multiple sessions

### Session 1: Creative Mode (Brainstorming)

```
$ python main.py

>>> mode creative
Switched to CREATIVE mode

>>> transcribe brainstorm1.wav
Added: "we should explore semantic planning..."

>>> process Semantic planning means...
CREATIVE mode processing (divergent, exploratory)
Spec updated with new ideas section

>>> status
Mode: CREATIVE
Transcript chunks: 2

(Multiple recordings and manual inputs over time)
```

**State After Creative Phase**:
```
Spec contains:
  ## Ideas (scattered)
  - Idea 1
  - Idea 2
  - ...many exploratory thoughts

transcript_buffer: 10+ chunks (brainstorming)
```

### Session 2: Distillation Mode (Consolidation)

```
$ python main.py

>>> mode distillation
Switched to DISTILLATION mode

>>> process Let's consolidate these ideas into requirements
DISTILLATION mode processing (convergent, structuring)
Spec updated with structured sections

Spec now contains:
  ## Requirements
  - Requirement 1
  - Requirement 2
  
  ## Architecture
  - Layer 1
  - Layer 2
  
  ## Implementation Plan
  - Phase 1
  - Phase 2
```

**Semantic Engine Behavior Change**:

In CREATIVE mode:
```
System prompt: "You are in CREATIVE mode. Prioritize exploration, 
divergence, and capturing all ideas. Add new sections for novel concepts."

Result: Spec grows, ideas accumulate, exploratory language
```

In DISTILLATION mode:
```
System prompt: "You are in DISTILLATION mode. Organize ideas into 
categories, extract requirements, reduce ambiguity, create structure."

Result: Spec becomes more organized, clearer, more actionable
```

---

## Summary: Workflow Decision Tree

```
┌─ How am I recording?
│
├─ Phone (iOS/Android)
│  ├─ Save to OneDrive folder
│  └─ (File watcher auto-processes, 1-3 min delay)
│
├─ Laptop (Windows/Mac)
│  ├─ Option A: Save to OneDrive folder
│  │  └─ (Same as phone, 1-3 min delay)
│  │
│  └─ Option B: Upload via API
│     └─ (Direct upload, 30-90 sec, need online)
│
└─ Both devices available, checking progress?
   ├─ Laptop online → Use HTTP API
   │  └─ Fast, real-time status
   │
   └─ Only offline access → Check OneDrive files
      └─ Read spec.md offline, check tasks.json
```

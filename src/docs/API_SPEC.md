# API Specification

## Overview

Block 1 exposes a FastAPI REST API on port 8001 (configurable). This document specifies every endpoint, including request format, response format, and error handling.

**Base URL**: `http://<dgx-host>:8001`

---

## Health & Status Endpoints

### GET /health

**Purpose**: Check if server is running and get session ID

**Request**:
```http
GET /health HTTP/1.1
Host: dgx:8001
```

**Response** (200 OK):
```json
{
    "status": "ok",
    "session": "sess-abc123xyz789"
}
```

**Use Case**: Connection verification, health checks

**cURL Example**:
```bash
curl http://dgx:8001/health
```

---

### GET /status

**Purpose**: Get current system state overview

**Request**:
```http
GET /status HTTP/1.1
Host: dgx:8001
```

**Response** (200 OK):
```json
{
    "session_id": "sess-abc123xyz789",
    "mode": "creative",
    "version": 42,
    "transcript_chunks": 5,
    "spec_size": 2845,
    "last_updated": "2026-06-02T10:15:45.123456"
}
```

**Fields**:
- `session_id` - Unique session identifier
- `mode` - Current system mode (creative/distillation)
- `version` - State version number (increments on each save)
- `transcript_chunks` - Number of transcript entries in buffer
- `spec_size` - Character count of markdown spec
- `last_updated` - ISO 8601 timestamp of last state change

**cURL Example**:
```bash
curl http://dgx:8001/status
```

---

## Data Access Endpoints

### GET /spec

**Purpose**: Retrieve current markdown specification

**Request**:
```http
GET /spec HTTP/1.1
Host: dgx:8001
```

**Response** (200 OK):
```json
{
    "spec": "# Block 1 Specification\n\n## Overview\n...\n## Requirements\n..."
}
```

**Response Fields**:
- `spec` - Complete markdown specification as string

**Use Case**: 
- Laptop pulling latest spec when online
- External agents reading spec for guidance
- Viewing current state of living document

**cURL Example**:
```bash
curl http://dgx:8001/spec
```

**Python Example**:
```python
import requests
response = requests.get("http://dgx:8001/spec")
spec_markdown = response.json()["spec"]
print(spec_markdown)
```

---

### GET /transcript

**Purpose**: Retrieve complete transcript history

**Request**:
```http
GET /transcript HTTP/1.1
Host: dgx:8001
```

**Response** (200 OK):
```json
{
    "transcript": "[2026-06-02T10:15:23] (phone, 45.2s):\nthe first transcript\n\n[2026-06-02T10:45:12] (laptop, 32.8s):\nthe second transcript\n..."
}
```

**Response Fields**:
- `transcript` - Formatted text of all transcript chunks in chronological order

**Format**: Each chunk includes timestamp, source, duration, and text content

**Use Case**: 
- Reviewing conversation history
- Understanding context for processing
- Auditing what was said

**cURL Example**:
```bash
curl http://dgx:8001/transcript
```

---

## Processing Endpoints

### POST /process

**Purpose**: Process text through semantic engine

**Request**:
```http
POST /process HTTP/1.1
Host: dgx:8001
Content-Type: application/json

{
    "text": "the text to process",
    "mode": "creative"
}
```

**Request Fields**:
- `text` (required, str) - Content to process
- `mode` (optional, str) - "creative" or "distillation" (default: "creative")

**Response** (200 OK):
```json
{
    "spec": "# Updated Specification\n...",
    "backend": "claude"
}
```

**Response Fields**:
- `spec` - Updated markdown specification
- `backend` - Which backend processed it ("claude" or "dgx")

**Error Responses**:

**500 Internal Server Error**:
```json
{
    "detail": "Processing failed: timeout waiting for LLM response"
}
```

**Use Case**:
- Direct API call to process transcript
- Immediate (synchronous) processing
- Testing semantic engine

**cURL Example**:
```bash
curl -X POST http://dgx:8001/process \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world", "mode": "creative"}'
```

**Python Example**:
```python
import requests

response = requests.post("http://dgx:8001/process", json={
    "text": "the transcript",
    "mode": "creative"
})

result = response.json()
print(result["spec"])
print(f"Processed by: {result['backend']}")
```

---

### POST /transcribe

**Purpose**: Upload audio file for transcription

**Request**:
```http
POST /transcribe HTTP/1.1
Host: dgx:8001
Content-Type: multipart/form-data

[binary audio data]
```

**Form Data**:
- `file` (required, binary) - Audio file (mp3, wav, m4a, ogg, flac)

**Response** (200 OK):
```json
{
    "text": "the transcribed text",
    "duration": 45.2,
    "task_id": "a1b2c3d4"
}
```

**Response Fields**:
- `text` - Transcribed content
- `duration` - Audio duration in seconds
- `task_id` - Task ID for tracking progress

**Error Responses**:

**500 Internal Server Error**:
```json
{
    "detail": "Transcription failed: file format not supported"
}
```

**Supported Formats**: .wav, .mp3, .m4a, .ogg, .flac

**Use Case**:
- Direct upload from laptop app
- API-based recording pipeline
- Integration with other applications

**Behavior**:
1. Creates ProcessingTask with "api" source
2. Saves file to ./recordings/
3. Transcribes using Whisper
4. Returns transcript and task_id for progress tracking

**cURL Example**:
```bash
curl -X POST http://dgx:8001/transcribe \
  -F "file=@/path/to/audio.wav"
```

**Python Example**:
```python
import requests

with open("audio.wav", "rb") as f:
    files = {"file": f}
    response = requests.post("http://dgx:8001/transcribe", files=files)

result = response.json()
print(f"Transcript: {result['text']}")
print(f"Track progress: /progress/{result['task_id']}")
```

---

## Mode Control Endpoint

### POST /mode/{new_mode}

**Purpose**: Switch system operating mode

**Request**:
```http
POST /mode/distillation HTTP/1.1
Host: dgx:8001
```

**URL Parameters**:
- `new_mode` - "creative" or "distillation"

**Response** (200 OK):
```json
{
    "mode": "distillation",
    "status": "switched"
}
```

**Response Fields**:
- `mode` - Confirmed new mode
- `status` - Status message

**Error Responses**:

**400 Bad Request**:
```json
{
    "detail": "Invalid mode: unknown"
}
```

**Valid Modes**: "creative", "distillation" (case-insensitive)

**Use Case**:
- Switching between ideation and consolidation phases
- Signaling system to change processing behavior

**Behavior**:
- Updates SystemState.mode
- Persists change to disk
- Affects future /process calls

**cURL Example**:
```bash
curl -X POST http://dgx:8001/mode/creative
```

**Python Example**:
```python
import requests

response = requests.post("http://dgx:8001/mode/distillation")
print(f"Mode: {response.json()['mode']}")
```

---

## Progress Tracking Endpoints

### GET /progress/{task_id}

**Purpose**: Get status and details of a specific task

**Request**:
```http
GET /progress/a1b2c3d4 HTTP/1.1
Host: dgx:8001
```

**URL Parameters**:
- `task_id` - 8-character task ID

**Response** (200 OK):
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

**Response Fields**:
- `task_id` - Unique task identifier
- `filename` - Original audio filename
- `source` - Where recording came from (phone/laptop/api)
- `status` - Current progress (queued/uploading/transcribing/processing/completed/failed)
- `created_at` - When task was created
- `started_at` - When processing began (empty if queued)
- `completed_at` - When task finished (empty if still running)
- `file_size_bytes` - Size of audio file
- `duration_seconds` - Duration of audio
- `error_message` - Error details if failed (empty if successful)
- `transcript_length` - Character count of transcribed text
- `spec_updated` - Whether spec was updated
- `backend_used` - Which LLM processed it (claude/dgx)

**Error Responses**:

**404 Not Found**:
```json
{
    "detail": "Task a1b2c3d4 not found"
}
```

**Use Case**:
- Monitor progress of uploaded file
- Detect failures and error messages
- Track completion

**Status Flow**:
```
queued → uploading → transcribing → processing → completed
                                              ↘
                                              failed
```

**cURL Example**:
```bash
curl http://dgx:8001/progress/a1b2c3d4
```

**Python Example**:
```python
import requests
import time

task_id = "a1b2c3d4"

while True:
    response = requests.get(f"http://dgx:8001/progress/{task_id}")
    task = response.json()
    
    print(f"Status: {task['status']}")
    
    if task['status'] == "completed":
        print(f"Transcript: {task['transcript_length']} chars")
        print(f"Spec updated: {task['spec_updated']}")
        break
    elif task['status'] == "failed":
        print(f"Error: {task['error_message']}")
        break
    
    time.sleep(2)  # Poll every 2 seconds
```

---

### GET /progress

**Purpose**: List recent processing tasks with optional filtering

**Request**:
```http
GET /progress?source=phone&limit=20 HTTP/1.1
Host: dgx:8001
```

**Query Parameters**:
- `source` (optional, str) - Filter by "phone", "laptop", or "api"
- `limit` (optional, int) - Max results (default 50, max 200)

**Response** (200 OK):
```json
{
    "tasks": [
        {
            "task_id": "a1b2c3d4",
            "filename": "research_notes.wav",
            "source": "phone",
            "status": "completed",
            "created_at": "2026-06-02T10:15:23.123456",
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

**Response Fields**:
- `tasks` - Array of TaskProgressResponse objects
- `total` - Total tasks in result set
- `active_count` - Tasks currently processing (not completed/failed)

**Filtering Examples**:

All recent tasks:
```
GET /progress
```

Phone recordings only:
```
GET /progress?source=phone
```

Laptop recordings, max 10:
```
GET /progress?source=laptop&limit=10
```

**Use Case**:
- Dashboard showing recent activity
- Monitor device-specific processing
- Identify backlog

**cURL Examples**:
```bash
# All tasks
curl http://dgx:8001/progress

# Phone only
curl "http://dgx:8001/progress?source=phone&limit=20"

# Laptop only
curl "http://dgx:8001/progress?source=laptop&limit=20"
```

**Python Example**:
```python
import requests

# Get recent phone recordings
response = requests.get("http://dgx:8001/progress", params={
    "source": "phone",
    "limit": 10
})

result = response.json()
print(f"Phone tasks: {result['total']}")
print(f"Active: {result['active_count']}")

for task in result['tasks']:
    status = task['status']
    filename = task['filename']
    print(f"  {filename}: {status}")
```

---

### GET /progress/stats

**Purpose**: Get aggregate statistics about all tasks

**Request**:
```http
GET /progress/stats HTTP/1.1
Host: dgx:8001
```

**Response** (200 OK):
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

**Response Fields**:
- `total_tasks` - Total tasks created across all sources
- `completed` - Successfully completed tasks
- `failed` - Failed tasks with errors
- `active` - Currently processing tasks
- `total_transcript_characters` - Sum of all transcript lengths
- `average_audio_duration_seconds` - Mean duration of processed audio
- `sources` - Breakdown by source (phone/laptop/api)

**Use Case**:
- System monitoring dashboard
- Throughput metrics
- Performance analysis
- Device usage breakdown

**cURL Example**:
```bash
curl http://dgx:8001/progress/stats
```

**Python Example**:
```python
import requests

response = requests.get("http://dgx:8001/progress/stats")
stats = response.json()

print(f"Completion Rate: {stats['completed']}/{stats['total_tasks']}")
print(f"Success Rate: {100 * stats['completed'] / stats['total_tasks']:.1f}%")
print(f"Phone: {stats['sources']['phone']} tasks")
print(f"Laptop: {stats['sources']['laptop']} tasks")
print(f"Avg duration: {stats['average_audio_duration_seconds']:.1f}s")
```

---

## Error Handling

### Common Error Responses

**500 Internal Server Error**:
```json
{
    "detail": "Error message describing what went wrong"
}
```

Possible causes:
- Transcription service timeout
- Claude API unavailable
- DGX LLM unavailable
- File read/write errors
- Invalid state

**400 Bad Request**:
```json
{
    "detail": "Invalid request: message"
}
```

Possible causes:
- Invalid mode specified
- Malformed JSON body
- Missing required fields

**404 Not Found**:
```json
{
    "detail": "Resource not found: message"
}
```

Possible causes:
- Task ID doesn't exist
- File not found

---

## Rate Limiting & Timeouts

Currently no rate limiting implemented. However:

- **Transcription timeout**: 30 seconds (configurable via `DGX_TIMEOUT`)
- **Claude API timeout**: 60 seconds (configurable via `CLAUDE_TIMEOUT`)
- **Long transcripts**: May take 30-120 seconds to process

**Recommendation**: Implement timeout handling for long-running /process operations.

---

## Authentication

Currently no authentication implemented. Add before production:

```python
# Future enhancement
@app.post("/process")
async def process_text(request: ProcessRequest, api_key: str = Header(...)):
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... proceed
```

---

## CORS

Currently CORS not configured. To enable from external domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Future Enhancements

- [ ] WebSocket progress streaming (instead of polling)
- [ ] Batch upload endpoint for multiple files
- [ ] API key authentication
- [ ] Rate limiting per API key
- [ ] Request logging/audit trail
- [ ] Pagination for /progress endpoint
- [ ] Export endpoints (JSON, CSV)
- [ ] Webhook callbacks on task completion

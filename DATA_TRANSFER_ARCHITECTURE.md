# Data Transfer Architecture: Phone & Laptop Recording Pipeline

## Overview

Both phone and laptop recordings use **OneDrive as the central sync point**, ensuring seamless data transfer across devices. The system automatically detects new recordings and processes them through a unified pipeline.

## Unified Recording Flow

```
Phone                          Laptop
  ↓                              ↓
Voice Memos                    Voice/Audio App
  ↓                              ↓
OneDrive/Chat2Plan/recordings/OneDrive/Chat2Plan/recordings/
  ↓                              ↓
  └──────────────┬───────────────┘
                 ↓
        File Watcher (DGX)
                 ↓
    ┌────────────┴────────────┐
    ↓                         ↓
Transcribe (Whisper)    Determine Source
    ↓                         ↓
    └────────────┬────────────┘
                 ↓
        Progress Tracker
    (queued → transcribing → processing → completed)
                 ↓
        Semantic Processing
        (Claude API or DGX LLM)
                 ↓
        Living Markdown Spec Update
                 ↓
        OneDrive Sync (Results)
```

## Recording Workflow Details

### 1. **Phone Recording**
- Record audio on phone (Voice Memos, Dictaphone, etc.)
- Manually upload to OneDrive folder: `Chat2Plan/recordings/`
- Or use OneDrive app's auto-sync if recording is saved directly to OneDrive

### 2. **Laptop Recording** 
- Record audio on laptop (Windows Voice Recorder, Audacity, QuickTime, etc.)
- Save directly to: `C:\Users\<user>\OneDrive\Chat2Plan\recordings\`
- Or manually upload the file to OneDrive
- OneDrive auto-syncs to DGX

### 3. **DGX Processing (Automatic)**
- File Watcher monitors OneDrive `recordings/` folder
- Detects new `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac` files
- Creates a processing task with unique ID
- Routes through pipeline: transcribe → process → update spec

## Progress Tracking System

Each file gets a **task ID** that tracks its lifecycle:

### Task Statuses
- `queued` - Task created, waiting to start
- `uploading` - File upload in progress
- `transcribing` - Whisper transcription in progress
- `processing` - Semantic engine processing transcript
- `completed` - Successfully processed and spec updated
- `failed` - Error encountered (see error_message)

### Tracking a File

**Get status of a specific task:**
```bash
curl http://dgx-host:8001/progress/{task_id}
```

Response:
```json
{
  "task_id": "a1b2c3d4",
  "filename": "research_notes.wav",
  "source": "phone",
  "status": "completed",
  "created_at": "2026-06-02T10:15:23",
  "started_at": "2026-06-02T10:15:24",
  "completed_at": "2026-06-02T10:16:45",
  "file_size_bytes": 2456789,
  "duration_seconds": 45.2,
  "error_message": "",
  "transcript_length": 4521,
  "spec_updated": true,
  "backend_used": "claude"
}
```

**List all recent tasks:**
```bash
curl "http://dgx-host:8001/progress?limit=20"
```

**Filter by device source:**
```bash
curl "http://dgx-host:8001/progress?source=phone&limit=20"
curl "http://dgx-host:8001/progress?source=laptop&limit=20"
```

**Get aggregate statistics:**
```bash
curl http://dgx-host:8001/progress/stats
```

Response:
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

## Efficiency Optimizations

### 1. **OneDrive Central Hub**
- ✅ No external API uploads for audio (stays private)
- ✅ Auto-sync handles network retries
- ✅ Works offline - uploads when connection restored
- ✅ Single source of truth for all recordings

### 2. **Local Transcription**
- ✅ Audio processed on DGX (no cloud upload)
- ✅ Whisper model runs locally (fast turnaround)
- ✅ Bandwidth efficient (only text → Claude API)

### 3. **Asynchronous Processing**
- ✅ File watcher runs continuously in background
- ✅ No manual intervention needed
- ✅ Client can poll progress without blocking

### 4. **Fallback Architecture**
- ✅ Claude API primary (cost-efficient Haiku model)
- ✅ DGX LLM fallback if Claude rate-limited
- ✅ Automatic retry on transient failures

### 5. **Progress Visibility**
- ✅ Track each file from upload to completion
- ✅ Identify failures with error messages
- ✅ Monitor system throughput with statistics

## API Endpoints for Data Transfer

### Health & Status
```
GET /health              - Server health check
GET /status              - System overview
```

### Processing
```
POST /transcribe         - Upload audio file directly (returns task_id)
POST /process            - Process text transcript
```

### Progress Tracking
```
GET  /progress/{task_id}        - Get task status
GET  /progress                  - List recent tasks (filterable)
GET  /progress/stats            - Aggregate statistics
```

### Data Retrieval
```
GET /spec                - Get current markdown specification
GET /transcript          - Get full transcript history
```

## Laptop Recording Setup (Windows)

### Option 1: Direct OneDrive Folder Save
1. Use Windows Voice Recorder or other app
2. Save to: `C:\Users\<username>\OneDrive\Chat2Plan\recordings\`
3. OneDrive auto-syncs to DGX

### Option 2: File Upload via API
```bash
curl -X POST \
  -F "file=@/path/to/recording.wav" \
  http://dgx-host:8001/transcribe
```

Returns: `{"text": "...", "task_id": "a1b2c3d4", "duration": 45.2}`

## Phone Recording Setup (iOS)

1. Record in Voice Memos or similar app
2. Export/upload to OneDrive
3. Navigate to: `Chat2Plan/recordings/`
4. Upload the .m4a or .wav file
5. DGX automatically processes within 1-2 minutes

## Phone Recording Setup (Android)

1. Record using Google Recorder or voice app
2. Save to OneDrive `Chat2Plan/recordings/`
3. Or manually upload the audio file
4. Supported formats: `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`

## Monitoring Pipeline Status

### From Laptop (Remote)
```bash
# Check overall system status
python -m src.client <dgx-host>

# In interactive client, use:
status                    - System overview
progress stats            - See throughput
```

### From DGX (Direct)
```bash
# View progress file directly
cat ./state/tasks.json

# Watch live activity
tail -f ./state/tasks.json

# Check API logs
curl http://localhost:8001/progress/stats
```

## Error Handling

### Common Issues & Resolution

**Transcription Failed**
- Check audio file format (must be .wav, .mp3, .m4a, .ogg, or .flac)
- Verify Whisper model is loaded on DGX
- Check error_message in task status

**Spec Update Failed**
- Check Claude API key configured
- Check DGX LLM fallback availability
- View error_message in task details

**File Not Detected**
- Verify OneDrive path is mounted/synced
- Check file is in correct folder: `Chat2Plan/recordings/`
- Wait 30-60 seconds for file sync (depends on file size & network)

**Timeout Issues**
- For files > 5 min: Increase CLAUDE_TIMEOUT in .env
- Monitor processing with `/progress/{task_id}` endpoint
- Long files may take 2-5 minutes total

## Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Phone → OneDrive sync | 1-3 min (network dependent) |
| File detection by watcher | 5-10 sec |
| Transcription (1 min audio) | 10-15 sec |
| Semantic processing | 15-45 sec (depends on transcript length) |
| **Total pipeline end-to-end** | **1-3 minutes** |
| Concurrent tasks | 2-3 (depends on DGX resources) |

## Architecture Advantages

1. **Privacy**: Audio never leaves your network (local transcription)
2. **Reliability**: OneDrive handles sync, retry logic, offline support
3. **Cost**: Only LLM API calls billed, not transcription
4. **Scalability**: Multiple devices simultaneously → single OneDrive folder
5. **Flexibility**: Works with any recording app on any device
6. **Traceability**: Full progress tracking with task IDs and timestamps
7. **Resilience**: Fallback LLM if primary API unavailable

## Future Optimizations

Potential improvements:
- [ ] Streaming transcription for real-time progress
- [ ] WebSocket progress notifications (instead of polling)
- [ ] Compression for audio files before OneDrive upload
- [ ] Batch processing for multiple files
- [ ] Selective sync (cherry-pick which devices to process)

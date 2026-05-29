# Block 1: Research Ideation & Distillation System

A dual-phase semantic planning system for research-driven workflows. Separates creative exploration from structured consolidation.

## Architecture

```
Phone (Voice Recording)
  ↓ OneDrive auto-sync
  ↓
DGX Spark (Always Running)
├─ Whisper (local transcription)
├─ API Server (port 8001)
├─ File Watcher (monitors OneDrive/recordings)
│  ├─ Auto-transcribes new files
│  └─ Auto-processes specs via Claude (or DGX fallback)
└─ Semantic LLM (local processing, fallback only)
  
Claude API (Primary Semantic Processing)
└─ Better reasoning for mode discipline
└─ Fallback to DGX if rate-limited
  ↓
OneDrive (syncs results)
  ↓
Laptop (pulls results when online)
└─ Client CLI (remote API calls)
```

## Features

- **Dual-Mode Processing**: Creative (divergence) and Distillation (convergence) modes
- **Two-Stage Voice Pipeline**:
  - Stage 1: Voice recording on phone → OneDrive
  - Stage 2: DGX auto-transcribes → processes → syncs back
- **Hybrid LLM Architecture**:
  - Primary: Claude API (Haiku model for cost-efficiency)
  - Fallback: Self-hosted LLM on DGX (when Claude unavailable/rate-limited)
- **Remote Access**:
  - FastAPI server on DGX for remote requests
  - File watcher for auto-processing OneDrive files
  - Client CLI for laptop (when online)
- **Living Markdown Spec**: Single versioned artifact with incremental updates

## Installation

### Option A: Run Locally (for testing)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DGX settings
python main.py
```

### Option B: Deploy to DGX (production)

**Prerequisites:**
- DGX accessible via SSH or proxyjump
- OneDrive mounted/synced on DGX (see OneDrive Setup below)

**Steps:**

```bash
# From laptop
bash deploy_to_dgx.sh <dgx_host> <dgx_user>

# Example with proxyjump:
# Configure ~/.ssh/config first, then:
bash deploy_to_dgx.sh <dgx_hostname> <dgx_user>
```

Then SSH to DGX and:

```bash
cd ~/Chat2Plan
cp .env.example .env
nano .env  # Configure DGX endpoints + Claude API key

# Start both services
python -m src.api_server  # Terminal 1
python -m src.file_watcher  # Terminal 2 (or use systemd)
```

## Usage

### Phone Workflow (Auto)

1. Record on phone (Voice Memos, etc.)
2. Upload to OneDrive `Chat2Plan/recordings/`
3. DGX file watcher detects → transcribes → processes
4. Results sync back to OneDrive
5. Pull from laptop when online

### Laptop Workflow (Interactive)

Once DGX is running, from laptop:

```bash
python -m src.client 192.168.1.100
```

Then in the client:

```
>>> help
>>> spec                    # View current spec
>>> transcript              # View transcript history
>>> process Some idea here  # Process text (Creative mode)
>>> process:d Refine this   # Process in Distillation mode
>>> mode d                  # Switch to Distillation mode
>>> transcribe audio.mp3    # Transcribe audio file
>>> status                  # Show system status
```

### CLI Modes (Local Development)

For local testing without DGX:

```bash
python main.py

>>> help
>>> mode creative
>>> process Test idea
>>> spec
>>> mode distillation
>>> process Refine this
```

## Configuration

Edit `.env`:

```ini
# DGX vLLM API
DGX_BASE_URL=http://192.168.1.100:8000
DGX_API_KEY=dummy-key
DGX_TIMEOUT=30

# Claude Fallback (cheap Haiku model)
CLAUDE_API_KEY=your-claude-api-key
CLAUDE_MODEL=claude-3-5-haiku-20241022
CLAUDE_TIMEOUT=60

# Models
SEMANTIC_LLM_MODEL=your-model-name
WHISPER_MODEL=whisper-1

# Paths
STATE_DIR=./state
SPECS_DIR=./specs
RECORDINGS_DIR=./recordings
ONEDRIVE_RECORDINGS_PATH=/path/to/OneDrive/Chat2Plan/recordings

# Server
API_HOST=0.0.0.0
API_PORT=8001
```

### OneDrive Setup on DGX

The file watcher monitors `ONEDRIVE_RECORDINGS_PATH`. Configure this by:

1. **Mount OneDrive on DGX** (via rclone, syncthing, or native mount)
   ```bash
   # Example with rclone:
   rclone config  # Configure OneDrive
   rclone mount OneDrive: /mnt/onedrive --daemon
   ```

2. **Set path in .env:**
   ```
   ONEDRIVE_RECORDINGS_PATH=/mnt/onedrive/Chat2Plan/recordings
   ```

3. **File watcher will monitor this folder automatically**

## System Components

**On DGX (Always Running):**
- `api_server.py` — FastAPI server for remote requests (port 8001)
- `file_watcher.py` — Monitors OneDrive recordings, auto-processes
- Whisper + Semantic LLM (vLLM endpoints)

**On Laptop (Interactive):**
- `cli.py` — Local CLI for testing
- `client.py` — Remote client for DGX API

**Shared:**
- `state_manager.py` — File-based persistence (JSON + Markdown)
- `semantic_engine.py` — DGX LLM processing
- `transcription_service.py` — Whisper client
- `models.py` — Data structures

## API Endpoints (on DGX)

```
GET  /health                    # Health check
GET  /status                    # System status
GET  /spec                      # Get current spec
GET  /transcript                # Get transcript history
POST /process                   # Process text
POST /transcribe                # Transcribe audio file
POST /mode/{creative|distillation}  # Switch mode
```

## Deployment with systemd (DGX)

Create systemd services for auto-start on reboot:

**API Server** (`/etc/systemd/system/block1-api.service`):
```ini
[Unit]
Description=Block 1 API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Chat2Plan
ExecStart=/usr/bin/python3 -m src.api_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**File Watcher** (`/etc/systemd/system/block1-watcher.service`):
```ini
[Unit]
Description=Block 1 File Watcher
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Chat2Plan
ExecStart=/usr/bin/python3 -m src.file_watcher
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable block1-api block1-watcher
sudo systemctl start block1-api block1-watcher
sudo systemctl status block1-api block1-watcher
```

## Testing

```bash
pytest tests/
```

## Key Design Principles

1. **Stateless LLM**: All state external (JSON + Markdown files)
2. **Enforced Mode Discipline**: Creative ≠ Distillation (different prompts + behavior)
3. **Incremental Updates**: Only changed spec sections rewritten
4. **Hybrid LLM Backend**: Claude primary (better semantic reasoning) + DGX fallback (when rate-limited)
5. **Always-On DGX**: Enables phone recording → auto-processing pipeline
6. **Network-Resilient**: Laptop and phone work offline; DGX syncs when online

## Known Limitations

- Audio recording requires phone + OneDrive
- Local device needs network for client access
- Codebase graph injection not yet implemented
- Web UI not implemented (CLI-only)

## Future Work

- Mobile app for direct upload
- Web UI dashboard
- Session versioning/archiving
- Codebase-aware planning (graph injection)

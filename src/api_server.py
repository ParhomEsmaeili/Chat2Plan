"""FastAPI server for Block 1 system - runs on DGX."""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from src.state_manager import StateManager
from src.semantic_engine import SemanticEngine
from src.transcription_service import TranscriptionService
from src.progress_manager import ProgressManager
from src.models import Mode, TaskStatus


app = FastAPI(title="Block 1 Research Ideation System", version="0.1.0")

# Initialize services
state_manager = StateManager(
    state_dir=os.getenv("STATE_DIR", "./state"),
    specs_dir=os.getenv("SPECS_DIR", "./specs"),
)

semantic_engine = SemanticEngine(
    dgx_base_url=os.getenv("DGX_BASE_URL"),
    dgx_api_key=os.getenv("DGX_API_KEY"),
    dgx_model=os.getenv("SEMANTIC_LLM_MODEL"),
    dgx_timeout=int(os.getenv("DGX_TIMEOUT", "30")),
    claude_api_key=os.getenv("CLAUDE_API_KEY"),
    claude_model=os.getenv("CLAUDE_MODEL"),
    claude_timeout=int(os.getenv("CLAUDE_TIMEOUT", "60")),
)

transcription_service = TranscriptionService(
    dgx_base_url=os.getenv("DGX_BASE_URL"),
    dgx_api_key=os.getenv("DGX_API_KEY"),
    whisper_model=os.getenv("WHISPER_MODEL"),
    timeout=int(os.getenv("DGX_TIMEOUT", "30")),
)

progress_manager = ProgressManager(
    progress_dir=os.getenv("STATE_DIR", "./state"),
)


class ProcessRequest(BaseModel):
    """Request to process text."""
    text: str
    mode: str = "creative"  # or "distillation"


class TranscribeResponse(BaseModel):
    """Response from transcription."""
    text: str
    duration: float
    task_id: str = ""


class ProcessResponse(BaseModel):
    """Response from processing."""
    spec: str
    backend: str


class TaskProgressResponse(BaseModel):
    """Response for a single task's progress."""
    task_id: str
    filename: str
    source: str
    status: str
    created_at: str
    started_at: str = ""
    completed_at: str = ""
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    error_message: str = ""
    transcript_length: int = 0
    spec_updated: bool = False
    backend_used: str = ""


class TasksListResponse(BaseModel):
    """Response for list of tasks."""
    tasks: list
    total: int
    active_count: int


class ProgressStatsResponse(BaseModel):
    """Response for progress statistics."""
    total_tasks: int
    completed: int
    failed: int
    active: int
    total_transcript_characters: int
    average_audio_duration_seconds: float
    sources: dict


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "session": state_manager.load_state().session_id}


@app.get("/status")
async def status():
    """Get current system status."""
    state = state_manager.load_state()
    spec = state_manager.load_spec()
    return {
        "session_id": state.session_id,
        "mode": state.mode.value,
        "version": state.version,
        "transcript_chunks": len(state.transcript_buffer),
        "spec_size": len(spec),
        "last_updated": state.last_updated,
    }


@app.get("/spec")
async def get_spec():
    """Get current specification."""
    spec = state_manager.load_spec()
    return {"spec": spec}


@app.get("/transcript")
async def get_transcript():
    """Get transcript history."""
    history = state_manager.get_transcript_history()
    return {"transcript": history}


@app.post("/process")
async def process_text(request: ProcessRequest) -> ProcessResponse:
    """Process text through semantic engine."""
    try:
        # Switch mode if needed
        current_mode = state_manager.get_mode()
        if request.mode.lower() != current_mode.value:
            state_manager.switch_mode(Mode(request.mode.lower()))
        
        # Add to transcript
        state_manager.append_transcript(request.text, source="api")
        
        # Process
        mode = state_manager.get_mode().value
        current_spec = state_manager.load_spec()
        transcript_history = state_manager.get_transcript_history()
        
        updated_spec, backend = semantic_engine.process_transcript(
            mode=mode,
            transcript_text=request.text,
            current_spec=current_spec,
            transcript_history=transcript_history,
        )
        
        # Save updated spec
        state_manager.save_spec(updated_spec)
        state = state_manager.load_state()
        state.current_spec_markdown = updated_spec
        state_manager.save_state(state)
        
        return ProcessResponse(spec=updated_spec, backend=backend)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio file and track progress."""
    try:
        # Create task
        task = progress_manager.create_task(
            filename=file.filename or "unknown",
            source="api",
            mode="creative",
        )
        
        # Save uploaded file temporarily
        recordings_dir = os.getenv("RECORDINGS_DIR", "./recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        
        file_path = os.path.join(recordings_dir, file.filename)
        content = await file.read()
        
        # Update task: uploading
        progress_manager.update_task_status(task.task_id, TaskStatus.UPLOADING)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        task.file_size_bytes = len(content)
        
        # Update task: transcribing
        progress_manager.update_task_status(task.task_id, TaskStatus.TRANSCRIBING)
        
        # Transcribe
        text = transcription_service.transcribe(file_path)
        if not text:
            raise Exception("Transcription failed")
        
        # Add to transcript
        state_manager.append_transcript(text, source="api")
        
        # Update task: processing
        progress_manager.update_task_status(
            task.task_id,
            TaskStatus.PROCESSING,
            transcript_text=text,
            transcript_length=len(text),
        )
        
        # Update task: completed
        progress_manager.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            spec_updated=True,
        )
        
        return TranscribeResponse(text=text, duration=0.0, task_id=task.task_id)
    
    except Exception as e:
        if 'task' in locals():
            progress_manager.update_task_status(
                task.task_id,
                TaskStatus.FAILED,
                error_message=str(e),
            )
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/mode/{new_mode}")
async def switch_mode(new_mode: str):
    """Switch system mode."""
    try:
        if new_mode.lower() not in ["creative", "distillation"]:
            raise ValueError(f"Invalid mode: {new_mode}")
        
        state_manager.switch_mode(Mode(new_mode.lower()))
        return {"mode": new_mode.lower(), "status": "switched"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PROGRESS TRACKING ENDPOINTS
# ============================================================================

@app.get("/progress/{task_id}", response_model=TaskProgressResponse)
async def get_task_progress(task_id: str):
    """Get progress of a specific task."""
    task = progress_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskProgressResponse(
        task_id=task.task_id,
        filename=task.filename,
        source=task.source,
        status=task.status.value,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        file_size_bytes=task.file_size_bytes,
        duration_seconds=task.duration_seconds,
        error_message=task.error_message,
        transcript_length=task.transcript_length,
        spec_updated=task.spec_updated,
        backend_used=task.backend_used,
    )


@app.get("/progress", response_model=TasksListResponse)
async def list_tasks(
    source: str = Query(None, description="Filter by 'phone', 'laptop', or 'api'"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all processing tasks with optional filtering."""
    tasks = progress_manager.list_tasks(source=source, limit=limit)
    active_count = len(progress_manager.get_active_tasks())
    
    task_responses = [
        {
            "task_id": task.task_id,
            "filename": task.filename,
            "source": task.source,
            "status": task.status.value,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "file_size_bytes": task.file_size_bytes,
            "duration_seconds": task.duration_seconds,
            "error_message": task.error_message,
            "transcript_length": task.transcript_length,
            "spec_updated": task.spec_updated,
            "backend_used": task.backend_used,
        }
        for task in tasks
    ]
    
    return TasksListResponse(
        tasks=task_responses,
        total=len(tasks),
        active_count=active_count,
    )


@app.get("/progress/stats", response_model=ProgressStatsResponse)
async def get_progress_stats():
    """Get aggregate statistics about all processing tasks."""
    stats = progress_manager.get_statistics()
    return ProgressStatsResponse(**stats)


def run_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    run_server(host=host, port=port)

"""File watcher for auto-processing OneDrive recordings."""

import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.state_manager import StateManager
from src.semantic_engine import SemanticEngine
from src.transcription_service import TranscriptionService
from src.models import Mode


class RecordingHandler(FileSystemEventHandler):
    """Handle new audio files in the recordings folder."""

    def __init__(self, state_manager, semantic_engine, transcription_service):
        """Initialize with service instances."""
        self.state_manager = state_manager
        self.semantic_engine = semantic_engine
        self.transcription_service = transcription_service
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file is created."""
        if event.is_dir:
            return
        
        # Only process audio files
        if not event.src_path.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac')):
            return
        
        # Skip if already processed
        if event.src_path in self.processed_files:
            return
        
        print(f"New audio file detected: {event.src_path}")
        
        # Wait a bit for file to finish writing
        time.sleep(1)
        
        try:
            # Transcribe
            print(f"Transcribing {Path(event.src_path).name}...")
            text = self.transcription_service.transcribe(event.src_path)
            
            if not text:
                print(f"Transcription failed for {event.src_path}")
                return
            
            print(f"Transcription complete: {len(text)} characters")
            
            # Add to transcript buffer
            self.state_manager.append_transcript(text, source="phone")
            
            # Auto-process in Creative mode
            print("Processing in CREATIVE mode...")
            mode = "creative"  # Always start in creative mode for brainstorms
            current_spec = self.state_manager.load_spec()
            transcript_history = self.state_manager.get_transcript_history()
            
            updated_spec, backend = self.semantic_engine.process_transcript(
                mode=mode,
                transcript_text=text,
                current_spec=current_spec,
                transcript_history=transcript_history,
            )
            
            # Save updated spec
            self.state_manager.save_spec(updated_spec)
            state = self.state_manager.load_state()
            state.current_spec_markdown = updated_spec
            self.state_manager.save_state(state)
            
            print(f"Spec updated (backend: {backend})")
            
            # Mark as processed
            self.processed_files.add(event.src_path)
        
        except Exception as e:
            print(f"Error processing {event.src_path}: {e}")


class FileWatcher:
    """Watch OneDrive recordings folder for new audio files."""

    def __init__(self, watch_path: str, state_manager, semantic_engine, transcription_service):
        """
        Initialize file watcher.
        
        Args:
            watch_path: Path to watch (e.g., /path/to/OneDrive/recordings)
            state_manager: StateManager instance
            semantic_engine: SemanticEngine instance
            transcription_service: TranscriptionService instance
        """
        self.watch_path = Path(watch_path)
        self.observer = Observer()
        self.handler = RecordingHandler(state_manager, semantic_engine, transcription_service)

    def start(self):
        """Start watching the folder."""
        if not self.watch_path.exists():
            print(f"Warning: Watch path does not exist: {self.watch_path}")
            self.watch_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Starting file watcher on {self.watch_path}")
        self.observer.schedule(self.handler, str(self.watch_path), recursive=False)
        self.observer.start()

    def stop(self):
        """Stop watching the folder."""
        self.observer.stop()
        self.observer.join()
        print("File watcher stopped")


def run_file_watcher():
    """Run file watcher (for daemon mode on DGX)."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
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
    
    # Start watcher
    watch_path = os.getenv("ONEDRIVE_RECORDINGS_PATH", "./recordings")
    watcher = FileWatcher(watch_path, state_manager, semantic_engine, transcription_service)
    watcher.start()
    
    print("File watcher running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("Shutting down...")


if __name__ == "__main__":
    run_file_watcher()

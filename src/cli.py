"""CLI interaction loop for Block 1 system."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from src.state_manager import StateManager
from src.semantic_engine import SemanticEngine
from src.transcription_service import TranscriptionService
from src.models import Mode


class Block1CLI:
    """Interactive CLI for Block 1 research ideation system."""

    def __init__(self):
        """Initialize CLI and load configuration."""
        load_dotenv()

        # Initialize managers and services
        self.state_manager = StateManager(
            state_dir=os.getenv("STATE_DIR", "./state"),
            specs_dir=os.getenv("SPECS_DIR", "./specs"),
        )
        
        self.semantic_engine = SemanticEngine(
            dgx_base_url=os.getenv("DGX_BASE_URL"),
            dgx_api_key=os.getenv("DGX_API_KEY"),
            dgx_model=os.getenv("SEMANTIC_LLM_MODEL"),
            dgx_timeout=int(os.getenv("DGX_TIMEOUT", "30")),
            claude_api_key=os.getenv("CLAUDE_API_KEY"),
            claude_model=os.getenv("CLAUDE_MODEL"),
            claude_timeout=int(os.getenv("CLAUDE_TIMEOUT", "60")),
        )
        
        self.transcription_service = TranscriptionService(
            dgx_base_url=os.getenv("DGX_BASE_URL"),
            dgx_api_key=os.getenv("DGX_API_KEY"),
            whisper_model=os.getenv("WHISPER_MODEL"),
            timeout=int(os.getenv("DGX_TIMEOUT", "30")),
        )

        self.running = True
        print("Block 1 Research Ideation System")
        print("=" * 50)
        print(f"Mode: {self.state_manager.get_mode().value.upper()}")
        print("Type 'help' for commands\n")

    def run(self):
        """Main CLI loop."""
        while self.running:
            try:
                command = input(">>> ").strip()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                print("\nExiting...")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")

    def process_command(self, command: str):
        """Process a CLI command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self.show_help()
        elif cmd == "transcript":
            self.show_transcript()
        elif cmd == "spec":
            self.show_spec()
        elif cmd == "section":
            self.show_section(args)
        elif cmd == "transcribe":
            self.transcribe_audio(args)
        elif cmd == "process":
            self.process_transcript(args)
        elif cmd == "mode":
            self.switch_mode(args)
        elif cmd == "status":
            self.show_status()
        elif cmd == "exit":
            self.running = False
        else:
            print(f"Unknown command: {cmd}. Type 'help' for commands.")

    def show_help(self):
        """Show available commands."""
        print("""
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
""")

    def show_transcript(self):
        """Display full transcript history."""
        print("\n--- Transcript History ---")
        print(self.state_manager.get_transcript_history())
        print()

    def show_spec(self):
        """Display current markdown spec."""
        spec = self.state_manager.load_spec()
        print("\n--- Current Specification ---")
        print(spec)
        print()

    def show_section(self, section_name: str):
        """Display specific section of spec."""
        if not section_name:
            print("Usage: section <section_name>")
            return
        
        content = self.state_manager.get_spec_section(section_name)
        print(f"\n--- {section_name} ---")
        print(content if content else "(empty)")
        print()

    def transcribe_audio(self, file_path: str):
        """Transcribe audio file."""
        if not file_path:
            print("Usage: transcribe <path>")
            return
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        print(f"Transcribing {file_path}...")
        text = self.transcription_service.transcribe(file_path)
        
        if text:
            # Add to transcript buffer
            self.state_manager.append_transcript(text, source="whisper")
            print(f"Added to transcript buffer:\n{text}\n")
        else:
            print("Transcription failed.\n")

    def process_transcript(self, user_input: str):
        """Process transcript through semantic engine."""
        # If user provided text, add it to transcript
        if user_input:
            self.state_manager.append_transcript(user_input, source="user")
            transcript_text = user_input
        else:
            # Use latest transcript chunk
            state = self.state_manager.load_state()
            if not state.transcript_buffer:
                print("No transcript to process. Use 'transcribe <file>' first.\n")
                return
            transcript_text = state.transcript_buffer[-1].text
        
        mode = self.state_manager.get_mode().value
        current_spec = self.state_manager.load_spec()
        transcript_history = self.state_manager.get_transcript_history()
        
        print(f"Processing in {mode.upper()} mode...")
        updated_spec, backend = self.semantic_engine.process_transcript(
            mode=mode,
            transcript_text=transcript_text,
            current_spec=current_spec,
            transcript_history=transcript_history,
        )
        
        # Save updated spec
        self.state_manager.save_spec(updated_spec)
        state = self.state_manager.load_state()
        state.current_spec_markdown = updated_spec
        self.state_manager.save_state(state)
        
        print(f"Spec updated (backend: {backend})\n")
        print("--- Updated Sections ---")
        print(updated_spec[-500:])  # Show last 500 chars
        print("\n")

    def switch_mode(self, mode_str: str):
        """Switch between Creative and Distillation modes."""
        if not mode_str:
            current_mode = self.state_manager.get_mode()
            print(f"Current mode: {current_mode.value}")
            print("Usage: mode [creative|distillation]")
            return
        
        mode_str = mode_str.lower()
        if mode_str == "creative":
            self.state_manager.switch_mode(Mode.CREATIVE)
            print("Switched to CREATIVE mode")
        elif mode_str == "distillation":
            self.state_manager.switch_mode(Mode.DISTILLATION)
            print("Switched to DISTILLATION mode")
        else:
            print(f"Unknown mode: {mode_str}")
        print()

    def show_status(self):
        """Show current system status."""
        state = self.state_manager.load_state()
        spec = self.state_manager.load_spec()
        
        print(f"""
--- System Status ---
Session ID: {state.session_id}
Mode: {state.mode.value.upper()}
Version: {state.version}
Last Updated: {state.last_updated}

Transcript Chunks: {len(state.transcript_buffer)}
Spec Size: {len(spec)} chars

DGX Base URL: {self.semantic_engine.dgx_base_url}
DGX Model: {self.semantic_engine.dgx_model}
Claude Available: {self.semantic_engine.claude_client is not None}
""")


def main():
    """Entry point."""
    cli = Block1CLI()
    cli.run()


if __name__ == "__main__":
    main()

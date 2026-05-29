"""Client for interacting with Block 1 API server on DGX."""

import requests
from pathlib import Path
from typing import Optional


class Block1Client:
    """Client for Block 1 API server."""

    def __init__(self, dgx_host: str, dgx_port: int = 8001):
        """
        Initialize client.
        
        Args:
            dgx_host: DGX hostname or IP
            dgx_port: API server port
        """
        self.base_url = f"http://{dgx_host}:{dgx_port}"

    def health(self) -> dict:
        """Check server health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def status(self) -> dict:
        """Get system status."""
        response = requests.get(f"{self.base_url}/status")
        return response.json()

    def get_spec(self) -> str:
        """Get current specification."""
        response = requests.get(f"{self.base_url}/spec")
        return response.json()["spec"]

    def get_transcript(self) -> str:
        """Get transcript history."""
        response = requests.get(f"{self.base_url}/transcript")
        return response.json()["transcript"]

    def process(self, text: str, mode: str = "creative") -> dict:
        """Process text through semantic engine."""
        response = requests.post(
            f"{self.base_url}/process",
            json={"text": text, "mode": mode},
        )
        return response.json()

    def transcribe(self, audio_file_path: str) -> dict:
        """Transcribe audio file."""
        with open(audio_file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.base_url}/transcribe",
                files=files,
            )
        return response.json()

    def switch_mode(self, mode: str) -> dict:
        """Switch system mode."""
        response = requests.post(f"{self.base_url}/mode/{mode}")
        return response.json()


def interactive_client(dgx_host: str):
    """Interactive CLI client for laptop."""
    client = Block1Client(dgx_host)
    
    print("Block 1 Remote Client")
    print("=" * 50)
    
    # Check connection
    try:
        status = client.status()
        print(f"Connected to DGX ({status['session_id']})")
        print(f"Mode: {status['mode'].upper()}")
        print(f"Transcript chunks: {status['transcript_chunks']}")
    except Exception as e:
        print(f"Failed to connect to DGX at {dgx_host}: {e}")
        return
    
    print("\nCommands: spec | transcript | process | mode | transcribe | help | exit\n")
    
    while True:
        try:
            cmd = input(">>> ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command == "help":
                print("""
Commands:
  spec                - Show current specification
  transcript          - Show transcript history
  process [text]      - Process text (Creative mode by default)
  process:d [text]    - Process text in Distillation mode
  mode [c|d]          - Switch mode (c=creative, d=distillation)
  transcribe <file>   - Transcribe audio file
  status              - Show system status
  exit                - Exit client
""")
            
            elif command == "spec":
                spec = client.get_spec()
                print("\n--- Current Specification ---")
                print(spec)
                print()
            
            elif command == "transcript":
                transcript = client.get_transcript()
                print("\n--- Transcript History ---")
                print(transcript)
                print()
            
            elif command == "process":
                if args:
                    result = client.process(args, mode="creative")
                    print(f"\nProcessed (backend: {result['backend']})")
                    print("--- Updated Spec (last 500 chars) ---")
                    print(result['spec'][-500:])
                    print()
                else:
                    print("Usage: process <text>")
            
            elif command == "process:d":
                if args:
                    result = client.process(args, mode="distillation")
                    print(f"\nProcessed in DISTILLATION (backend: {result['backend']})")
                    print("--- Updated Spec (last 500 chars) ---")
                    print(result['spec'][-500:])
                    print()
                else:
                    print("Usage: process:d <text>")
            
            elif command == "mode":
                if args:
                    mode_map = {"c": "creative", "d": "distillation"}
                    mode = mode_map.get(args.lower(), args.lower())
                    result = client.switch_mode(mode)
                    print(f"Switched to {result['mode'].upper()}\n")
                else:
                    status = client.status()
                    print(f"Current mode: {status['mode'].upper()}\n")
            
            elif command == "transcribe":
                if args:
                    if not Path(args).exists():
                        print(f"File not found: {args}")
                    else:
                        print(f"Transcribing {args}...")
                        result = client.transcribe(args)
                        print(f"Transcribed: {len(result['text'])} characters\n")
                else:
                    print("Usage: transcribe <file_path>")
            
            elif command == "status":
                status = client.status()
                print(f"""
--- System Status ---
Mode: {status['mode'].upper()}
Version: {status['version']}
Transcript chunks: {status['transcript_chunks']}
Spec size: {status['spec_size']} chars
Last updated: {status['last_updated']}
""")
            
            elif command == "exit":
                print("Goodbye!")
                break
            
            else:
                print(f"Unknown command: {command}")
        
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python client.py <dgx_host> [dgx_port]")
        print("Example: python client.py 192.168.1.100")
        sys.exit(1)
    
    dgx_host = sys.argv[1]
    interactive_client(dgx_host)

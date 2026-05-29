"""Transcription service for DGX-hosted Whisper model."""

import os
from typing import Optional
from pathlib import Path
import requests


class TranscriptionService:
    """
    Handles audio transcription via DGX-hosted Whisper model (vLLM OpenAI-compatible API).
    """

    def __init__(
        self,
        dgx_base_url: Optional[str] = None,
        dgx_api_key: str = "dummy-key",
        whisper_model: str = "whisper-1",
        timeout: int = 60,
    ):
        """
        Initialize transcription service.

        Args:
            dgx_base_url: Base URL for DGX vLLM API (e.g., http://localhost:8000)
            dgx_api_key: API key for DGX
            whisper_model: Whisper model name on DGX
            timeout: Timeout for requests (seconds)
        """
        self.dgx_base_url = dgx_base_url or os.getenv("DGX_BASE_URL", "http://localhost:8000")
        self.dgx_api_key = dgx_api_key or os.getenv("DGX_API_KEY", "dummy-key")
        self.whisper_model = whisper_model or os.getenv("WHISPER_MODEL", "whisper-1")
        self.timeout = timeout
        self.endpoint = f"{self.dgx_base_url}/v1/audio/transcriptions"

    def transcribe(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using DGX Whisper.

        Args:
            audio_file_path: Path to audio file (MP3, WAV, etc.)

        Returns:
            Transcribed text or None if failed
        """
        if not os.path.exists(audio_file_path):
            print(f"Error: Audio file not found: {audio_file_path}")
            return None

        try:
            with open(audio_file_path, "rb") as f:
                files = {
                    "file": (Path(audio_file_path).name, f, "audio/mpeg"),
                }
                data = {
                    "model": self.whisper_model,
                }
                headers = {
                    "Authorization": f"Bearer {self.dgx_api_key}",
                }

                response = requests.post(
                    self.endpoint,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "")
                    print(f"Transcription successful: {len(text)} characters")
                    return text
                else:
                    print(f"Transcription failed: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    return None

        except requests.exceptions.Timeout:
            print(f"Transcription timeout after {self.timeout}s")
            return None
        except Exception as e:
            print(f"Transcription error: {type(e).__name__}: {e}")
            return None

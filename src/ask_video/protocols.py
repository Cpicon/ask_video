from pathlib import Path
from typing import Protocol

from ask_video.models import (
    Transcript, Session, Message, VideoURL, VideoID, TranscriptHash,
)


class VideoSource(Protocol):
    def extract_id(self, url: VideoURL) -> VideoID:
        """Extract a canonical video identifier from a URL."""
        ...

    def fetch_transcript(self, url: VideoURL) -> str | None:
        """Try to get an existing transcript with timestamps. Returns None if unavailable."""
        ...

    def download_audio(self, url: VideoURL, output_dir: Path) -> Path:
        """Download audio from the video URL. Returns path to audio file."""
        ...


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file to timestamped text."""
        ...


class QAEngine(Protocol):
    def ask(self, transcript: str, question: str, history: list[Message]) -> str:
        """Answer a question given a transcript and conversation history."""
        ...


class Store(Protocol):
    def lookup(self, transcript_hash: TranscriptHash) -> Transcript | None:
        """Look up a cached transcript by its hashed ID. Returns None if not found."""
        ...

    def save(self, transcript_hash: TranscriptHash, video_id: VideoID, url: VideoURL, text: str, source: str) -> Transcript:
        """Save a transcript to disk, keyed by the hashed ID."""
        ...

    def save_session(self, session: Session) -> Path:
        """Save a conversation session to disk."""
        ...

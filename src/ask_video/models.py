import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import NewType

# --- Domain Types ---
VideoURL = NewType("VideoURL", str)
VideoID = NewType("VideoID", str)
TranscriptHash = NewType("TranscriptHash", str)


def generate_transcript_hash(video_id: VideoID) -> TranscriptHash:
    """Generate a stable, filesystem-friendly hash from a canonical Video ID."""
    hashed = hashlib.sha256(video_id.encode("utf-8")).hexdigest()[:16]
    return TranscriptHash(hashed)


# --- Entities ---
@dataclass
class Transcript:
    id: TranscriptHash
    video_id: VideoID
    url: VideoURL
    text: str
    created_at: datetime
    source: str  # "youtube_captions" | "whisper"
    path: Path


@dataclass
class Session:
    id: str
    transcript_id: TranscriptHash
    started_at: datetime
    messages: list[dict] = field(default_factory=list)

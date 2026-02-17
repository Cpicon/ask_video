from datetime import datetime, timezone
from pathlib import Path

from ask_video.models import (
    Transcript, Session, VideoURL, VideoID, TranscriptHash,
    generate_transcript_hash,
)


def test_transcript_creation():
    t = Transcript(
        id=TranscriptHash("a1b2c3d4e5f6g7h8"),
        video_id=VideoID("dQw4w9WgXcQ"),
        url=VideoURL("https://youtube.com/watch?v=dQw4w9WgXcQ"),
        text="Hello world",
        created_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        source="youtube_captions",
        path=Path(".ask_video/transcripts/a1b2c3d4e5f6g7h8"),
    )
    assert t.id == "a1b2c3d4e5f6g7h8"
    assert t.video_id == "dQw4w9WgXcQ"
    assert t.url == "https://youtube.com/watch?v=dQw4w9WgXcQ"
    assert t.text == "Hello world"
    assert t.source == "youtube_captions"


def test_generate_transcript_hash_is_deterministic():
    vid = VideoID("dQw4w9WgXcQ")
    h1 = generate_transcript_hash(vid)
    h2 = generate_transcript_hash(vid)
    assert h1 == h2
    assert len(h1) == 16  # 16 hex chars


def test_generate_transcript_hash_differs_for_different_ids():
    h1 = generate_transcript_hash(VideoID("aaaaaaaaaaa"))
    h2 = generate_transcript_hash(VideoID("bbbbbbbbbbb"))
    assert h1 != h2


def test_session_creation():
    s = Session(
        id="sess001",
        transcript_id=TranscriptHash("a1b2c3d4e5f6g7h8"),
        started_at=datetime(2026, 2, 15, 10, 30, tzinfo=timezone.utc),
        messages=[],
    )
    assert s.id == "sess001"
    assert s.transcript_id == "a1b2c3d4e5f6g7h8"
    assert s.messages == []


def test_session_add_messages():
    s = Session(
        id="sess001",
        transcript_id=TranscriptHash("a1b2c3d4e5f6g7h8"),
        started_at=datetime(2026, 2, 15, 10, 30, tzinfo=timezone.utc),
        messages=[],
    )
    s.messages.append({"role": "user", "content": "What is this about?"})
    s.messages.append({"role": "assistant", "content": "This is about..."})
    assert len(s.messages) == 2
    assert s.messages[0]["role"] == "user"
    assert s.messages[1]["role"] == "assistant"

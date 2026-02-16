import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ask_video.store import TranscriptStore
from ask_video.models import (
    Transcript, Session, VideoURL, VideoID, TranscriptHash,
    generate_transcript_hash,
)


@pytest.fixture
def store(tmp_path: Path) -> TranscriptStore:
    return TranscriptStore(base_dir=tmp_path / ".ask_video")


def test_store_initializes_directory(store: TranscriptStore):
    assert store.base_dir.exists()


def test_lookup_returns_none_for_unknown_hash(store: TranscriptStore):
    assert store.lookup(TranscriptHash("0000000000000000")) is None


def test_save_and_lookup_transcript(store: TranscriptStore):
    video_id = VideoID("dQw4w9WgXcQ")
    t_hash = generate_transcript_hash(video_id)

    transcript = store.save(
        transcript_hash=t_hash,
        video_id=video_id,
        url=VideoURL("https://youtube.com/watch?v=dQw4w9WgXcQ"),
        text="Hello world transcript",
        source="youtube_captions",
    )
    assert transcript.id == t_hash
    assert transcript.video_id == "dQw4w9WgXcQ"
    assert transcript.text == "Hello world transcript"
    assert transcript.path.exists()

    # Lookup by hash should find it
    loaded = store.lookup(t_hash)
    assert loaded is not None
    assert loaded.id == transcript.id
    assert loaded.video_id == "dQw4w9WgXcQ"
    assert loaded.text == "Hello world transcript"


def test_lookup_returns_none_when_transcript_dir_deleted(store: TranscriptStore):
    video_id = VideoID("abc123def78")
    t_hash = generate_transcript_hash(video_id)

    transcript = store.save(
        transcript_hash=t_hash,
        video_id=video_id,
        url=VideoURL("https://youtube.com/watch?v=abc123def78"),
        text="Some text",
        source="youtube_captions",
    )
    shutil.rmtree(transcript.path)

    assert store.lookup(t_hash) is None


def test_save_session(store: TranscriptStore):
    video_id = VideoID("dQw4w9WgXcQ")
    t_hash = generate_transcript_hash(video_id)

    transcript = store.save(
        transcript_hash=t_hash,
        video_id=video_id,
        url=VideoURL("https://youtube.com/watch?v=dQw4w9WgXcQ"),
        text="Hello world",
        source="youtube_captions",
    )
    session = Session(
        id="sess001",
        transcript_id=transcript.id,
        started_at=datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
        messages=[
            {"role": "user", "content": "What is this?"},
            {"role": "assistant", "content": "This is a greeting."},
        ],
    )
    store.save_session(session)

    sessions_dir = transcript.path / "sessions"
    assert sessions_dir.exists()
    session_files = list(sessions_dir.glob("*.json"))
    assert len(session_files) == 1

    saved = json.loads(session_files[0].read_text())
    assert saved["id"] == "sess001"
    assert len(saved["messages"]) == 2

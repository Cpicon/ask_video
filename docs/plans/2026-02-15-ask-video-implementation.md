# ask_video Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI that takes a YouTube URL, obtains its transcript, and opens an interactive REPL for Q&A about the video content using an LLM.

**Architecture:** Layered pipeline with Protocol-based abstractions (VideoSource → Transcriber → TranscriptStore → QAEngine → REPL). Each layer has a concrete implementation behind a Protocol, resolved by factory functions. Constructor injection, no DI framework.

**Tech Stack:** Python 3.12+, Typer, Rich, yt-dlp, youtube-transcript-api, openai-whisper, google-genai, pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/ask_video/__init__.py`
- Create: `src/ask_video/sources/__init__.py`
- Create: `src/ask_video/transcribers/__init__.py`
- Create: `src/ask_video/engines/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

**Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ask-video"
version = "0.1.0"
description = "Ask questions about YouTube videos using AI"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.9",
    "rich>=13.0",
    "yt-dlp>=2024.0",
    "youtube-transcript-api>=0.6",
    "google-genai>=1.0",
]

[project.optional-dependencies]
whisper = ["openai-whisper>=20230918"]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[project.scripts]
ask_video = "ask_video.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/ask_video"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Create package `__init__.py` files**

`src/ask_video/__init__.py`:
```python
"""ask_video — Ask questions about YouTube videos using AI."""
```

`src/ask_video/sources/__init__.py`, `src/ask_video/transcribers/__init__.py`, `src/ask_video/engines/__init__.py`, `tests/__init__.py`: all empty files.

**Step 3: Create `.gitignore`**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.env
.ask_video/
```

**Step 4: Install the project in dev mode**

Run: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: Installs successfully, `ask_video` command available (will fail since cli.py doesn't exist yet — that's fine).

**Step 5: Commit**

```bash
git add pyproject.toml src/ tests/__init__.py .gitignore
git commit -m "chore: scaffold project structure with pyproject.toml"
```

---

### Task 2: Data Models & Domain Types

**Files:**
- Create: `src/ask_video/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

`tests/test_models.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ask_video.models'`

**Step 3: Write minimal implementation**

`src/ask_video/models.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/models.py tests/test_models.py
git commit -m "feat: add domain types (VideoURL, VideoID, TranscriptHash) and data models"
```

---

### Task 3: Protocols

**Files:**
- Create: `src/ask_video/protocols.py`

**Step 1: Write the protocols**

`src/ask_video/protocols.py`:
```python
from pathlib import Path
from typing import Protocol

from ask_video.models import (
    Transcript, Session, VideoURL, VideoID, TranscriptHash,
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
    def ask(self, transcript: str, question: str, history: list[dict]) -> str:
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
```

No tests needed for Protocol definitions — they're just type contracts. They get tested implicitly when we test the concrete implementations.

**Step 2: Commit**

```bash
git add src/ask_video/protocols.py
git commit -m "feat: define VideoSource, Transcriber, QAEngine, Store protocols"
```

---

### Task 4: TranscriptStore

**Files:**
- Create: `src/ask_video/store.py`
- Create: `tests/test_store.py`

**Step 1: Write the failing tests**

`tests/test_store.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ask_video.store'`

**Step 3: Write minimal implementation**

Note: No `metadata.json` needed. `TranscriptHash` is deterministic, so lookup simply checks if the directory exists. This eliminates race conditions and cache corruption entirely.

`src/ask_video/store.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path

from ask_video.models import (
    Transcript, Session, VideoURL, VideoID, TranscriptHash,
)


class TranscriptStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(".ask_video")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def lookup(self, transcript_hash: TranscriptHash) -> Transcript | None:
        transcript_dir = self.base_dir / "transcripts" / transcript_hash
        if not transcript_dir.exists():
            return None
        text = (transcript_dir / "transcript.txt").read_text()
        info = json.loads((transcript_dir / "info.json").read_text())
        return Transcript(
            id=transcript_hash,
            video_id=VideoID(info["video_id"]),
            url=VideoURL(info["url"]),
            text=text,
            created_at=datetime.fromisoformat(info["created_at"]),
            source=info["source"],
            path=transcript_dir,
        )

    def save(
        self,
        transcript_hash: TranscriptHash,
        video_id: VideoID,
        url: VideoURL,
        text: str,
        source: str,
    ) -> Transcript:
        transcript_dir = self.base_dir / "transcripts" / transcript_hash
        transcript_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)

        (transcript_dir / "transcript.txt").write_text(text)
        (transcript_dir / "info.json").write_text(
            json.dumps({
                "video_id": video_id,
                "url": url,
                "created_at": now.isoformat(),
                "source": source,
            }, indent=2)
        )

        return Transcript(
            id=transcript_hash,
            video_id=video_id,
            url=url,
            text=text,
            created_at=now,
            source=source,
            path=transcript_dir,
        )

    def save_session(self, session: Session) -> Path:
        transcript_dir = self.base_dir / "transcripts" / session.transcript_id
        sessions_dir = transcript_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        date_str = session.started_at.strftime("%Y-%m-%d")
        filename = f"{date_str}_{session.id}.json"
        path = sessions_dir / filename
        path.write_text(
            json.dumps({
                "id": session.id,
                "transcript_id": session.transcript_id,
                "started_at": session.started_at.isoformat(),
                "messages": session.messages,
            }, indent=2)
        )
        return path
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_store.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/store.py tests/test_store.py
git commit -m "feat: add TranscriptStore with hash-based lookup, no index file"
```

---

### Task 5: YouTube VideoSource

**Files:**
- Create: `src/ask_video/sources/youtube.py`
- Create: `tests/test_sources_youtube.py`

**Step 1: Write the failing tests**

`tests/test_sources_youtube.py`:
```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.sources.youtube import YouTubeSource


@pytest.fixture
def source() -> YouTubeSource:
    return YouTubeSource()


def test_extract_id_standard_url(source):
    assert source.extract_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_short_url(source):
    assert source.extract_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_with_extra_params(source):
    assert source.extract_id("https://youtube.com/watch?v=dQw4w9WgXcQ&t=10") == "dQw4w9WgXcQ"


def test_extract_id_v_not_first_param(source):
    assert source.extract_id("https://youtube.com/watch?app=desktop&v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_shorts_url(source):
    assert source.extract_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_embed_url(source):
    assert source.extract_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_invalid(source):
    with pytest.raises(ValueError, match="Could not extract video ID"):
        source.extract_id("https://example.com/not-youtube")


@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_fetch_transcript_returns_timestamped_captions(mock_api, source):
    mock_api.get_transcript.return_value = [
        {"text": "Hello", "start": 0.0, "duration": 1.0},
        {"text": "world", "start": 65.0, "duration": 1.0},
    ]
    result = source.fetch_transcript("https://youtube.com/watch?v=abc123def78")
    assert result == "[0:00] Hello\n[1:05] world"
    mock_api.get_transcript.assert_called_once_with("abc123def78")


@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_fetch_transcript_returns_none_when_no_captions(mock_api, source):
    mock_api.get_transcript.side_effect = Exception("No transcript")
    result = source.fetch_transcript("https://youtube.com/watch?v=abc123def78")
    assert result is None


@patch("ask_video.sources.youtube.yt_dlp")
def test_download_audio(mock_ytdlp, source, tmp_path):
    mock_ydl = MagicMock()
    mock_ytdlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ytdlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

    # Simulate yt-dlp creating the audio file
    expected_path = tmp_path / "abc123def78.m4a"
    expected_path.write_bytes(b"fake audio")
    mock_ydl.prepare_filename.return_value = str(expected_path)

    result = source.download_audio("https://youtube.com/watch?v=abc123def78", tmp_path)
    assert result == expected_path
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sources_youtube.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`src/ask_video/sources/youtube.py`:
```python
import re
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from ask_video.models import VideoURL, VideoID


def _format_ts(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class YouTubeSource:
    _VIDEO_ID_PATTERN = re.compile(
        r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/)([a-zA-Z0-9_-]{11})"
    )

    def extract_id(self, url: VideoURL) -> VideoID:
        match = self._VIDEO_ID_PATTERN.search(url)
        if match:
            return VideoID(match.group(1))
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def fetch_transcript(self, url: VideoURL) -> str | None:
        video_id = self.extract_id(url)
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id)
            return "\n".join(
                f"[{_format_ts(entry['start'])}] {entry['text']}"
                for entry in entries
            )
        except Exception:
            return None

    def download_audio(self, url: VideoURL, output_dir: Path) -> Path:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return Path(filename)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sources_youtube.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/sources/youtube.py tests/test_sources_youtube.py
git commit -m "feat: add YouTubeSource with timestamped captions and broad URL parsing"
```

---

### Task 6: Whisper Transcriber

**Files:**
- Create: `src/ask_video/transcribers/whisper.py`
- Create: `tests/test_transcribers_whisper.py`

**Step 1: Write the failing test**

`tests/test_transcribers_whisper.py`:
```python
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.transcribers.whisper import WhisperTranscriber


def test_transcribe_returns_timestamped_text(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    mock_whisper = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {
        "text": "Hello world",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": " Hello"},
            {"start": 65.0, "end": 67.0, "text": " world"},
        ],
    }

    with patch.dict("sys.modules", {"whisper": mock_whisper}):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            transcriber = WhisperTranscriber(model_name="base")
            result = transcriber.transcribe(audio_file)

    assert result == "[0:00] Hello\n[1:05] world"
    mock_whisper.load_model.assert_called_once_with("base")


def test_transcribe_default_model():
    transcriber = WhisperTranscriber()
    assert transcriber.model_name == "base"


def test_transcribe_raises_when_whisper_not_installed(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    with patch.dict("sys.modules", {"whisper": None}):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            transcriber = WhisperTranscriber()
            with pytest.raises(RuntimeError, match="pip install"):
                transcriber.transcribe(audio_file)


def test_transcribe_raises_when_ffmpeg_missing(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    with patch("shutil.which", return_value=None):
        transcriber = WhisperTranscriber()
        with pytest.raises(RuntimeError, match="ffmpeg"):
            transcriber.transcribe(audio_file)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_transcribers_whisper.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Note: Both `import whisper` and `ffmpeg` availability are checked lazily at transcription time, not at import time.

`src/ask_video/transcribers/whisper.py`:
```python
import shutil
from pathlib import Path


def _format_ts(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import whisper
            except ImportError:
                raise RuntimeError(
                    "Whisper is not installed. Install with: pip install 'ask-video[whisper]'"
                )
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg is required for audio transcription but was not found. "
                "Install it: https://ffmpeg.org/download.html"
            )
        model = self._get_model()
        result = model.transcribe(str(audio_path))
        return "\n".join(
            f"[{_format_ts(seg['start'])}]{seg['text']}"
            for seg in result["segments"]
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_transcribers_whisper.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/transcribers/whisper.py tests/test_transcribers_whisper.py
git commit -m "feat: add WhisperTranscriber with timestamps, ffmpeg check, and deferred import"
```

---

### Task 7: Gemini QAEngine

**Files:**
- Create: `src/ask_video/engines/gemini.py`
- Create: `tests/test_engines_gemini.py`

**Step 1: Write the failing test**

`tests/test_engines_gemini.py`:
```python
import os
from unittest.mock import patch, MagicMock, call

import pytest

from ask_video.engines.gemini import GeminiEngine


@patch("ask_video.engines.gemini.genai")
def test_ask_sends_transcript_and_question(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "The video discusses Python programming."
    mock_client.models.generate_content.return_value = mock_response

    engine = GeminiEngine(api_key="test-key", model="gemini-2.0-flash")
    result = engine.ask(
        transcript="Welcome to the Python tutorial...",
        question="What is this video about?",
        history=[],
    )

    assert result == "The video discusses Python programming."

    # Verify system_instruction is in config, not in contents
    call_kwargs = mock_client.models.generate_content.call_args
    contents = call_kwargs.kwargs["contents"]
    assert len(contents) == 1  # Only the user question, no system prompt in contents
    assert contents[0]["role"] == "user"
    assert call_kwargs.kwargs["config"].system_instruction is not None


@patch("ask_video.engines.gemini.genai")
def test_ask_includes_conversation_history(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "As I mentioned, it covers decorators."
    mock_client.models.generate_content.return_value = mock_response

    engine = GeminiEngine(api_key="test-key", model="gemini-2.0-flash")
    history = [
        {"role": "user", "content": "What is this about?"},
        {"role": "assistant", "content": "This is about Python."},
    ]
    result = engine.ask(
        transcript="Advanced Python decorators...",
        question="Can you elaborate?",
        history=history,
    )

    assert result == "As I mentioned, it covers decorators."

    # Verify history produces alternating user/model roles
    call_kwargs = mock_client.models.generate_content.call_args
    contents = call_kwargs.kwargs["contents"]
    roles = [c["role"] for c in contents]
    assert roles == ["user", "model", "user"]  # history user, history model, new question


def test_gemini_engine_raises_without_api_key():
    with pytest.raises(ValueError, match="API key"):
        GeminiEngine(api_key="", model="gemini-2.0-flash")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_engines_gemini.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Note: System prompt goes in `GenerateContentConfig.system_instruction`, NOT as a user message. Sending it as a user message causes consecutive user roles which crashes the Gemini API with 400.

`src/ask_video/engines/gemini.py`:
```python
from google import genai
from google.genai import types


class GeminiEngine:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("API key is required. Set GEMINI_API_KEY environment variable.")
        self.model = model
        self._client = genai.Client(api_key=api_key)

    def ask(self, transcript: str, question: str, history: list[dict]) -> str:
        system_prompt = (
            "You are a helpful assistant that answers questions about a video. "
            "Use the following transcript to answer the user's question. "
            "If the answer is not in the transcript, say so.\n\n"
            f"TRANSCRIPT:\n{transcript}"
        )

        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": question}]})

        response = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_engines_gemini.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/engines/gemini.py tests/test_engines_gemini.py
git commit -m "feat: add GeminiEngine with system_instruction config"
```

---

### Task 8: Factory Functions

**Files:**
- Create: `src/ask_video/factory.py`
- Create: `tests/test_factory.py`

**Step 1: Write the failing test**

Note: Tests import concrete classes for `isinstance` checks, but the factory itself defers imports so that optional dependencies (like whisper) don't crash the CLI on startup.

`tests/test_factory.py`:
```python
from unittest.mock import patch

import pytest

from ask_video.factory import create_source, create_transcriber, create_engine


def test_create_source_returns_youtube():
    from ask_video.sources.youtube import YouTubeSource
    source = create_source("youtube")
    assert isinstance(source, YouTubeSource)


def test_create_source_unknown_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        create_source("vimeo")


def test_create_transcriber_returns_whisper():
    from ask_video.transcribers.whisper import WhisperTranscriber
    transcriber = create_transcriber("whisper")
    assert isinstance(transcriber, WhisperTranscriber)


def test_create_transcriber_unknown_raises():
    with pytest.raises(ValueError, match="Unknown transcriber"):
        create_transcriber("deepgram")


def test_create_engine_returns_gemini():
    from ask_video.engines.gemini import GeminiEngine
    engine = create_engine("gemini", api_key="test-key")
    assert isinstance(engine, GeminiEngine)


def test_create_engine_unknown_raises():
    with pytest.raises(ValueError, match="Unknown engine"):
        create_engine("openai", api_key="test-key")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_factory.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Note: All imports are deferred inside factory functions. This prevents `import whisper` from crashing the CLI when whisper is not installed (it's an optional dependency).

`src/ask_video/factory.py`:
```python
def create_source(name: str = "youtube"):
    if name == "youtube":
        from ask_video.sources.youtube import YouTubeSource
        return YouTubeSource()
    raise ValueError(f"Unknown source: {name}. Available: ['youtube']")


def create_transcriber(name: str = "whisper"):
    if name == "whisper":
        from ask_video.transcribers.whisper import WhisperTranscriber
        return WhisperTranscriber()
    raise ValueError(f"Unknown transcriber: {name}. Available: ['whisper']")


def create_engine(name: str = "gemini", **kwargs):
    if name == "gemini":
        from ask_video.engines.gemini import GeminiEngine
        return GeminiEngine(**kwargs)
    raise ValueError(f"Unknown engine: {name}. Available: ['gemini']")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_factory.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/factory.py tests/test_factory.py
git commit -m "feat: add factory functions with deferred imports for optional deps"
```

---

### Task 9: CLI + REPL

**Files:**
- Create: `src/ask_video/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

`tests/test_cli.py`:
```python
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ask_video.cli import app
from ask_video.models import VideoID, generate_transcript_hash


runner = CliRunner()


@patch.dict(os.environ, {"GEMINI_API_KEY": ""})
def test_cli_missing_api_key():
    result = runner.invoke(app, ["https://youtube.com/watch?v=dQw4w9WgXcQ"])
    assert result.exit_code != 0
    assert "GEMINI_API_KEY" in result.output


@patch("ask_video.cli.run_session")
@patch("ask_video.cli.create_engine")
@patch("ask_video.cli.create_source")
@patch("ask_video.cli.TranscriptStore")
@patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
def test_cli_loads_cached_transcript(mock_store_cls, mock_source_fn, mock_engine, mock_run):
    mock_store = MagicMock()
    mock_store_cls.return_value = mock_store
    mock_source = MagicMock()
    mock_source_fn.return_value = mock_source
    mock_source.extract_id.return_value = VideoID("dQw4w9WgXcQ")
    expected_hash = generate_transcript_hash(VideoID("dQw4w9WgXcQ"))
    mock_transcript = MagicMock()
    mock_transcript.text = "cached text"
    mock_transcript.id = expected_hash
    mock_store.lookup.return_value = mock_transcript

    result = runner.invoke(app, ["https://youtube.com/watch?v=dQw4w9WgXcQ"])
    assert result.exit_code == 0
    mock_store.lookup.assert_called_once_with(expected_hash)
    mock_run.assert_called_once()


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
@patch("ask_video.cli.create_source")
@patch("ask_video.cli.TranscriptStore")
def test_cli_invalid_url_shows_clean_error(mock_store_cls, mock_source_fn):
    mock_source = MagicMock()
    mock_source_fn.return_value = mock_source
    mock_source.extract_id.side_effect = ValueError("Could not extract video ID")

    result = runner.invoke(app, ["https://example.com/not-youtube"])
    assert result.exit_code != 0
    assert "Could not extract video ID" in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`src/ask_video/cli.py`:
```python
import os
import uuid
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.panel import Panel

from ask_video.factory import create_source, create_transcriber, create_engine
from ask_video.models import VideoURL, Session, generate_transcript_hash
from ask_video.store import TranscriptStore

app = typer.Typer(help="Ask questions about YouTube videos using AI.")
console = Console()


def run_session(transcript_text: str, engine, store: TranscriptStore, transcript_id: str):
    session = Session(
        id=uuid.uuid4().hex[:8],
        transcript_id=transcript_id,
        started_at=datetime.now(timezone.utc),
        messages=[],
    )

    console.print(Panel("Ready! Ask questions about the video. Type 'exit' or Ctrl+C to quit.", style="green"))

    try:
        while True:
            question = console.input("[bold cyan]You:[/bold cyan] ").strip()
            if not question or question.lower() in ("exit", "quit"):
                break

            try:
                answer = engine.ask(transcript_text, question, session.messages)
            except Exception as e:
                console.print(f"[bold red]API Error:[/bold red] {e}")
                console.print("[dim]Retrying...[/dim]")
                try:
                    answer = engine.ask(transcript_text, question, session.messages)
                except Exception as retry_err:
                    console.print(f"[bold red]Retry failed:[/bold red] {retry_err}")
                    console.print("[dim]Please try again.[/dim]")
                    continue

            session.messages.append({"role": "user", "content": question})
            session.messages.append({"role": "assistant", "content": answer})

            console.print(f"\n[bold green]Assistant:[/bold green] {answer}\n")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Exiting...[/dim]")
    finally:
        if session.messages:
            store.save_session(session)
            console.print(f"[dim]Session saved ({len(session.messages) // 2} exchanges).[/dim]")


@app.command()
def main(
    url_input: str = typer.Argument(help="YouTube video URL"),
    transcriber_name: str = typer.Option("whisper", "--transcriber", "-t", help="Transcriber to use"),
    model: str = typer.Option("gemini-2.0-flash", "--model", "-m", help="LLM model name"),
):
    """Load a YouTube video and ask questions about it."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable is not set.[/red]")
        raise typer.Exit(code=1)

    store = TranscriptStore()
    source = create_source("youtube")

    # 1. Cast input string to domain type
    url = VideoURL(url_input)

    # 2. Extract canonical video ID (validates URL)
    try:
        video_id = source.extract_id(url)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # 3. Compute deterministic hash for storage lookup
    transcript_hash = generate_transcript_hash(video_id)

    # 4. Check cache using the hash
    transcript = store.lookup(transcript_hash)
    if transcript:
        console.print("[dim]Loaded cached transcript.[/dim]")
    else:
        console.print("[dim]Fetching transcript...[/dim]")
        text = source.fetch_transcript(url)

        if text:
            console.print("[dim]Found YouTube captions.[/dim]")
            transcript = store.save(
                transcript_hash=transcript_hash,
                video_id=video_id,
                url=url,
                text=text,
                source="youtube_captions",
            )
        else:
            console.print("[dim]No captions found. Downloading audio for transcription...[/dim]")
            transcriber = create_transcriber(transcriber_name)
            audio_path = source.download_audio(url, store.base_dir / "tmp")
            try:
                console.print(f"[dim]Transcribing with {transcriber_name}...[/dim]")
                text = transcriber.transcribe(audio_path)
                transcript = store.save(
                    transcript_hash=transcript_hash,
                    video_id=video_id,
                    url=url,
                    text=text,
                    source=transcriber_name,
                )
            finally:
                audio_path.unlink(missing_ok=True)

    engine = create_engine("gemini", api_key=api_key, model=model)
    run_session(transcript.text, engine, store, transcript.id)


if __name__ == "__main__":
    app()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/cli.py tests/test_cli.py
git commit -m "feat: add CLI with error handling, retry logic, and audio cleanup"
```

---

### Task 10: Integration Smoke Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

This test verifies the full pipeline works end-to-end using mocks for external services (no real API calls). It exercises the video_id extraction, cache key deduplication, and Gemini system_instruction config.

`tests/test_integration.py`:
```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.store import TranscriptStore
from ask_video.sources.youtube import YouTubeSource
from ask_video.engines.gemini import GeminiEngine
from ask_video.models import VideoURL, generate_transcript_hash


@patch("ask_video.engines.gemini.genai")
@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_full_pipeline_with_captions(mock_yt_api, mock_genai, tmp_path):
    # 1. YouTube captions exist
    mock_yt_api.get_transcript.return_value = [
        {"text": "Welcome to the tutorial", "start": 0.0, "duration": 2.0},
        {"text": "Today we learn Python", "start": 2.0, "duration": 2.0},
    ]

    # 2. Gemini returns an answer
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "The video is a Python tutorial."
    mock_client.models.generate_content.return_value = mock_response

    # Pipeline
    source = YouTubeSource()
    store = TranscriptStore(base_dir=tmp_path / ".ask_video")

    url = VideoURL("https://youtube.com/watch?v=test123test1")
    video_id = source.extract_id(url)
    assert video_id == "test123test1"

    transcript_hash = generate_transcript_hash(video_id)

    text = source.fetch_transcript(url)
    assert text is not None

    transcript = store.save(
        transcript_hash=transcript_hash,
        video_id=video_id,
        url=url,
        text=text,
        source="youtube_captions",
    )
    assert transcript.id == transcript_hash
    assert transcript.video_id == "test123test1"
    assert transcript.text == "[0:00] Welcome to the tutorial\n[0:02] Today we learn Python"

    engine = GeminiEngine(api_key="test-key")
    answer = engine.ask(transcript.text, "What is this video about?", history=[])
    assert answer == "The video is a Python tutorial."

    # Verify transcript is cached by hash
    cached = store.lookup(transcript_hash)
    assert cached is not None
    assert cached.id == transcript.id

    # Verify that a different URL for the same video produces the same hash
    alt_url = VideoURL("https://youtu.be/test123test1")
    alt_video_id = source.extract_id(alt_url)
    alt_hash = generate_transcript_hash(alt_video_id)
    assert alt_hash == transcript_hash  # Same video → same hash
    cached_again = store.lookup(alt_hash)
    assert cached_again is not None
    assert cached_again.id == transcript.id
```

**Step 2: Run test**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke test with video_id cache deduplication"
```

---

### Task 11: Final Polish

**Files:**
- Modify: `pyproject.toml` (if any dependency adjustments needed)
- Modify: `.gitignore` (ensure `.ask_video/` is listed)

**Step 1: Verify the CLI runs**

Run: `ask_video --help`
Expected: Shows help text with usage, arguments, and options.

**Step 2: Run full test suite with coverage**

Run: `pytest tests/ -v --cov=ask_video --cov-report=term-missing`
Expected: All tests pass, reasonable coverage across modules.

**Step 3: Final commit if any adjustments were needed**

```bash
git add -A
git commit -m "chore: final polish and cleanup"
```

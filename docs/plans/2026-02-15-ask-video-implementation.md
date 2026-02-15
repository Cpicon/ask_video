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

### Task 2: Data Models

**Files:**
- Create: `src/ask_video/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

`tests/test_models.py`:
```python
from datetime import datetime, timezone
from pathlib import Path

from ask_video.models import Transcript, Session


def test_transcript_creation():
    t = Transcript(
        id="abc123",
        url="https://youtube.com/watch?v=xyz",
        text="Hello world",
        created_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        source="youtube_captions",
        path=Path(".ask_video/transcripts/abc123"),
    )
    assert t.id == "abc123"
    assert t.url == "https://youtube.com/watch?v=xyz"
    assert t.text == "Hello world"
    assert t.source == "youtube_captions"


def test_session_creation():
    s = Session(
        id="sess001",
        transcript_id="abc123",
        started_at=datetime(2026, 2, 15, 10, 30, tzinfo=timezone.utc),
        messages=[],
    )
    assert s.id == "sess001"
    assert s.transcript_id == "abc123"
    assert s.messages == []


def test_session_add_messages():
    s = Session(
        id="sess001",
        transcript_id="abc123",
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
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Transcript:
    id: str
    url: str
    text: str
    created_at: datetime
    source: str  # "youtube_captions" | "whisper"
    path: Path


@dataclass
class Session:
    id: str
    transcript_id: str
    started_at: datetime
    messages: list[dict] = field(default_factory=list)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/models.py tests/test_models.py
git commit -m "feat: add Transcript and Session data models"
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


class VideoSource(Protocol):
    def fetch_transcript(self, url: str) -> str | None:
        """Try to get an existing transcript. Returns None if unavailable."""
        ...

    def download_audio(self, url: str, output_dir: Path) -> Path:
        """Download audio from the video URL. Returns path to audio file."""
        ...


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file to text."""
        ...


class QAEngine(Protocol):
    def ask(self, transcript: str, question: str, history: list[dict]) -> str:
        """Answer a question given a transcript and conversation history."""
        ...
```

No tests needed for Protocol definitions — they're just type contracts. They get tested implicitly when we test the concrete implementations.

**Step 2: Commit**

```bash
git add src/ask_video/protocols.py
git commit -m "feat: define VideoSource, Transcriber, QAEngine protocols"
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
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ask_video.store import TranscriptStore
from ask_video.models import Transcript, Session


@pytest.fixture
def store(tmp_path: Path) -> TranscriptStore:
    return TranscriptStore(base_dir=tmp_path / ".ask_video")


def test_store_initializes_directory(store: TranscriptStore):
    assert store.base_dir.exists()
    assert (store.base_dir / "metadata.json").exists()


def test_lookup_returns_none_for_unknown_url(store: TranscriptStore):
    assert store.lookup("https://youtube.com/watch?v=unknown") is None


def test_save_and_lookup_transcript(store: TranscriptStore):
    transcript = store.save(
        url="https://youtube.com/watch?v=abc",
        text="Hello world transcript",
        source="youtube_captions",
    )
    assert transcript.url == "https://youtube.com/watch?v=abc"
    assert transcript.text == "Hello world transcript"
    assert transcript.source == "youtube_captions"
    assert transcript.path.exists()

    # Lookup should find it
    loaded = store.lookup("https://youtube.com/watch?v=abc")
    assert loaded is not None
    assert loaded.id == transcript.id
    assert loaded.text == "Hello world transcript"


def test_save_session(store: TranscriptStore):
    transcript = store.save(
        url="https://youtube.com/watch?v=abc",
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

`src/ask_video/store.py`:
```python
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ask_video.models import Transcript, Session


class TranscriptStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(".ask_video")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.base_dir / "metadata.json"
        if not self._metadata_path.exists():
            self._metadata_path.write_text("{}")

    def _read_metadata(self) -> dict:
        return json.loads(self._metadata_path.read_text())

    def _write_metadata(self, data: dict) -> None:
        self._metadata_path.write_text(json.dumps(data, indent=2))

    def lookup(self, url: str) -> Transcript | None:
        metadata = self._read_metadata()
        if url not in metadata:
            return None
        entry = metadata[url]
        transcript_dir = self.base_dir / "transcripts" / entry["id"]
        text = (transcript_dir / "transcript.txt").read_text()
        info = json.loads((transcript_dir / "info.json").read_text())
        return Transcript(
            id=entry["id"],
            url=url,
            text=text,
            created_at=datetime.fromisoformat(info["created_at"]),
            source=info["source"],
            path=transcript_dir,
        )

    def save(self, url: str, text: str, source: str) -> Transcript:
        transcript_id = uuid.uuid4().hex[:12]
        transcript_dir = self.base_dir / "transcripts" / transcript_id
        transcript_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)

        (transcript_dir / "transcript.txt").write_text(text)
        (transcript_dir / "info.json").write_text(
            json.dumps({
                "url": url,
                "created_at": now.isoformat(),
                "source": source,
            }, indent=2)
        )

        metadata = self._read_metadata()
        metadata[url] = {"id": transcript_id}
        self._write_metadata(metadata)

        return Transcript(
            id=transcript_id,
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
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/store.py tests/test_store.py
git commit -m "feat: add TranscriptStore with metadata index and session persistence"
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


def test_extract_video_id():
    source = YouTubeSource()
    assert source._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert source._extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert source._extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ&t=10") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid():
    source = YouTubeSource()
    with pytest.raises(ValueError, match="Could not extract video ID"):
        source._extract_video_id("https://example.com/not-youtube")


@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_fetch_transcript_returns_captions(mock_api, source):
    mock_api.get_transcript.return_value = [
        {"text": "Hello", "start": 0.0, "duration": 1.0},
        {"text": "world", "start": 1.0, "duration": 1.0},
    ]
    result = source.fetch_transcript("https://youtube.com/watch?v=abc123")
    assert result == "Hello\nworld"
    mock_api.get_transcript.assert_called_once_with("abc123")


@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_fetch_transcript_returns_none_when_no_captions(mock_api, source):
    mock_api.get_transcript.side_effect = Exception("No transcript")
    result = source.fetch_transcript("https://youtube.com/watch?v=abc123")
    assert result is None


@patch("ask_video.sources.youtube.yt_dlp")
def test_download_audio(mock_ytdlp, source, tmp_path):
    mock_ydl = MagicMock()
    mock_ytdlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ytdlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)

    # Simulate yt-dlp creating the audio file
    expected_path = tmp_path / "abc123.m4a"
    expected_path.write_bytes(b"fake audio")
    mock_ydl.prepare_filename.return_value = str(expected_path)

    result = source.download_audio("https://youtube.com/watch?v=abc123", tmp_path)
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


class YouTubeSource:
    def _extract_video_id(self, url: str) -> str:
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def fetch_transcript(self, url: str) -> str | None:
        video_id = self._extract_video_id(url)
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id)
            return "\n".join(entry["text"] for entry in entries)
        except Exception:
            return None

    def download_audio(self, url: str, output_dir: Path) -> Path:
        video_id = self._extract_video_id(url)
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
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/sources/youtube.py tests/test_sources_youtube.py
git commit -m "feat: add YouTubeSource with caption fetching and audio download"
```

---

### Task 6: Whisper Transcriber

**Files:**
- Create: `src/ask_video/transcribers/whisper.py`
- Create: `tests/test_transcribers_whisper.py`

**Step 1: Write the failing test**

`tests/test_transcribers_whisper.py`:
```python
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.transcribers.whisper import WhisperTranscriber


@patch("ask_video.transcribers.whisper.whisper")
def test_transcribe_returns_text(mock_whisper, tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {"text": "This is the transcribed text."}

    transcriber = WhisperTranscriber(model_name="base")
    result = transcriber.transcribe(audio_file)

    assert result == "This is the transcribed text."
    mock_whisper.load_model.assert_called_once_with("base")
    mock_model.transcribe.assert_called_once_with(str(audio_file))


@patch("ask_video.transcribers.whisper.whisper")
def test_transcribe_default_model(mock_whisper):
    transcriber = WhisperTranscriber()
    assert transcriber.model_name == "base"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_transcribers_whisper.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`src/ask_video/transcribers/whisper.py`:
```python
from pathlib import Path

import whisper


class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        model = self._get_model()
        result = model.transcribe(str(audio_path))
        return result["text"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_transcribers_whisper.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/transcribers/whisper.py tests/test_transcribers_whisper.py
git commit -m "feat: add WhisperTranscriber with lazy model loading"
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
from unittest.mock import patch, MagicMock

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
    mock_client.models.generate_content.assert_called_once()


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


def test_gemini_engine_raises_without_api_key():
    with pytest.raises(ValueError, match="API key"):
        GeminiEngine(api_key="", model="gemini-2.0-flash")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_engines_gemini.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`src/ask_video/engines/gemini.py`:
```python
from google import genai


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

        contents = [{"role": "user", "parts": [{"text": system_prompt}]}]

        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        contents.append({"role": "user", "parts": [{"text": question}]})

        response = self._client.models.generate_content(
            model=self.model,
            contents=contents,
        )
        return response.text
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_engines_gemini.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/engines/gemini.py tests/test_engines_gemini.py
git commit -m "feat: add GeminiEngine with conversation history support"
```

---

### Task 8: Factory Functions

**Files:**
- Create: `src/ask_video/factory.py`
- Create: `tests/test_factory.py`

**Step 1: Write the failing test**

`tests/test_factory.py`:
```python
from unittest.mock import patch

import pytest

from ask_video.factory import create_source, create_transcriber, create_engine
from ask_video.sources.youtube import YouTubeSource
from ask_video.transcribers.whisper import WhisperTranscriber
from ask_video.engines.gemini import GeminiEngine


def test_create_source_returns_youtube():
    source = create_source("youtube")
    assert isinstance(source, YouTubeSource)


def test_create_source_unknown_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        create_source("vimeo")


def test_create_transcriber_returns_whisper():
    transcriber = create_transcriber("whisper")
    assert isinstance(transcriber, WhisperTranscriber)


def test_create_transcriber_unknown_raises():
    with pytest.raises(ValueError, match="Unknown transcriber"):
        create_transcriber("deepgram")


def test_create_engine_returns_gemini():
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

`src/ask_video/factory.py`:
```python
from ask_video.sources.youtube import YouTubeSource
from ask_video.transcribers.whisper import WhisperTranscriber
from ask_video.engines.gemini import GeminiEngine


def create_source(name: str = "youtube"):
    sources = {
        "youtube": YouTubeSource,
    }
    if name not in sources:
        raise ValueError(f"Unknown source: {name}. Available: {list(sources.keys())}")
    return sources[name]()


def create_transcriber(name: str = "whisper"):
    transcribers = {
        "whisper": WhisperTranscriber,
    }
    if name not in transcribers:
        raise ValueError(f"Unknown transcriber: {name}. Available: {list(transcribers.keys())}")
    return transcribers[name]()


def create_engine(name: str = "gemini", **kwargs):
    engines = {
        "gemini": GeminiEngine,
    }
    if name not in engines:
        raise ValueError(f"Unknown engine: {name}. Available: {list(engines.keys())}")
    return engines[name](**kwargs)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_factory.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/factory.py tests/test_factory.py
git commit -m "feat: add factory functions for source, transcriber, and engine"
```

---

### Task 9: CLI + REPL

**Files:**
- Create: `src/ask_video/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ask_video.cli import app


runner = CliRunner()


@patch("ask_video.cli.os.environ", {"GEMINI_API_KEY": ""})
def test_cli_missing_api_key():
    result = runner.invoke(app, ["https://youtube.com/watch?v=abc"])
    assert result.exit_code != 0
    assert "GEMINI_API_KEY" in result.output


@patch("ask_video.cli.run_session")
@patch("ask_video.cli.create_engine")
@patch("ask_video.cli.create_transcriber")
@patch("ask_video.cli.create_source")
@patch("ask_video.cli.TranscriptStore")
@patch("ask_video.cli.os.environ", {"GEMINI_API_KEY": "test-key"})
def test_cli_loads_cached_transcript(mock_store_cls, mock_source, mock_transcriber, mock_engine, mock_run):
    mock_store = MagicMock()
    mock_store_cls.return_value = mock_store
    mock_transcript = MagicMock()
    mock_transcript.text = "cached text"
    mock_transcript.url = "https://youtube.com/watch?v=abc"
    mock_store.lookup.return_value = mock_transcript

    result = runner.invoke(app, ["https://youtube.com/watch?v=abc"])
    assert result.exit_code == 0
    mock_store.lookup.assert_called_once_with("https://youtube.com/watch?v=abc")
    mock_run.assert_called_once()
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
from ask_video.models import Session
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

            answer = engine.ask(transcript_text, question, session.messages)
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
    url: str = typer.Argument(help="YouTube video URL"),
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

    # Check cache first
    transcript = store.lookup(url)
    if transcript:
        console.print(f"[dim]Loaded cached transcript.[/dim]")
    else:
        console.print(f"[dim]Fetching transcript...[/dim]")
        text = source.fetch_transcript(url)

        if text:
            console.print(f"[dim]Found YouTube captions.[/dim]")
            transcript = store.save(url=url, text=text, source="youtube_captions")
        else:
            console.print(f"[dim]No captions found. Downloading audio for transcription...[/dim]")
            transcriber = create_transcriber(transcriber_name)
            audio_path = source.download_audio(url, store.base_dir / "tmp")
            console.print(f"[dim]Transcribing with {transcriber_name}...[/dim]")
            text = transcriber.transcribe(audio_path)
            transcript = store.save(url=url, text=text, source=transcriber_name)
            # Clean up audio file
            audio_path.unlink(missing_ok=True)

    engine = create_engine("gemini", api_key=api_key, model=model)
    run_session(transcript.text, engine, store, transcript.id)


if __name__ == "__main__":
    app()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add src/ask_video/cli.py tests/test_cli.py
git commit -m "feat: add Typer CLI with interactive REPL session"
```

---

### Task 10: Integration Smoke Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

This test verifies the full pipeline works end-to-end using mocks for external services (no real API calls).

`tests/test_integration.py`:
```python
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.store import TranscriptStore
from ask_video.sources.youtube import YouTubeSource
from ask_video.engines.gemini import GeminiEngine


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

    url = "https://youtube.com/watch?v=test123"
    text = source.fetch_transcript(url)
    assert text is not None

    transcript = store.save(url=url, text=text, source="youtube_captions")
    assert transcript.text == "Welcome to the tutorial\nToday we learn Python"

    engine = GeminiEngine(api_key="test-key")
    answer = engine.ask(transcript.text, "What is this video about?", history=[])
    assert answer == "The video is a Python tutorial."

    # Verify transcript is cached
    cached = store.lookup(url)
    assert cached is not None
    assert cached.id == transcript.id
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
git commit -m "test: add integration smoke test for full pipeline"
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

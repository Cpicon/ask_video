# ask_video — Design Document

**Date:** 2026-02-15
**Status:** Approved

## Purpose

A Python CLI tool that takes a YouTube URL, obtains its transcript (via existing captions or local Whisper transcription), and opens an interactive REPL where users can ask natural language questions about the video content using an LLM.

## Architecture: Layered Pipeline

```
CLI (typer) → VideoSource → Transcriber → TranscriptStore → QAEngine → REPL
```

Each layer is defined as a Python `Protocol` with concrete implementations. A factory function resolves which adapter to use. No DI framework — constructor injection only.

## Project Structure

```
ask_video/
├── pyproject.toml
├── src/
│   └── ask_video/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI entry point, REPL loop
│       ├── protocols.py        # Protocol definitions
│       ├── models.py           # Transcript, Session dataclasses
│       ├── factory.py          # Factory functions to resolve implementations
│       ├── sources/
│       │   ├── __init__.py
│       │   └── youtube.py      # YouTube adapter (yt-dlp, youtube_transcript_api)
│       ├── transcribers/
│       │   ├── __init__.py
│       │   └── whisper.py      # Local Whisper transcription
│       ├── engines/
│       │   ├── __init__.py
│       │   └── gemini.py       # Google Gemini Q&A engine
│       └── store.py            # TranscriptStore: metadata + file management
├── tests/
└── .ask_video/                 # Created at runtime in CWD (not checked in)
```

## Domain Types

To prevent Primitive Obsession (passing raw strings where semantically different identifiers are expected), the application defines strict types using `NewType`. These are zero-cost at runtime but enable `mypy` to catch misuse at type-check time.

```python
from typing import NewType

VideoURL = NewType("VideoURL", str)             # e.g., "https://youtube.com/watch?v=xyz"
VideoID = NewType("VideoID", str)               # Canonical ID from the source (e.g., "xyz")
TranscriptHash = NewType("TranscriptHash", str) # SHA-256 hash of VideoID, used as storage key
```

`TranscriptHash` is deterministically derived from `VideoID` via `generate_transcript_hash()`. This decouples storage from provider-specific ID formats (no special characters in directory names) and eliminates the need for a lookup index file.

## Core Protocols

```python
class VideoSource(Protocol):
    def extract_id(self, url: VideoURL) -> VideoID:
        """Extract a canonical video identifier from a URL (e.g. YouTube video ID)."""
        ...

    def fetch_transcript(self, url: VideoURL) -> str | None:
        """Try to get an existing transcript with timestamps (e.g. YouTube captions).
        Returns timestamped text in [MM:SS] format, or None if unavailable."""
        ...

    def download_audio(self, url: VideoURL, output_dir: Path) -> Path:
        """Download audio from the video URL. Returns path to audio file."""
        ...

class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file to timestamped text in [MM:SS] format."""
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

## Data Model

### Transcript Entity

```python
@dataclass
class Transcript:
    id: TranscriptHash         # Hashed identifier used by the store
    video_id: VideoID          # Canonical ID from the source (e.g. YouTube video ID)
    url: VideoURL              # Source video URL
    text: str                  # Timestamped transcription (e.g. "[0:00] Hello\n[0:05] World")
    created_at: datetime       # When the transcript was created
    source: str                # "youtube_captions" | "whisper"
    path: Path                 # Path to the transcript directory on disk
```

### Session Entity

```python
@dataclass
class Session:
    id: str                    # Short UUID
    transcript_id: TranscriptHash  # Links to Transcript via hashed ID
    started_at: datetime       # Session start timestamp
    messages: list[dict]       # [{"role": "user"|"assistant", "content": "..."}]
```

## Storage Layout

No index file is needed. `TranscriptHash` is deterministically computed from `VideoID`, so the CLI knows exactly which directory to check.

```
.ask_video/
└── transcripts/
    └── <transcript_hash>/
        ├── transcript.txt                    # The transcription text
        ├── info.json                         # video_id, url, created_at, source
        └── sessions/
            └── 2026-02-15_<short_uuid>.json  # Conversation history
```

## Data Flow

1. User runs: `ask_video https://youtube.com/watch?v=xyz`
2. CLI casts input to `VideoURL`
3. `VideoSource.extract_id(url)` extracts canonical `VideoID` (validates URL)
4. CLI computes `TranscriptHash` via `generate_transcript_hash(video_id)`
5. `Store.lookup(transcript_hash)` checks if directory exists
6. If cached: load transcript from disk
7. If not cached:
   a. `VideoSource.fetch_transcript(url)` — try YouTube captions first
   b. If no captions: `VideoSource.download_audio()` + `Transcriber.transcribe()`
   c. `Store.save(transcript_hash, video_id, url, text, source)` — cache to disk
8. Enter REPL loop:
   - User types question
   - `QAEngine.ask(transcript, question, history)` returns answer
   - Display answer, append to session history
   - Repeat until user exits (Ctrl+C or "exit")
9. On exit: save session to `sessions/<date>_<session_id>.json`

## Dependencies

| Package | Purpose |
|---|---|
| `typer` | CLI framework |
| `rich` | REPL formatting and output |
| `yt-dlp` | YouTube audio download |
| `youtube-transcript-api` | Fetch existing YouTube captions |
| `openai-whisper` | Local audio transcription |
| `google-genai` | Gemini LLM API |
| `pytest` | Testing |

## Configuration

- **Secrets via env vars:** `GEMINI_API_KEY`
- **CLI flags:** `--transcriber whisper` (default), `--model gemini-2.0-flash` (default)
- No config file for v1.

## Error Handling

| Scenario | Behavior |
|---|---|
| Invalid/unreachable YouTube URL | Clear error message, exit |
| No captions + Whisper not installed | Error suggesting `pip install 'ask-video[whisper]'` |
| ffmpeg not found on system | Error explaining ffmpeg is required for audio transcription |
| Gemini API key missing | Error with env var instructions |
| Gemini rate limit / API error | Retry once, then show error, stay in REPL |
| Network failure during transcription | Save partial progress, suggest retry |
| Ctrl+C during REPL | Save session history, clean exit |

## Provider Extensibility

Adding a new provider (e.g., OpenAI for Q&A, AssemblyAI for transcription) requires:

1. Create a new module in the appropriate directory (`engines/`, `transcribers/`, `sources/`)
2. Implement the relevant Protocol
3. Register it in `factory.py`

No changes to the core pipeline, CLI, or store logic.

## Testing Strategy

- Unit tests per protocol implementation (mock external APIs)
- Integration test for the full pipeline
- `pytest` as the test framework

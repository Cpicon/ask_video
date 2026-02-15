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

## Core Protocols

```python
class VideoSource(Protocol):
    def fetch_transcript(self, url: str) -> str | None:
        """Try to get an existing transcript (e.g. YouTube captions). Returns None if unavailable."""
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

## Data Model

### Transcript Entity

```python
@dataclass
class Transcript:
    id: str                    # Short UUID
    url: str                   # Source YouTube URL
    text: str                  # The transcription content
    created_at: datetime       # When the transcript was created
    source: str                # "youtube_captions" | "whisper"
    path: Path                 # Path to the transcript directory on disk
```

### Session Entity

```python
@dataclass
class Session:
    id: str                    # Short UUID
    transcript_id: str         # Links to Transcript
    started_at: datetime       # Session start timestamp
    messages: list[dict]       # [{"role": "user"|"assistant", "content": "..."}]
```

## Storage Layout

```
.ask_video/
├── metadata.json                             # URL → transcript_id index
└── transcripts/
    └── <transcript_id>/
        ├── transcript.txt                    # The transcription text
        ├── info.json                         # URL, created_at, source
        └── sessions/
            └── 2026-02-15_<short_uuid>.json  # Conversation history
```

## Data Flow

1. User runs: `ask_video https://youtube.com/watch?v=xyz`
2. TranscriptStore checks `.ask_video/metadata.json` for cached transcript
3. If cached: load transcript from disk
4. If not cached:
   a. `VideoSource.fetch_transcript()` — try YouTube captions first
   b. If no captions: `VideoSource.download_audio()` + `Transcriber.transcribe()`
   c. Save transcript to `.ask_video/transcripts/` and update `metadata.json`
5. Enter REPL loop:
   - User types question
   - `QAEngine.ask(transcript, question, history)` returns answer
   - Display answer, append to session history
   - Repeat until user exits (Ctrl+C or "exit")
6. On exit: save session to `sessions/<date>_<session_id>.json`

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
| No captions + Whisper not installed | Error suggesting install |
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

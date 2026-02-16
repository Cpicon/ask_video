# Technology Stack

## Core
- **Programming Language:** Python 3.12+
- **CLI Framework:** Typer
- **UI/Formatting:** Rich
- **Build System:** Hatchling
- **Package Manager:** uv

## Data Processing
- **Video Source:** yt-dlp, youtube-transcript-api
- **Transcriber:** OpenAI Whisper (Local)
- **LLM/AI Engine:** Google GenAI (Gemini)

## Testing
- **Framework:** Pytest
- **Plugins:** pytest-cov

## Dependencies
- **Core Dependencies:**
    - `typer>=0.9`
    - `rich>=13.0`
    - `yt-dlp>=2024.0`
    - `youtube-transcript-api>=0.6`
    - `google-genai>=1.0`
- **Optional Dependencies:**
    - `whisper`: `openai-whisper>=20230918`
- **Dev Dependencies:**
    - `pytest>=8.0`
    - `pytest-cov>=4.0`

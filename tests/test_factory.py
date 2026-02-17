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

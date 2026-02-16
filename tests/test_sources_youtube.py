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
def test_fetch_transcript_returns_timestamped_captions(mock_api_cls, source):
    # Mock the instance-based API: YouTubeTranscriptApi() -> api.list() -> transcript.fetch()
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    mock_transcript = MagicMock()
    mock_api.list.return_value.find_manually_created_transcript.return_value = mock_transcript
    mock_transcript.fetch.return_value = [
        {"text": "Hello", "start": 0.0, "duration": 1.0},
        {"text": "world", "start": 65.0, "duration": 1.0},
    ]

    result = source.fetch_transcript("https://youtube.com/watch?v=abc123def78")
    assert result == "[0:00] Hello\n[1:05] world"
    mock_api.list.assert_called_once_with("abc123def78")


@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_fetch_transcript_returns_none_when_no_captions(mock_api_cls, source):
    mock_api = MagicMock()
    mock_api_cls.return_value = mock_api
    mock_api.list.side_effect = Exception("No transcript available")

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

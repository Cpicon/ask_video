import os
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ask_video.cli import app
from ask_video.models import VideoID, generate_transcript_hash


runner = CliRunner()


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

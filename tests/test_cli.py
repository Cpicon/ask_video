import os
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner

from ask_video.cli import app, run_session
from ask_video.models import VideoID, generate_transcript_hash


runner = CliRunner()


def _run_session_with_capture(markdown_response, questions=None):
    """Helper: run run_session with a captured Rich console and mock engine.

    Returns the rendered output as a plain string (no ANSI codes).
    Uses prompt_session=None so get_user_input() falls back to builtins.input().
    """
    if questions is None:
        questions = ["test question", "exit"]

    output = StringIO()
    test_console = Console(file=output, force_terminal=False, width=80)

    mock_engine = MagicMock()
    mock_engine.ask.return_value = markdown_response
    mock_store = MagicMock()

    with patch("ask_video.cli.console", test_console), \
         patch("ask_video.ui.prompt.input", side_effect=questions):
        run_session("transcript text", mock_engine, mock_store, "test-id")

    return output.getvalue()


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


def test_run_session_renders_markdown():
    """AI markdown responses should be rendered, not displayed as raw syntax."""
    rendered = _run_session_with_capture(
        "## Summary\n**Key points:**\n- First\n- Second"
    )
    # Raw markdown delimiters must not appear in rendered output
    assert "**Key points:**" not in rendered, f"Raw bold markdown found: {rendered}"
    assert "## Summary" not in rendered, f"Raw header markdown found: {rendered}"
    # Content text must still be present
    assert "Summary" in rendered
    assert "Key points" in rendered
    assert "First" in rendered
    assert "Second" in rendered
    assert "Assistant:" in rendered


def test_run_session_renders_markdown_with_brackets():
    """Square brackets in LLM output must not be interpreted as Rich markup."""
    rendered = _run_session_with_capture(
        "See [1] and [important note] for details."
    )
    assert "[1]" in rendered, f"Bracket reference lost in output: {rendered}"
    assert "[important note]" in rendered, f"Bracket text lost in output: {rendered}"


def test_run_session_renders_code_blocks():
    """Fenced code blocks should render without raw backtick delimiters."""
    rendered = _run_session_with_capture(
        "Here is code:\n```python\nprint('hello')\n```"
    )
    assert "print" in rendered
    assert "hello" in rendered
    assert "```" not in rendered, f"Raw code fence found in output: {rendered}"


def test_run_session_handles_empty_response():
    """Empty engine response should not crash; Assistant label still appears."""
    rendered = _run_session_with_capture("")
    assert "Assistant:" in rendered


def test_run_session_skips_empty_lines():
    """Empty input lines should be skipped, not treated as exit signal."""
    rendered = _run_session_with_capture(
        "The answer is 42.",
        questions=["first question", "", "", "second question", "exit"],
    )
    # Both questions should have been answered (empty lines skipped)
    assert rendered.count("Assistant:") == 2, (
        f"Expected 2 assistant responses (empty lines skipped), got: {rendered}"
    )

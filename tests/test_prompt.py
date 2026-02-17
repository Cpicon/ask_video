import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from ask_video.ui.prompt import create_prompt_session, get_user_input


def test_create_prompt_session_returns_session():
    session = create_prompt_session()
    assert isinstance(session, PromptSession)


def test_create_prompt_session_multiline_enabled():
    session = create_prompt_session()
    assert session.default_buffer.multiline() is True


def test_create_prompt_session_with_history(tmp_path):
    history_path = tmp_path / "test_history"
    session = create_prompt_session(history_path=history_path)
    assert isinstance(session.history, FileHistory)


def test_create_prompt_session_without_history():
    session = create_prompt_session()
    assert not isinstance(session.history, FileHistory)


def test_get_user_input_fallback_when_no_session():
    with patch("ask_video.ui.prompt.input", return_value="  hello  "):
        result = get_user_input(session=None)
    assert result == "hello"


def test_get_user_input_fallback_when_no_tty():
    mock_session = MagicMock(spec=PromptSession)
    with patch("ask_video.ui.prompt.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = False
        with patch("ask_video.ui.prompt.input", return_value="piped input"):
            result = get_user_input(session=mock_session)
    assert result == "piped input"
    mock_session.prompt.assert_not_called()


def test_get_user_input_uses_session_when_tty():
    mock_session = MagicMock(spec=PromptSession)
    mock_session.prompt.return_value = "  session input  "
    with patch("ask_video.ui.prompt.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        result = get_user_input(session=mock_session)
    assert result == "session input"
    mock_session.prompt.assert_called_once_with("You: ")


def test_get_user_input_strips_whitespace():
    with patch("ask_video.ui.prompt.input", return_value="  spaced  "):
        result = get_user_input(session=None)
    assert result == "spaced"

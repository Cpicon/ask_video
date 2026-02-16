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

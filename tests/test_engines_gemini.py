import os
from unittest.mock import patch, MagicMock, call

import pytest

from ask_video.engines.gemini import GeminiEngine


def _make_stream_chunks(*texts):
    """Helper: create mock streaming chunks from text strings."""
    chunks = []
    for t in texts:
        chunk = MagicMock()
        chunk.text = t
        chunks.append(chunk)
    return chunks


@patch("ask_video.engines.gemini.genai")
def test_ask_streams_and_returns_full_response(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content_stream.return_value = _make_stream_chunks(
        "The video ", "discusses ", "Python programming."
    )

    engine = GeminiEngine(api_key="test-key", model="gemini-3-pro-preview")
    result = engine.ask(
        transcript="Welcome to the Python tutorial...",
        question="What is this video about?",
        history=[],
    )

    assert result == "The video discusses Python programming."

    # Verify streaming was used, not non-streaming
    mock_client.models.generate_content_stream.assert_called_once()
    mock_client.models.generate_content.assert_not_called()

    # Verify system_instruction and thinking_config are in config
    call_kwargs = mock_client.models.generate_content_stream.call_args
    contents = call_kwargs.kwargs["contents"]
    assert len(contents) == 1
    assert contents[0]["role"] == "user"
    config = call_kwargs.kwargs["config"]
    assert config.system_instruction is not None
    assert config.thinking_config is not None
    assert config.thinking_config.thinking_budget == 24576


@patch("ask_video.engines.gemini.genai")
def test_ask_includes_conversation_history(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content_stream.return_value = _make_stream_chunks(
        "As I mentioned, it covers decorators."
    )

    engine = GeminiEngine(api_key="test-key", model="gemini-3-pro-preview")
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
    call_kwargs = mock_client.models.generate_content_stream.call_args
    contents = call_kwargs.kwargs["contents"]
    roles = [c["role"] for c in contents]
    assert roles == ["user", "model", "user"]


@patch("ask_video.engines.gemini.genai")
def test_gemini_engine_falls_back_to_vertex_without_api_key(mock_genai):
    """When no API key is provided, GeminiEngine uses Vertex AI via ADC."""
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client

    engine = GeminiEngine(api_key=None, project="my-project", location="us-central1")
    mock_genai.Client.assert_called_once_with(
        vertexai=True, project="my-project", location="us-central1"
    )


@patch("ask_video.engines.gemini.genai")
def test_gemini_engine_uses_api_key_when_provided(mock_genai):
    """When API key is provided, GeminiEngine uses AI Studio."""
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client

    engine = GeminiEngine(api_key="test-key")
    mock_genai.Client.assert_called_once_with(api_key="test-key", vertexai=False)

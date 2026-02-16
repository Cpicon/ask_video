from unittest.mock import MagicMock, patch
import pytest
from ask_video.cli import app
from ask_video.engines.gemini import GeminiEngine
from ask_video.models import VideoURL, VideoID, generate_transcript_hash
from ask_video.sources.youtube import YouTubeSource
from ask_video.store import TranscriptStore
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def mock_youtube_api():
    with patch("ask_video.sources.youtube.YouTubeTranscriptApi") as mock:
        yield mock


@pytest.fixture
def mock_genai():
    with patch("ask_video.engines.gemini.genai") as mock:
        mock_client = MagicMock()
        mock.Client.return_value = mock_client
        yield mock


@pytest.fixture
def store(tmp_path):
    return TranscriptStore(base_dir=tmp_path / ".ask_video")


@pytest.fixture
def mock_env_setup(mock_youtube_api, mock_genai, store):
    """
    Sets up the environment for the integration test.
    Mocks external APIs and injects the temporary store.
    """
    with patch("ask_video.cli.TranscriptStore", return_value=store):
        yield

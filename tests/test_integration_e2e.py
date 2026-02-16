import os
import pytest
from ask_video.store import TranscriptStore
from typer.testing import CliRunner

runner = CliRunner()

@pytest.fixture
def store(tmp_path):
    """
    Creates a TranscriptStore backed by a temporary directory.
    This ensures the live test doesn't pollute the user's real cache.
    """
    return TranscriptStore(base_dir=tmp_path / ".ask_video")

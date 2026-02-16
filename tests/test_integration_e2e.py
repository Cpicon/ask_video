import os
import pytest
from unittest.mock import patch
from ask_video.cli import app
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

def test_e2e_live_flow(store):
    """
    Live integration test hitting real YouTube and Gemini APIs (Vertex AI or AI Studio).
    """
    # We patch the TranscriptStore class in the CLI module to return our
    # temporary store instance. This is the ONLY mock/patch we use.
    # Everything else (YouTubeSource, GeminiEngine) is real.
    with patch("ask_video.cli.TranscriptStore", return_value=store):
        
        # "Python in 100 Seconds" - has captions
        video_url = "https://www.youtube.com/watch?v=x7X9w_GIm1s"
        
        # Simulate user input: Question + Exit
        user_input = "Summarize this video in one sentence.\nexit\n"
        
        # Unset GEMINI_API_KEY to force Vertex AI usage (via ADC)
        # We must set it to empty string because CliRunner updates env, doesn't replace it
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = ""
        
        # Use gemini-3-pro-preview as requested
        result = runner.invoke(app, [video_url, "--model", "gemini-3-pro-preview"], input=user_input, env=env)
        
        print(f"Full Output:\n{result.output}")
        
        # Debugging output if test fails
        if result.exit_code != 0:
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        
        # Verify Transcript Fetching (from YouTube)
        assert "Fetching transcript..." in result.output or "Found YouTube captions" in result.output
        
        # Verify Gemini Interaction
        # We look for the standard assistant prompt prefix
        assert "Assistant:" in result.output
        
        # Verify Cache Creation
        transcripts_dir = store.base_dir / "transcripts"
        assert transcripts_dir.exists()
        assert any(transcripts_dir.iterdir()), "No transcript directory created in cache"

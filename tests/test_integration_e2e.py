from unittest.mock import MagicMock, patch
import pytest
from ask_video.cli import app
from ask_video.engines.gemini import GeminiEngine
from ask_video.models import VideoURL, VideoID, generate_transcript_hash
from ask_video.sources.youtube import YouTubeSource
from ask_video.store import TranscriptStore
from typer.testing import CliRunner

runner = CliRunner()

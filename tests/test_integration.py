from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.store import TranscriptStore
from ask_video.sources.youtube import YouTubeSource
from ask_video.engines.gemini import GeminiEngine
from ask_video.models import VideoURL, generate_transcript_hash


@patch("ask_video.engines.gemini.genai")
@patch("ask_video.sources.youtube.YouTubeTranscriptApi")
def test_full_pipeline_with_captions(mock_yt_api_cls, mock_genai, tmp_path):
    # 1. YouTube captions exist (instance-based API)
    mock_api = MagicMock()
    mock_yt_api_cls.return_value = mock_api
    mock_transcript = MagicMock()
    mock_api.list.return_value.find_manually_created_transcript.return_value = mock_transcript
    mock_transcript.fetch.return_value = [
        {"text": "Welcome to the tutorial", "start": 0.0, "duration": 2.0},
        {"text": "Today we learn Python", "start": 2.0, "duration": 2.0},
    ]

    # 2. Gemini returns a streamed answer
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_chunk = MagicMock()
    mock_chunk.text = "The video is a Python tutorial."
    mock_client.models.generate_content_stream.return_value = [mock_chunk]

    # Pipeline
    source = YouTubeSource()
    store = TranscriptStore(base_dir=tmp_path / ".ask_video")

    url = VideoURL("https://youtube.com/watch?v=tEst123tEst")
    video_id = source.extract_id(url)
    assert video_id == "tEst123tEst"

    transcript_hash = generate_transcript_hash(video_id)

    text = source.fetch_transcript(url)
    assert text is not None

    transcript = store.save(
        transcript_hash=transcript_hash,
        video_id=video_id,
        url=url,
        text=text,
        source="youtube_captions",
    )
    assert transcript.id == transcript_hash
    assert transcript.video_id == "tEst123tEst"
    assert transcript.text == "[0:00] Welcome to the tutorial\n[0:02] Today we learn Python"

    engine = GeminiEngine(api_key="test-key")
    answer = engine.ask(transcript.text, "What is this video about?", history=[])
    assert answer == "The video is a Python tutorial."

    # Verify transcript is cached by hash
    cached = store.lookup(transcript_hash)
    assert cached is not None
    assert cached.id == transcript.id

    # Verify that a different URL for the same video produces the same hash
    alt_url = VideoURL("https://youtu.be/tEst123tEst")
    alt_video_id = source.extract_id(alt_url)
    alt_hash = generate_transcript_hash(alt_video_id)
    assert alt_hash == transcript_hash  # Same video -> same hash
    cached_again = store.lookup(alt_hash)
    assert cached_again is not None
    assert cached_again.id == transcript.id

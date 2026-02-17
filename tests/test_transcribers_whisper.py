import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ask_video.transcribers.whisper import WhisperTranscriber


def test_transcribe_returns_timestamped_text(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    mock_whisper = MagicMock()
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {
        "text": "Hello world",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": " Hello"},
            {"start": 65.0, "end": 67.0, "text": " world"},
        ],
    }

    with patch.dict("sys.modules", {"whisper": mock_whisper}):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            transcriber = WhisperTranscriber(model_name="base")
            result = transcriber.transcribe(audio_file)

    assert result == "[0:00] Hello\n[1:05] world"
    mock_whisper.load_model.assert_called_once_with("base")


def test_transcribe_default_model():
    transcriber = WhisperTranscriber()
    assert transcriber.model_name == "base"


def test_transcribe_raises_when_whisper_not_installed(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    with patch.dict("sys.modules", {"whisper": None}):
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            transcriber = WhisperTranscriber()
            with pytest.raises(RuntimeError, match="pip install"):
                transcriber.transcribe(audio_file)


def test_transcribe_raises_when_ffmpeg_missing(tmp_path):
    audio_file = tmp_path / "audio.m4a"
    audio_file.write_bytes(b"fake audio data")

    with patch("shutil.which", return_value=None):
        transcriber = WhisperTranscriber()
        with pytest.raises(RuntimeError, match="ffmpeg"):
            transcriber.transcribe(audio_file)

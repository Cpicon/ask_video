import shutil
from pathlib import Path


def _format_ts(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class WhisperTranscriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import whisper
            except ImportError:
                raise RuntimeError(
                    "Whisper is not installed. Install with: pip install 'ask-video[whisper]'"
                )
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg is required for audio transcription but was not found. "
                "Install it: https://ffmpeg.org/download.html"
            )
        model = self._get_model()
        result = model.transcribe(str(audio_path))
        return "\n".join(
            f"[{_format_ts(seg['start'])}]{seg['text']}"
            for seg in result["segments"]
        )

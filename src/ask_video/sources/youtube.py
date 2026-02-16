import re
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from ask_video.models import VideoURL, VideoID


def _format_ts(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class YouTubeSource:
    _VIDEO_ID_PATTERN = re.compile(
        r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/)([a-zA-Z0-9_-]{11})"
    )

    def extract_id(self, url: VideoURL) -> VideoID:
        match = self._VIDEO_ID_PATTERN.search(url)
        if match:
            return VideoID(match.group(1))
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def fetch_transcript(self, url: VideoURL) -> str | None:
        video_id = self.extract_id(url)
        try:
            entries = YouTubeTranscriptApi.get_transcript(video_id)
            return "\n".join(
                f"[{_format_ts(entry['start'])}] {entry['text']}"
                for entry in entries
            )
        except Exception:
            return None

    def download_audio(self, url: VideoURL, output_dir: Path) -> Path:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return Path(filename)

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
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            # Try to get manual English, then generated English, then any English
            try:
                transcript = transcript_list.find_manually_created_transcript(["en"])
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(["en"])
                except Exception:
                    # Fallback to whatever is available (e.g. translated) or just the first one
                    transcript = next(iter(transcript_list))
            
            entries = transcript.fetch()
            # Inspect first entry type for debugging
            if entries:
                first = entries[0]
                # If it's a dict
                if isinstance(first, dict):
                    return "\n".join(
                        f"[{_format_ts(entry['start'])}] {entry['text']}"
                        for entry in entries
                    )
                # If it's an object
                else:
                    return "\n".join(
                        f"[{_format_ts(entry.start)}] {entry.text}"
                        for entry in entries
                    )
            return ""
        except Exception as e:
            print(f"DEBUG: fetch_transcript failed: {e} Type: {type(e)}")
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

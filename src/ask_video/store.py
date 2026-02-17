import json
from datetime import datetime, timezone
from pathlib import Path

from ask_video.models import (
    Transcript, Session, VideoURL, VideoID, TranscriptHash,
)


class TranscriptStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(".ask_video")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def lookup(self, transcript_hash: TranscriptHash) -> Transcript | None:
        transcript_dir = self.base_dir / "transcripts" / transcript_hash
        if not transcript_dir.exists():
            return None
        text = (transcript_dir / "transcript.txt").read_text()
        info = json.loads((transcript_dir / "info.json").read_text())
        return Transcript(
            id=transcript_hash,
            video_id=VideoID(info["video_id"]),
            url=VideoURL(info["url"]),
            text=text,
            created_at=datetime.fromisoformat(info["created_at"]),
            source=info["source"],
            path=transcript_dir,
        )

    def save(
        self,
        transcript_hash: TranscriptHash,
        video_id: VideoID,
        url: VideoURL,
        text: str,
        source: str,
    ) -> Transcript:
        transcript_dir = self.base_dir / "transcripts" / transcript_hash
        transcript_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)

        (transcript_dir / "transcript.txt").write_text(text)
        (transcript_dir / "info.json").write_text(
            json.dumps({
                "video_id": video_id,
                "url": url,
                "created_at": now.isoformat(),
                "source": source,
            }, indent=2)
        )

        return Transcript(
            id=transcript_hash,
            video_id=video_id,
            url=url,
            text=text,
            created_at=now,
            source=source,
            path=transcript_dir,
        )

    def save_session(self, session: Session) -> Path:
        transcript_dir = self.base_dir / "transcripts" / session.transcript_id
        sessions_dir = transcript_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        date_str = session.started_at.strftime("%Y-%m-%d")
        filename = f"{date_str}_{session.id}.json"
        path = sessions_dir / filename
        path.write_text(
            json.dumps({
                "id": session.id,
                "transcript_id": session.transcript_id,
                "started_at": session.started_at.isoformat(),
                "messages": session.messages,
            }, indent=2)
        )
        return path

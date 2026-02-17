def create_source(name: str = "youtube"):
    if name == "youtube":
        from ask_video.sources.youtube import YouTubeSource
        return YouTubeSource()
    raise ValueError(f"Unknown source: {name}. Available: ['youtube']")


def create_transcriber(name: str = "whisper"):
    if name == "whisper":
        from ask_video.transcribers.whisper import WhisperTranscriber
        return WhisperTranscriber()
    raise ValueError(f"Unknown transcriber: {name}. Available: ['whisper']")


def create_engine(name: str = "gemini", **kwargs):
    if name == "gemini":
        from ask_video.engines.gemini import GeminiEngine
        return GeminiEngine(**kwargs)
    raise ValueError(f"Unknown engine: {name}. Available: ['gemini']")

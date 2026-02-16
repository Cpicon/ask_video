import os
import uuid
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.panel import Panel

from ask_video.factory import create_source, create_transcriber, create_engine
from ask_video.models import VideoURL, Session, generate_transcript_hash
from ask_video.store import TranscriptStore

app = typer.Typer(help="Ask questions about YouTube videos using AI.")
console = Console()


def run_session(transcript_text: str, engine, store: TranscriptStore, transcript_id: str):
    session = Session(
        id=uuid.uuid4().hex[:8],
        transcript_id=transcript_id,
        started_at=datetime.now(timezone.utc),
        messages=[],
    )

    console.print(Panel("Ready! Ask questions about the video. Type 'exit' or Ctrl+C to quit.", style="green"))

    try:
        while True:
            question = console.input("[bold cyan]You:[/bold cyan] ").strip()
            if not question or question.lower() in ("exit", "quit"):
                break

            try:
                answer = engine.ask(transcript_text, question, session.messages)
            except Exception as e:
                console.print(f"[bold red]API Error:[/bold red] {e}")
                console.print("[dim]Retrying...[/dim]")
                try:
                    answer = engine.ask(transcript_text, question, session.messages)
                except Exception as retry_err:
                    console.print(f"[bold red]Retry failed:[/bold red] {retry_err}")
                    console.print("[dim]Please try again.[/dim]")
                    continue

            session.messages.append({"role": "user", "content": question})
            session.messages.append({"role": "assistant", "content": answer})

            console.print(f"\n[bold green]Assistant:[/bold green] {answer}\n")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Exiting...[/dim]")
    finally:
        if session.messages:
            store.save_session(session)
            console.print(f"[dim]Session saved ({len(session.messages) // 2} exchanges).[/dim]")


@app.command()
def main(
    url_input: str = typer.Argument(help="YouTube video URL"),
    transcriber_name: str = typer.Option("whisper", "--transcriber", "-t", help="Transcriber to use"),
    model: str = typer.Option("gemini-3-pro-preview", "--model", "-m", help="LLM model name"),
):
    """Load a YouTube video and ask questions about it."""
    api_key = os.environ.get("GEMINI_API_KEY")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")

    store = TranscriptStore()
    source = create_source("youtube")

    # 1. Cast input string to domain type
    url = VideoURL(url_input)

    # 2. Extract canonical video ID (validates URL)
    try:
        video_id = source.extract_id(url)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    # 3. Compute deterministic hash for storage lookup
    transcript_hash = generate_transcript_hash(video_id)

    # 4. Check cache using the hash
    transcript = store.lookup(transcript_hash)
    if transcript:
        console.print("[dim]Loaded cached transcript.[/dim]")
    else:
        console.print("[dim]Fetching transcript...[/dim]")
        text = source.fetch_transcript(url)

        if text:
            console.print("[dim]Found YouTube captions.[/dim]")
            transcript = store.save(
                transcript_hash=transcript_hash,
                video_id=video_id,
                url=url,
                text=text,
                source="youtube_captions",
            )
        else:
            console.print("[dim]No captions found. Downloading audio for transcription...[/dim]")
            transcriber = create_transcriber(transcriber_name)
            audio_path = source.download_audio(url, store.base_dir / "tmp")
            try:
                console.print(f"[dim]Transcribing with {transcriber_name}...[/dim]")
                text = transcriber.transcribe(audio_path)
                transcript = store.save(
                    transcript_hash=transcript_hash,
                    video_id=video_id,
                    url=url,
                    text=text,
                    source=transcriber_name,
                )
            finally:
                audio_path.unlink(missing_ok=True)

    engine = create_engine(
        "gemini", 
        api_key=api_key, 
        model=model, 
        project=project, 
        location=location
    )
    run_session(transcript.text, engine, store, transcript.id)


if __name__ == "__main__":
    app()

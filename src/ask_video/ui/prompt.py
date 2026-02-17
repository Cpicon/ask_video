import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML


def _bottom_toolbar():
    return HTML(
        "<b>Enter</b>: New Line  |  <b>Esc→Enter</b>: Submit  |  <b>Ctrl+D</b>: Exit"
    )


def create_prompt_session(history_path: Path | None = None) -> PromptSession:
    """Create a configured PromptSession for the chat REPL.

    The session uses multiline mode (Enter inserts newline, Esc→Enter submits)
    and optionally persists history to disk.
    """
    history = FileHistory(str(history_path)) if history_path else None
    return PromptSession(
        multiline=True,
        history=history,
        bottom_toolbar=_bottom_toolbar,
    )


def get_user_input(session: PromptSession | None = None) -> str:
    """Get input from the user, with fallback for non-interactive terminals.

    When a PromptSession is provided and stdin is a TTY, uses prompt_toolkit
    for multiline editing. Otherwise falls back to plain input().
    """
    if session is None or not sys.stdin.isatty():
        return input("You: ").strip()

    return session.prompt("You: ").strip()

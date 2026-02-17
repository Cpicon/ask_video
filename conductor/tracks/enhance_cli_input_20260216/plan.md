# Implementation Plan - Enhance CLI Input with Multi-line Support

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rich + prompt_toolkit terminal conflict | Output corruption, garbled display | Sequential handoff: prompt_toolkit for input only, Rich for output only. Never active simultaneously. |
| Existing test suite breaks (`test_cli.py:27` mocks `console.input`) | All 5 `_run_session_with_capture` tests fail | Refactor `run_session()` to accept an input callable; tests inject mock without patching console.input. |
| Non-interactive stdin (piped, CI) crashes prompt_toolkit | CI failures, scripting impossible | TTY detection with `sys.stdin.isatty()`; fallback to plain `input()`. |
| Option+Enter (Meta+Enter) not available without terminal config on macOS | Users cannot submit without Esc→Enter | Document `Esc→Enter` as the primary submit method; Option+Enter as optional shortcut requiring terminal setup. |

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add `prompt-toolkit>=3.0.43` dependency |
| `src/ask_video/ui/__init__.py` | Create empty package init |
| `src/ask_video/ui/prompt.py` | New module: `create_prompt_session()` factory + `get_user_input()` function |
| `src/ask_video/cli.py` | Replace `console.input()` at line 30 with `get_user_input()` call; add `prompt_session` parameter to `run_session()` |
| `tests/test_cli.py` | Update `_run_session_with_capture` to inject mock input callable instead of patching `console.input` |

---

## Phase 1: Dependency & Prototype
- [ ] Task: Add `prompt-toolkit>=3.0.43` to `pyproject.toml` dependencies.
- [ ] Task: Install with `uv sync`.
- [ ] Task: Create `scripts/prompt_prototype.py` — standalone script to validate:
    - [ ] `PromptSession` with `multiline=True` (Enter adds newline, Esc→Enter submits).
    - [ ] Bottom toolbar displaying `Enter: New Line | Esc→Enter: Submit | Ctrl+D: Exit`.
    - [ ] History recall with Up/Down arrows.
    - [ ] `Ctrl+C` clears current input without crashing.
    - [ ] `Ctrl+D` on empty prompt raises `EOFError`.
    - [ ] Pasting multi-line text via clipboard.
- [ ] Task: Document terminal compatibility findings (macOS Terminal, iTerm2, VS Code integrated terminal).
- [ ] Task: Conductor - User Manual Verification 'Dependency & Prototype' (Protocol in workflow.md)

## Phase 2: Module Creation (TDD)
- [ ] Task: Create `src/ask_video/ui/__init__.py` (empty).
- [ ] Task: Create `src/ask_video/ui/prompt.py` with:
    - [ ] `create_prompt_session(history_path: Path | None = None) -> PromptSession` factory function.
        - Creates `PromptSession` with `multiline=True`.
        - Configures `FileHistory` at `history_path` if provided.
        - Sets bottom toolbar text.
        - Returns the session object (no class wrapper, matches codebase factory pattern).
    - [ ] `get_user_input(session: PromptSession | None = None) -> str` function.
        - If `session` is `None` or `not sys.stdin.isatty()`, falls back to `input("You: ")`.
        - Otherwise calls `session.prompt("You: ")` and returns stripped result.
        - Raises `EOFError` on Ctrl+D, `KeyboardInterrupt` on Ctrl+C (natural prompt_toolkit behavior).
- [ ] Task: Write tests for `src/ask_video/ui/prompt.py`:
    - [ ] Test `create_prompt_session()` returns a `PromptSession` with `multiline=True`.
    - [ ] Test `create_prompt_session(history_path=...)` configures `FileHistory`.
    - [ ] Test `get_user_input(session=None)` falls back to `input()`.
    - [ ] Test `get_user_input(session=mock)` calls `session.prompt()` and strips result.
    - [ ] Test `get_user_input()` when `stdin.isatty()` returns `False` uses fallback.
- [ ] Task: Conductor - User Manual Verification 'Module Creation (TDD)' (Protocol in workflow.md)

## Phase 3: CLI Integration
- [ ] Task: Update `run_session()` signature in `cli.py`:
    - Add parameter: `prompt_session: PromptSession | None = None`.
    - Replace `console.input("[bold cyan]You:[/bold cyan] ").strip()` (line 30) with `get_user_input(prompt_session)`.
    - Keep all existing exception handling (`KeyboardInterrupt`, `EOFError`) at lines 54-55.
- [ ] Task: Update `main()` in `cli.py`:
    - Create session via `create_prompt_session(history_path=store.base_dir / "prompt_history")`.
    - Pass it to `run_session()`.
- [ ] Task: Verify Rich output rendering is unaffected:
    - Markdown responses still render correctly (not raw syntax).
    - Panels, styled text, and dim text all display properly.
    - No terminal corruption between input and output phases.
- [ ] Task: Conductor - User Manual Verification 'CLI Integration' (Protocol in workflow.md)

## Phase 4: Test Refactoring
- [ ] Task: Update `_run_session_with_capture` helper in `tests/test_cli.py`:
    - Stop mocking `console.input` (line 27).
    - Instead, create a mock `PromptSession` (or mock callable) and pass via `prompt_session` parameter.
    - OR: pass `prompt_session=None` and mock `builtins.input` for the fallback path.
- [ ] Task: Run full test suite — verify all existing tests pass:
    - `test_run_session_renders_markdown`
    - `test_run_session_renders_markdown_with_brackets`
    - `test_run_session_renders_code_blocks`
    - `test_run_session_handles_empty_response`
    - `test_run_session_skips_empty_lines`
    - `test_cli_loads_cached_transcript`
    - `test_cli_invalid_url_shows_clean_error`
- [ ] Task: Add new tests:
    - Test `run_session()` with a real `PromptSession` mock (prompt_toolkit path).
    - Test `run_session()` with `prompt_session=None` (fallback path).
    - Test that `Ctrl+D` (`EOFError`) triggers graceful exit with session save.
- [ ] Task: Conductor - User Manual Verification 'Test Refactoring' (Protocol in workflow.md)

## Phase 5: Polish & Verification
- [ ] Task: Style the prompt prefix to match existing CLI theme (`bold cyan` for "You:").
    - Use prompt_toolkit's `style` or ANSI formatting for the prompt string.
- [ ] Task: Verify edge cases:
    - Empty input → skipped (not treated as exit).
    - Very long pasted text → no truncation or crash.
    - Special characters (unicode, emoji) → handled correctly.
    - `exit` and `quit` commands → session ends normally.
- [ ] Task: Manual end-to-end verification:
    - Run `ask_video <url>`.
    - Type a single-line question → Enter → response renders as Markdown.
    - Type a multi-line question using Enter for newlines → Esc→Enter to submit → response renders correctly.
    - Press Up arrow → previous question recalled.
    - Press Ctrl+C during input → input cleared, prompt redisplayed.
    - Press Ctrl+D on empty prompt → session exits, saved.
    - Pipe input: `echo "What is the video about?" | ask_video <url>` → no crash.
- [ ] Task: Conductor - User Manual Verification 'Polish & Verification' (Protocol in workflow.md)

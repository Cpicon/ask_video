# Implementation Plan - Fix Markdown Rendering in CLI Chat Output

## Agent Analysis Summary

**Root cause:** `cli.py:48` interpolates the raw `answer` string into a Rich markup f-string:

```python
console.print(f"\n[bold green]Assistant:[/bold green] {answer}\n")
```

Rich interprets its own `[tag]` markup but does **not** parse Markdown. The LLM's markdown output (`**bold**`, `## Header`, `- list`) is printed verbatim.

**Architecture context:**

- `QAEngine.ask()` returns `str` (protocol at `protocols.py:30`). The engine streams internally but joins chunks before return (`engines/gemini.py:54`).
- No post-processing exists between engine output and display.
- `Console()` is a module-level singleton at `cli.py:14`. Only `Console` and `Panel` are imported from Rich.
- `rich.markdown.Markdown` is not imported or used anywhere in the project.
- Test coverage for `run_session` display output is **zero** — all CLI tests patch `run_session` out entirely.

---

## Phase 1: Exploration and Reproduction

- [x] Task: Create a reproduction script or manual test case.
  - [x] Task: Identify the code responsible for printing the AI response in `ask_video/cli.py` (likely in `run_session` or similar).
    - **Finding:** `cli.py:48` — `console.print(f"\n[bold green]Assistant:[/bold green] {answer}\n")` inside `run_session()` (lines 17-54).
  - [x] Task: Create a test case in `tests/test_cli.py` that mocks a markdown response from Gemini (e.g., `**Bold**`).
    - Mock `engine.ask()` to return a markdown string (e.g., `"## Summary\n**Key points:**\n- First\n- Second"`).
    - Use `typer.testing.CliRunner` to capture output (existing pattern in `test_cli.py`).
    - Unlike existing CLI tests (which patch out `run_session`), this test must exercise `run_session` to verify display behavior.
    - Use `@patch("ask_video.cli.console")` to inject a `Console(file=StringIO(), force_terminal=True)` for deterministic output capture.
  - [x] Task: Verify that the current output contains raw markdown characters (e.g., `**`).
    - Assert the captured output includes literal `**` and `##` characters (proving markdown is not rendered).
- [x] Task: Conductor - User Manual Verification 'Exploration and Reproduction' (Protocol in workflow.md)

## Phase 2: Implementation (TDD)

- [x] Task: Update the printing logic to use `rich.markdown.Markdown`.
  - [x] Task: Import `Markdown` from `rich.markdown`.
    - Add `from rich.markdown import Markdown` to imports at `cli.py:7` (alongside existing `from rich.panel import Panel`).
  - [x] Task: Modify the output function to wrap the AI response text in `Markdown(text)`.
    - **Current code** (`cli.py:48`):
      ```python
      console.print(f"\n[bold green]Assistant:[/bold green] {answer}\n")
      ```
    - **New code** — split into label + rendered body:
      ```python
      console.print("\n[bold green]Assistant:[/bold green]")
      console.print(Markdown(answer))
      console.print()
      ```
    - **Rationale:** `Markdown()` is a Rich renderable that `console.print()` renders as formatted terminal output. It cannot be mixed inside an f-string with Rich markup — it must be printed as a standalone object.
  - [x] Task: Ensure that `console.print` handles the `Markdown` object correctly.
    - `Console.print()` natively accepts any Rich `RenderableType`, including `Markdown`. No special configuration needed.
  - [x] Task: Handle Rich markup injection from LLM output.
    - **Risk:** Without `Markdown()`, if the LLM returns text with square brackets (e.g., `[important]`, `[1]`, `[citation needed]`), Rich's `console.print()` could misinterpret them as markup tags, causing `MarkupError` or mangled output.
    - **Mitigation:** `Markdown()` renders its own content internally and does not pass through Rich's markup parser, so this is inherently safe. Verify with a test containing square brackets.
  - [x] Task: Handle malformed or empty markdown gracefully.
    - Test that `Markdown("")` (empty string) renders without error.
    - Test that `Markdown("unclosed **bold")` (malformed markdown) renders without crashing.
    - The `rich.markdown.Markdown` parser is lenient by design — it degrades to plain text for unrecognized syntax.
- [x] Task: Run the reproduction test case again.
  - [x] Task: Verify that the output no longer contains raw markdown syntax (e.g., `**` should be gone, replaced by formatting codes or just the text).
  - [x] Task: Verify that headers render as distinct styled lines (not raw `##` characters).
  - [x] Task: Verify that lists render as formatted lists (not raw `- ` or `1. ` prefixes).
  - [x] Task: Verify that code blocks render with syntax highlighting (or at minimum as distinct blocks).
- [x] Task: Conductor - User Manual Verification 'Implementation (TDD)' (Protocol in workflow.md)

## Phase 3: Test Coverage Expansion

- [x] Task: Add unit test for markdown rendering in `run_session`.
  - [x] Task: Create test `test_run_session_renders_markdown` in `tests/test_cli.py`.
    - Mock `engine.ask()` to return markdown containing headers, bold, lists, and code blocks.
    - Patch `console` to capture Rich-rendered output (use `Console(file=StringIO(), force_terminal=True)`).
    - Assert that raw markdown syntax (`**`, `##`, `` ``` ``) does NOT appear in the rendered output.
    - Assert that the rendered text contains the content words (e.g., "Summary", "Key points") without markdown delimiters.
  - [x] Task: Create test `test_run_session_renders_markdown_with_brackets` in `tests/test_cli.py`.
    - Mock `engine.ask()` to return text containing square brackets (e.g., `"See [1] and [important note]"`).
    - Assert the output contains the brackets literally (not interpreted as Rich markup).
  - [x] Task: Create test `test_run_session_handles_empty_response` in `tests/test_cli.py`.
    - Mock `engine.ask()` to return `""`.
    - Assert no crash occurs and output still includes the "Assistant:" label.
- [x] Task: Add integration-level test for markdown rendering.
  - [x] Task: Extend the existing mock integration test (`tests/test_integration.py`) or add a companion test that verifies the full pipeline (mock Gemini returning markdown → CLI renders it).
  - [x] Task: Follow existing mock patterns from `test_engines_gemini.py` (use `_make_stream_chunks` helper with markdown content).
- [x] Task: Ensure no regressions in existing tests.
  - [x] Task: Run the full test suite (`pytest tests/`) and confirm all existing tests pass.
  - [x] Task: Verify that the 2 existing CLI tests (`test_cli_loads_cached_transcript`, `test_cli_invalid_url_shows_clean_error`) still pass — they patch `run_session` so the change should be invisible to them.
  - [x] Task: Verify the integration E2E test (`test_integration_e2e.py`) still passes — it checks for `"Assistant:" in result.output` which should remain true.
- [x] Task: Conductor - User Manual Verification 'Test Coverage Expansion' (Protocol in workflow.md)

## Phase 4: Refinement and Verification

- [x] Task: Manual verification with a real video.
- [x] Task: Run the CLI against a video (e.g., "Me at the zoo").
- [x] Task: Ask a question that produces a list or bold text (e.g., "Summarize this in bullet points").
- [x] Task: Confirm visually that the output is formatted correctly.
- [x] Task: Ask a question that produces a code block (e.g., "Show me example Python code for this concept").
- [x] Task: Ask a question that produces headers and sub-headers (e.g., "Give me a structured breakdown of the video topics").
- [x] Task: Ask a question whose answer contains square brackets (e.g., "List references with citation numbers").
- [x] Task: Ensure no regressions in other output (errors, prompts).
- [x] Task: Verify the REPL greeting panel (`Panel(...)` at `cli.py:25`) still renders correctly.
- [x] Task: Verify error messages (API errors at `cli.py:36-42`, invalid URL at `cli.py:79`) display with correct Rich markup styling.
- [x] Task: Verify status messages (cache hit, fetching, transcribing) at `cli.py:88-107` are unchanged.
- [x] Task: Verify the "Session saved" message at `cli.py:54` is unchanged.

- [x] Task: Performance check.
- [x] Task: Confirm that `Markdown()` parsing does not introduce visible latency on typical responses (1-2 KB of markdown). Rich's Markdown parser is O(n) on input size and operates in-memory — no perceivable delay expected.

- [x] Task: Conductor - User Manual Verification 'Refinement and Verification' (Protocol in workflow.md)

## Appendix: Files to Modify

| File                          | Change                                                                      | Lines         |
| ----------------------------- | --------------------------------------------------------------------------- | ------------- |
| `src/ask_video/cli.py`      | Add `from rich.markdown import Markdown` import                           | Line 7        |
| `src/ask_video/cli.py`      | Replace single `console.print()` with label + `Markdown()` + blank line | Line 48       |
| `tests/test_cli.py`         | Add 3 new tests for markdown rendering, brackets, and empty response        | New tests     |
| `tests/test_integration.py` | Optionally extend with markdown-aware assertion                             | Existing test |

**Total production code change: 2 lines modified, 1 line added (import).**

# Specification: Enhance CLI Input with Multi-line Support

## Overview
The current CLI REPL loop uses Rich's `console.input()` (see `cli.py:30`), which immediately submits the user's input upon pressing Enter. This prevents users from typing multi-line prompts or formatting their questions. This track replaces `console.input()` with a `prompt_toolkit` `PromptSession` for the main chat REPL, enabling true multi-line editing, command history, and helpful UI cues.

## Functional Requirements

### Multi-line Input
- **Newline:** `Enter` inserts a newline (natural typing behavior).
- **Submission:** `Esc` then `Enter` submits the prompt. On terminals with Meta configured, `Option+Enter` (macOS) or `Alt+Enter` (Linux/Windows) also submits.
- **Rationale:** This is the default behavior of prompt_toolkit's `multiline=True` mode. `Enter` for newline is the most intuitive UX for multi-line input — users type naturally and use a deliberate key sequence to submit. This matches Jupyter, IPython, and other multi-line CLI tools. `Esc→Enter` is documented as the primary submit method because it works universally across all terminals without configuration. `Option+Enter` requires terminal-specific setup on macOS (Terminal.app: "Use Option as Meta key"; iTerm2: Left Option → "Esc+").

### Enhanced Prompt
- **Command History:** Navigate previous inputs using Up/Down arrows. History is persisted to disk.
- **Bottom Toolbar:** Display key binding hints (e.g., `Enter: New Line | Esc→Enter: Submit | Ctrl+D: Exit`).
- **Prompt Indicator:** Display `You: ` prompt prefix, styled to match the existing CLI theme.

### Scope
- This enhanced input method replaces `console.input()` **only** within the `run_session()` REPL loop (`cli.py:30`).
- Other prompts (menus, confirmations) remain unchanged.
- Rich Console continues to own all **output** rendering (Markdown, panels, styled text). prompt_toolkit owns only the **input** phase.

### Non-Interactive Fallback
- When `sys.stdin.isatty()` is `False` (piped input, CI environments, testing), fall back to plain `input()` or accept injected input. The application must NOT crash when no TTY is available.

## Non-Functional Requirements
- **Dependencies:** Add `prompt-toolkit>=3.0.43` (Python 3.12 compatibility). Add `pygments>=2.17` if syntax highlighting is implemented.
- **Performance:** The prompt must feel responsive with no perceptible lag on session creation.
- **Compatibility:** `Esc→Enter` for submit works universally across all terminals. `Option+Enter` / `Alt+Enter` for submit requires Meta key configuration on macOS terminals.
- **Terminal Handoff:** prompt_toolkit and Rich must NOT control the terminal simultaneously. Sequence: prompt_toolkit → capture input → release terminal → Rich renders output.

## Acceptance Criteria
- [ ] User types a multi-line prompt using `Enter` for newlines.
- [ ] The prompt does NOT submit when `Enter` is pressed (it inserts a newline).
- [ ] The prompt submits successfully when the user presses `Esc` then `Enter` (or `Option+Enter` with Meta configured).
- [ ] Previous inputs can be recalled using Up/Down arrows.
- [ ] A bottom toolbar displays usage hints.
- [ ] The CLI does not crash or behave unexpectedly on empty input or special characters.
- [ ] `Ctrl+C` interrupts the current input (does not crash the app).
- [ ] `Ctrl+D` on an empty prompt exits the session gracefully (like `exit`/`quit`).
- [ ] Pasting multi-line text via clipboard inserts all lines without submitting (bracketed paste mode).
- [ ] The prompt prefix (`You:`) matches the existing CLI color scheme.
- [ ] `exit` and `quit` commands continue to work as before.
- [ ] Rich Markdown rendering of AI responses is unaffected by the prompt_toolkit integration.
- [ ] The CLI works in non-interactive mode (piped stdin) without crashing.
- [ ] All existing tests in `test_cli.py` continue to pass (with updated mocking strategy).

## Out of Scope
- Custom auto-completion for complex commands (beyond simple history matching).
- Changing input methods for non-REPL prompts.
- Syntax highlighting of user input (deferred — adds complexity with minimal value for chat input).
- Auto-suggestion from history (deferred — can be added later without architecture changes).

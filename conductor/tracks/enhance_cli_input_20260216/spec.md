# Specification: Enhance CLI Input with Multi-line Support

## Overview
The current CLI REPL loop uses Python's standard `input()`, which immediately submits the user's input upon pressing Enter or Shift+Enter (which sends a newline character in most terminals). This prevents users from typing multi-line prompts or formatting their questions. This track aims to replace the basic `input()` with a robust `prompt_toolkit` implementation for the main chat REPL, enabling true multi-line editing, history, syntax highlighting, and helpful UI cues.

## Functional Requirements
- **Multi-line Input:** Users must be able to type multiple lines of text before submitting their query.
    - **Key Binding:** `Shift+Enter` (or `Alt+Enter` depending on terminal compatibility) should insert a newline without submitting.
    - **Submission:** Pressing `Enter` alone should submit the prompt.
- **Enhanced Prompt:** The input prompt should leverage `prompt_toolkit` features:
    - **Syntax Highlighting:** Basic highlighting for the user's input (e.g., Markdown or plain text).
    - **Command History:** Allow users to navigate through previous inputs using Up/Down arrows.
    - **Auto-suggestion:** Provide subtle suggestions based on history or context (if applicable).
    - **Bottom Toolbar:** Display helpful key binding hints (e.g., "Shift+Enter: New Line | Enter: Submit").
- **Scope:** This enhanced input method will replace the standard `console.input()` *only* within the main chat REPL loop. Other prompts (menus, confirmations) remain unchanged.

## Non-Functional Requirements
- **Dependency:** Add `prompt_toolkit` as a dependency.
- **Performance:** The prompt should feel responsive and not introduce perceptible lag.
- **Compatibility:** Ensure key bindings work across major terminal emulators (macOS Terminal, iTerm2, Windows Terminal, Linux GNOME Terminal). Note: `Shift+Enter` support can vary; fallback instructions may be needed.

## Acceptance Criteria
- [ ] A user types a multi-line prompt (e.g., a list or code block) using the configured key combination for newlines.
- [ ] The prompt does *not* submit prematurely when a newline is inserted.
- [ ] The prompt submits successfully when the user presses `Enter`.
- [ ] Previous inputs can be recalled using Up/Down arrows.
- [ ] A bottom toolbar displays usage hints.
- [ ] The CLI does not crash or behave unexpectedly on empty input or special characters.

## Out of Scope
- Implementing custom auto-completion for complex commands (beyond simple history matching).
- Changing input methods for non-REPL prompts.

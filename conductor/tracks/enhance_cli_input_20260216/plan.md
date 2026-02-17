# Implementation Plan - Enhance CLI Input with Multi-line Support

## Phase 1: Exploration and Prototype
- [ ] Task: Create a prototype script to test `prompt_toolkit` integration.
    - [ ] Task: Install `prompt_toolkit` dependency using `uv`.
    - [ ] Task: Create `scripts/prompt_prototype.py`.
    - [ ] Task: Implement a basic prompt loop using `PromptSession`.
    - [ ] Task: Configure key bindings: `Shift+Enter` (or `Alt+Enter` fallback) for newline, `Enter` for submit.
    - [ ] Task: Add a bottom toolbar with usage hints.
    - [ ] Task: Verify behavior across different terminals (if possible, or document limitations).
- [ ] Task: Conductor - User Manual Verification 'Exploration and Prototype' (Protocol in workflow.md)

## Phase 2: Implementation (TDD)
- [ ] Task: Integrate `prompt_toolkit` into the main application.
    - [ ] Task: Add `prompt_toolkit` to project dependencies in `pyproject.toml`.
    - [ ] Task: Create a new module `src/ask_video/ui/prompt.py` to encapsulate the prompt logic.
        - [ ] Task: Define a `PromptManager` class or function that handles session creation and input loops.
        - [ ] Task: Implement syntax highlighting (e.g., Markdown lexer).
        - [ ] Task: Implement history persistence (e.g., to a file in `.ask_video/history`).
        - [ ] Task: Implement the bottom toolbar.
    - [ ] Task: Update `src/ask_video/cli.py` to use `PromptManager` instead of `console.input()`.
- [ ] Task: Write tests for the new prompt logic.
    - [ ] Task: Mock `prompt_toolkit`'s `PromptSession` to test input handling without blocking.
    - [ ] Task: Verify that key bindings trigger expected actions (newline vs submit).
    - [ ] Task: Verify history saving and loading.
- [ ] Task: Conductor - User Manual Verification 'Implementation (TDD)' (Protocol in workflow.md)

## Phase 3: Refinement and Verification
- [ ] Task: Polish the user experience.
    - [ ] Task: Adjust colors/styles to match the CLI theme.
    - [ ] Task: Ensure the prompt handles empty inputs gracefully.
    - [ ] Task: Test edge cases: pasting large blocks of text, special characters.
- [ ] Task: Manual verification.
    - [ ] Task: Run the full application.
    - [ ] Task: Enter a multi-line query using the new key bindings.
    - [ ] Task: Confirm submission and response.
    - [ ] Task: Recall previous commands from history.
- [ ] Task: Conductor - User Manual Verification 'Refinement and Verification' (Protocol in workflow.md)

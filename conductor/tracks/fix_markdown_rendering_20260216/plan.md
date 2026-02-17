# Implementation Plan - Fix Markdown Rendering in CLI Chat Output

## Phase 1: Exploration and Reproduction
- [ ] Task: Create a reproduction script or manual test case.
    - [ ] Task: Identify the code responsible for printing the AI response in `ask_video/cli.py` (likely in `run_session` or similar).
    - [ ] Task: Create a test case in `tests/test_cli.py` that mocks a markdown response from Gemini (e.g., `**Bold**`).
    - [ ] Task: Verify that the current output contains raw markdown characters (e.g., `**`).
- [ ] Task: Conductor - User Manual Verification 'Exploration and Reproduction' (Protocol in workflow.md)

## Phase 2: Implementation (TDD)
- [ ] Task: Update the printing logic to use `rich.markdown.Markdown`.
    - [ ] Task: Import `Markdown` from `rich.markdown`.
    - [ ] Task: Modify the output function to wrap the AI response text in `Markdown(text)`.
    - [ ] Task: Ensure that `console.print` handles the `Markdown` object correctly.
- [ ] Task: Run the reproduction test case again.
    - [ ] Task: Verify that the output no longer contains raw markdown syntax (e.g., `**` should be gone, replaced by formatting codes or just the text).
- [ ] Task: Conductor - User Manual Verification 'Implementation (TDD)' (Protocol in workflow.md)

## Phase 3: Refinement and Verification
- [ ] Task: Manual verification with a real video.
    - [ ] Task: Run the CLI against a video (e.g., "Me at the zoo").
    - [ ] Task: Ask a question that produces a list or bold text (e.g., "Summarize this in bullet points").
    - [ ] Task: Confirm visually that the output is formatted correctly.
- [ ] Task: Ensure no regressions in other output (errors, prompts).
- [ ] Task: Conductor - User Manual Verification 'Refinement and Verification' (Protocol in workflow.md)

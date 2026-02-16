# Implementation Plan - End-to-End Live Integration Test

## Phase 1: Test Infrastructure Setup (Live)
- [x] Task: Create a new test file `tests/test_integration_e2e.py` and import necessary modules (`mock`, `pytest`, `ask_video` components). 83b48f2
- [x] Task: Update `tests/test_integration_e2e.py` to remove mock fixtures and instead add a `live_store` fixture using `tmp_path`. 0973b6d
    - [ ] Task: Remove `mock_youtube_api` and `mock_genai`.
    - [ ] Task: Ensure `GEMINI_API_KEY` check is in place (skip test if missing).
- [ ] Task: Conductor - User Manual Verification 'Test Infrastructure Setup (Live)' (Protocol in workflow.md)

## Phase 2: Implement Live Test Logic
- [ ] Task: Write the `test_e2e_live_flow` test case.
    - [ ] Task: Use `CliRunner` with `env={"GEMINI_API_KEY": "..."}` (passed from real env).
    - [ ] Task: Run against a stable YouTube video (e.g., "Me at the zoo" - `jNQXAC9IVRw`).
    - [ ] Task: Send input `What is this video about?\nexit\n`.
- [ ] Task: Verify Real Side Effects.
    - [ ] Task: Assert that the CLI output contains "Found YouTube captions" (or similar).
    - [ ] Task: Assert that the CLI output contains a response from Gemini (check for non-empty string or key words).
    - [ ] Task: Assert that the transcript file exists in the `tmp_path` cache directory.
- [ ] Task: Conductor - User Manual Verification 'Implement Live Test Logic' (Protocol in workflow.md)

## Phase 3: Execution and Refinement
- [ ] Task: Run the live test with `uv run pytest tests/test_integration_e2e.py`.
    - [ ] Task: Verify it passes with a valid key.
- [ ] Task: specific check to ensure 80% coverage is maintained or improved.
- [ ] Task: Conductor - User Manual Verification 'Execution and Refinement' (Protocol in workflow.md)

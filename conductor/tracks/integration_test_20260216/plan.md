# Implementation Plan - End-to-End Integration Test

## Phase 1: Test Infrastructure Setup
- [x] Task: Create a new test file `tests/test_integration_e2e.py` and import necessary modules (`mock`, `pytest`, `ask_video` components). 83b48f2
    - [ ] Task: Create the test file and add imports.
- [x] Task: Define a `pytest` fixture to simulate the CLI environment and mock external dependencies (`youtube_transcript_api`, `google.genai`). d296c0d
    - [ ] Task: specific fixture for mocking YouTube API.
    - [ ] Task: specific fixture for mocking Gemini API.
    - [ ] Task: specific fixture for temporary file system (using `tmp_path`).
- [ ] Task: Conductor - User Manual Verification 'Test Infrastructure Setup' (Protocol in workflow.md)

## Phase 2: Implement Test Logic
- [ ] Task: Write the test case `test_e2e_flow` that simulates the user running `ask_video <url>`.
    - [ ] Task: Write test logic to invoke the CLI runner.
    - [ ] Task: Assert that `YouTubeSource.extract_id` is called correctly.
    - [ ] Task: Assert that `YouTubeSource.fetch_transcript` is called and returns mock data.
- [ ] Task: Verify caching behavior within the test.
    - [ ] Task: Assert that a transcript file is created in the expected hashed directory.
    - [ ] Task: Assert that a second call with the same URL does *not* trigger a new fetch (hits cache).
- [ ] Task: Verify REPL and Gemini Interaction.
    - [ ] Task: Simulate user input for a question.
    - [ ] Task: Assert `GeminiEngine.ask` is called with the correct transcript context.
    - [ ] Task: Assert the CLI outputs the mocked AI response.
- [ ] Task: Conductor - User Manual Verification 'Implement Test Logic' (Protocol in workflow.md)

## Phase 3: Execution and Refinement
- [ ] Task: Run the newly created test with `pytest tests/test_integration_e2e.py`.
    - [ ] Task: Execute tests and capture output.
- [ ] Task: Fix any failures or bugs revealed by the test execution.
    - [ ] Task: Refine mocks or application logic if discrepancies are found.
- [ ] Task: specific check to ensure 80% coverage is maintained or improved.
    - [ ] Task: Run `pytest --cov=ask_video` and verify coverage report.
- [ ] Task: Conductor - User Manual Verification 'Execution and Refinement' (Protocol in workflow.md)

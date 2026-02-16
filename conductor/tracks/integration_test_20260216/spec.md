# Specification: End-to-End Integration Test

## Goal
Implement a robust end-to-end integration test that verifies the core functionality of the `ask-video` CLI. This test will ensure that the system can successfully fetch a YouTube video transcript, cache it locally, and allow a user to query the content via the Gemini-powered REPL interface.

## Core Requirements
- **Transcript Fetching:** Verify that the system can retrieve captions from a valid YouTube URL using `youtube-transcript-api`.
- **Caching Mechanism:** Confirm that the fetched transcript is correctly stored in the local cache (hashed ID) and retrieved on subsequent requests to prevent redundant API calls.
- **REPL Interaction:** Simulate a user interaction within the REPL loop, sending a question to the Gemini engine and receiving a valid response based on the transcript context.
- **Gemini Integration:** Ensure the `QAEngine` correctly formats the prompt with the transcript and conversation history before sending it to the Google GenAI API.

## Testing Strategy
- **Mocking External APIs:** Since this is an automated test suite, external calls to YouTube and Google Gemini APIs should be mocked to ensure determinism and avoid network dependency or cost.
- **Data Verification:** Assert that the data passed to the mocks (video ID, prompt content) matches expected values.
- **State Validation:** Check the state of the local file system (cache directory) to verify persistence.

## Success Criteria
- A new test file `tests/test_integration_e2e.py` is created.
- The test suite passes when run with `pytest`.
- The test covers the "happy path": URL input -> Transcript Fetch -> Cache Write -> REPL Query -> Answer Output.

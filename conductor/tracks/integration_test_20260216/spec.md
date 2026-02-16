# Specification: End-to-End Live Integration Test

## Goal
Implement a **live** end-to-end integration test that verifies the full operational flow of the `ask-video` CLI against real external services. This test serves as a final "smoke test" to ensure that the system works in the real world, connecting successfully to YouTube and Google Gemini.

## Core Requirements
- **Real YouTube Connection:** The system must fetch *actual* captions from a live YouTube video URL.
- **Real Gemini API Call:** The system must send a request to the live Google Gemini API and receive a generated response.
- **Real Filesystem Caching:** The system must write the fetched transcript to the actual disk (using a temporary directory for isolation) and read it back on subsequent calls.
- **Interactive REPL Simulation:** The test must simulate a user entering a question and then exiting the REPL, ensuring the CLI handles standard input/output correctly during a live session.

## Testing Strategy
- **No Mocks:** **Crucially, no external APIs will be mocked.** This test validates the network path, API authentication, and payload formats against the real providers.
- **Environment Dependency:** The test requires a valid `GEMINI_API_KEY` environment variable to function. It should skip or fail clearly if this is missing.
- **Live Data Validation:**
    - Use a stable, short, public YouTube video (e.g., "Me at the zoo" or a stable Google Cloud Tech video) to minimize flakiness.
    - Assert that the response from Gemini is non-empty and coherent (though exact text matching is impossible with LLMs).
- **Isolation:** Use a temporary directory for the `TranscriptStore` to avoid polluting the user's actual `.ask_video` cache.

## Success Criteria
- The test file `tests/test_integration_e2e.py` is updated to remove mocks.
- The test passes when run with a valid `GEMINI_API_KEY`.
- The test verifies that a cache file is created on disk.
- The test verifies that a real answer is received from Gemini.

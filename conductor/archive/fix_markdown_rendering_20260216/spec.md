# Specification: Fix Markdown Rendering in CLI Chat Output

## Overview
The CLI chat interface currently displays raw markdown syntax (e.g., `**text**`, `## Header`) instead of rendering it as formatted text. This negatively impacts readability and the user experience. This track aims to fix the rendering issue by ensuring that all AI responses are properly processed and displayed using the `rich.markdown.Markdown` class.

## Functional Requirements
- **Render Markdown:** All text responses from the Gemini AI engine must be rendered as formatted Markdown in the CLI.
    - **Bold:** `**text**` should appear as **bold text**.
    - **Headers:** `## Header` should appear as a styled header.
    - **Lists:** `- Item` and `1. Item` should be formatted as lists.
    - **Code Blocks:** ` ```code``` ` should be syntax highlighted.
    - **Other Elements:** Blockquotes, links, and other standard markdown features should render correctly.
- **Global Application:** This fix must apply to all standard chat outputs within the `ask-video` CLI.

## Non-Functional Requirements
- **Performance:** Rendering should not introduce noticeable latency.
- **Readability:** The default `rich` markdown theme should be used to ensure high contrast and readability in various terminal environments.
- **Robustness:** The renderer should handle potentially malformed markdown gracefully without crashing.

## Acceptance Criteria
- [ ] A user asks a question that triggers a markdown response (e.g., "Give me a list of key points").
- [ ] The output displays a properly formatted list, not raw markdown characters.
- [ ] Headers in the response are distinct and styled.
- [ ] Code blocks (if any) are syntax highlighted.
- [ ] No regression in other CLI output formatting (e.g., error messages).

## Out of Scope
- Customizing the markdown theme or colors beyond the `rich` defaults.
- Markdown rendering for user input (input is treated as raw text).
- Markdown rendering for error messages or help text (unless incidentally improved).

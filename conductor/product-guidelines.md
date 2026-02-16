# Product Guidelines

## Tone and Voice
- **Professional & Concise:** Communicate efficiently, respecting the user's time and context as a CLI tool.
- **Friendly & Helpful:** Use a welcoming and supportive tone, especially when guiding users or handling errors.
- **Technical & Detailed:** Provide depth and clarity in explanations, catering to users who appreciate technical precision.

## Visual Design
- **Rich Formatting:** utilize the `rich` library to employ colors, bold text, and other styles to clearly distinguish between user input, system messages, and AI responses.
- **Structured Output:** Use tables, panels, and other structured elements to present information in a readable and organized manner.
- **Progress Indicators:** Implement progress bars for long-running operations like downloading or transcribing to keep users informed.
- **Engaging Elements:** Use emojis judiciously to make the interface more engaging and visually distinct.
- **Standard Output Compliance:** Ensure that the tool adheres to standard terminal conventions for stdout to support piping and scripting.

## User Interaction & Error Handling
- **Clear Error Messages:** Provide actionable error messages with suggested solutions to help users resolve issues quickly.
- **Interactive REPL:** Support a Read-Eval-Print Loop (REPL) for interactive Q&A sessions, allowing for a conversational flow.
- **Interactive Configuration:** Offer an interactive wizard for first-time setup to simplify the configuration process.
- **Command-Line Arguments:** Support standard flags and arguments for non-interactive use and automation.
- **Clean UI Logging:** Log detailed errors to a file for debugging purposes while keeping the user interface clean and uncluttered.

## Accessibility & Inclusivity
- **High Contrast:** Default to high-contrast color schemes to ensure readability for all users.
- **Clear Language:** Use simple, clear language and avoid overly complex jargon to make the tool accessible to a broad audience.

## Code & Contribution Standards
- **Dependency Management:** Use `uv` for all package management and environment handling.
- **Type Safety:** Enforce type hints throughout the codebase to ensure compatibility with `mypy` and improve code reliability.
- **Style Enforcement:** Adhere strictly to PEP 8 style guidelines, enforced by tools like `ruff` or `black`.
- **Testing:** Maintain high test coverage with unit tests for all core logic using `pytest`.
- **Naming Conventions:** Use clear, descriptive variable and function names to enhance code readability.
- **Documentation:** Document all public modules and functions thoroughly to support contributors and users.

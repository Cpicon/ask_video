# Contributing to ask-video

We welcome contributions! Please follow these guidelines.

## Development Setup

This project uses `uv` for dependency management.

1.  **Install `uv`:**
    Follow the instructions in the [README](README.md).

2.  **Install Dependencies:**
    ```bash
    uv sync
    ```

3.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```

## Running Tests

```bash
uv run pytest
```

## Adding Dependencies

To add a new dependency:
```bash
uv add <package_name>
```

To add a dev dependency:
```bash
uv add --dev <package_name>
```

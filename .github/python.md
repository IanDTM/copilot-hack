# GitHub Copilot Instructions for Python Whack a mole

## Project Overview
This is a Python web application (Flask) integrating Azure AI services (OpenAI, Speech, Search) with a responsive JS frontend.
- **Core Stack**: Python 3.11+, Flask, JavaScript (ES6+), Azure SDKs.
- **Architecture**: Modular service-oriented architecture (`app/*_service.py`) with graceful degradation.
- **Dependency Manager**: `uv`.

## Critical Coding Standards
**Strictly enforced rules - violations will fail CI:**

1.  **Function Complexity Limit**:
    - **MAXIMUM 50 STATEMENTS** per function (PLR0915).
    - **Action**: If a function exceeds this, you MUST refactor it immediately using helper functions.
    - **Strategy**: Extract validation, preprocessing, and post-processing into private `_helper_methods`.

2.  **Refactoring Patterns**:
    - **Early Returns**: Use guard clauses to reduce nesting.
    - **Decomposition**: Break complex conditionals into named boolean functions (e.g., `_is_upload_valid(...)`).
    - **Comprehensions**: Prefer list/dict comprehensions over loops for simple transformations.

3.  **Type Safety & Documentation**:
    - All function signatures must have type hints.
    - All public modules, classes, and functions must have docstrings.

4.  **Logging**:
    - Use the `logging` module for all logs.
    - Log at appropriate levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

5. **Multi threading & Async**:
    - Use `concurrent.futures` or `asyncio` for I/O-bound tasks.
    - Ensure thread safety when accessing shared resources.

6. **Multi User Considerations**:
    - Ensure session management is robust.
    - Validate and sanitize all user inputs to prevent injection attacks.
    - Assume that multiple users may interact with the system simultaneously.
    
## Azure Integration Guidelines
- **Service Pattern**: Each Azure service (LLM, Speech, Storage) is encapsulated in a singleton class in `app/`.
- **Graceful Degradation**: ALWAYS check `service.is_enabled` before using an Azure service. Provide local fallbacks.
- **Configuration**: Access settings via `app.config` or `os.environ`. Do not hardcode credentials.
- **Authentication**: Prefer `DefaultAzureCredential` combined with connection strings/keys as fallbacks.

## Development Workflow
- **Package Management**: Use `uv` for dependencies.
    - Install: `uv pip install -e .`
- **Linting & Formatting**:
    - Run: `ruff check .` (Fixes enabled in config).
    - Config: See `[tool.ruff]` in `pyproject.toml`.
- **Testing**:
    - Run: `pytest` (or `.venv/bin/python -m pytest`).
    - Tests are located in `tests/`.

## Key Files & Directories
- `app/app.py`: Application factory and configuration.
- `app/routes/`: Blueprint definitions (API endpoints).
- `app/*_service.py`: Azure service integrations (LLM, Speech, Cosmos, Search).
- `app/business_logic.py`: Core application logic (agnostic of HTTP layer).
- `AI_CODING_GUIDELINES.md`: Detailed refactoring and complexity rules.

# Whack-a-Mole Testing

This directory contains comprehensive unit and integration tests for the whack-a-mole game.

## Test Structure

```
tests/
├── backend/              # Python backend tests
│   ├── conftest.py       # Shared fixtures
│   ├── unit/             # Unit tests
│   │   ├── test_difficulty.py
│   │   ├── test_game_state.py
│   │   └── test_handlers.py
│   └── integration/      # Integration tests
│       └── test_threads.py
└── frontend/             # JavaScript frontend tests
    ├── setup.js          # Jest configuration
    ├── unit/             # Unit tests
    │   ├── game.test.js
    │   └── gameWorker.test.js
    └── integration/      # Integration tests (future)
```

## Running Tests

### Backend Tests (Python/Pytest)

```bash
# Run all backend tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run specific test file
uv run pytest tests/backend/unit/test_game_state.py

# Run specific test
uv run pytest tests/backend/unit/test_handlers.py::TestHandleWhack::test_whack_valid_hole_number_1

# Run only unit tests
uv run pytest tests/backend/unit/ -v

# Run only integration tests
uv run pytest tests/backend/integration/ -v

# Run tests by marker
uv run pytest -m thread  # Threading tests
uv run pytest -m "not slow"  # Skip slow tests
```

### Frontend Tests (JavaScript/Jest)

```bash
# Run all frontend tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- game.test.js
```

## Test Coverage

### Backend Tests

#### High Priority ✅
- ✅ **Difficulty validation** - All enum values and settings
- ✅ **GameState** - Properties, reset, thread-safety
- ✅ **handle_whack** - Hole validation (1-6), hit/miss logic, score updates
- ✅ **submit_high_score** - XSS prevention, sorting, top 10 limit
- ✅ **Thread safety** - Concurrent score updates, lock behavior

#### Integration Tests ✅
- ✅ **MoleSpawnerThread** - Mole spawning (1-6 range), miss counting, cleanup
- ✅ **GameTimerThread** - Timer updates, accuracy
- ✅ **Thread cleanup** - Proper shutdown on disconnect
- ✅ **Thread synchronization** - Race condition prevention

### Frontend Tests

#### Unit Tests ✅
- ✅ **Position generation** - Collision detection, minimum distance
- ✅ **XSS prevention** - HTML escaping in escapeHtml()
- ✅ **Accuracy calculation** - Percentage, division by zero handling
- ✅ **Game state** - Initial values, state management
- ✅ **High scores** - Rendering, empty state, medal display
- ✅ **Hole validation** - Valid range (1-6), type checking
- ✅ **Worker timing** - Progress calculation, remaining time, flags

## Test Markers

Tests can be marked with the following markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests with dependencies
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.thread` - Tests involving threading/concurrency

## Fixtures

### Backend Fixtures (conftest.py)

- `flask_app` - Flask application instance
- `client` - Flask test client
- `socketio_client` - SocketIO test client
- `game_state` - Fresh GameState instance
- `game_state_easy/medium/hard` - GameState with specific difficulty
- `mock_session_id` - Mock session ID
- `sample_high_scores` - Sample high score data
- `cleanup_game_states` - Auto-cleanup after tests

### Frontend Setup (setup.js)

- Mocked `io` (Socket.IO client)
- Mocked `Worker` (Web Worker)
- Mocked console methods
- Auto-cleanup after each test

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run backend tests
  run: uv run pytest --cov --cov-report=xml

- name: Run frontend tests
  run: npm test -- --coverage --ci
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass locally
3. Maintain >80% code coverage
4. Add appropriate markers
5. Update this README if needed

## Test Categories

### Critical Business Logic
- Whack validation (hole 1-6)
- Score and miss counting
- High score sorting and limits
- Thread-safety

### Important Features
- Mole spawn randomness
- Reaction time calculation
- Timer accuracy
- Position collision detection

### Edge Cases
- Invalid inputs (negative, out of range)
- Division by zero
- Concurrent operations
- XSS prevention

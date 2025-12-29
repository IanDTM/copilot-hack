"""
Pytest configuration and shared fixtures for backend tests.
"""

import pytest
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app import app, socketio, GameState, Difficulty, game_states  # noqa: E402


@pytest.fixture
def flask_app():
    """Create and configure a Flask application instance for testing."""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    yield app


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask application."""
    return flask_app.test_client()


@pytest.fixture
def socketio_client(flask_app):
    """Create a test client for SocketIO."""
    return socketio.test_client(flask_app)


@pytest.fixture
def game_state():
    """Create a fresh GameState instance for testing."""
    return GameState()


@pytest.fixture
def game_state_easy():
    """Create a GameState instance with EASY difficulty."""
    return GameState(Difficulty.EASY)


@pytest.fixture
def game_state_medium():
    """Create a GameState instance with MEDIUM difficulty."""
    return GameState(Difficulty.MEDIUM)


@pytest.fixture
def game_state_hard():
    """Create a GameState instance with HARD difficulty."""
    return GameState(Difficulty.HARD)


@pytest.fixture
def mock_session_id():
    """Generate a mock session ID for testing."""
    return "test-session-123"


@pytest.fixture(autouse=True)
def cleanup_game_states():
    """Automatically cleanup game_states dict after each test."""
    yield
    # Clear all game states after each test
    game_states.clear()


@pytest.fixture
def sample_high_scores():
    """Sample high scores data for testing."""
    return [
        {"name": "Alice", "score": 100, "date": "2025-12-24"},
        {"name": "Bob", "score": 85, "date": "2025-12-23"},
        {"name": "Charlie", "score": 70, "date": "2025-12-22"},
    ]

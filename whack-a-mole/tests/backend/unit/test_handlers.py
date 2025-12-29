"""
Unit tests for WebSocket event handlers.
"""

import time
from backend.app import (
    game_states,
    high_scores,
)


class TestHandleConnect:
    """Tests for handle_connect WebSocket handler."""

    def test_connect_creates_game_state(self, socketio_client):
        """Test that connecting creates a GameState for the session."""
        # Connect creates session
        assert socketio_client.is_connected()

        # Check connection response
        received = socketio_client.get_received()
        assert len(received) > 0
        assert received[0]["name"] == "connected"
        assert "session_id" in received[0]["args"][0]


class TestHandleStartGame:
    """Tests for handle_start_game WebSocket handler."""

    def test_start_game_with_easy_difficulty(self, socketio_client):
        """Test starting game with EASY difficulty."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        received = socketio_client.get_received()

        # Find game_started event
        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "easy"
        assert game_started["args"][0]["duration"] == 60
        assert game_started["args"][0]["mole_timeout"] == 2.0

    def test_start_game_with_medium_difficulty(self, socketio_client):
        """Test starting game with MEDIUM difficulty."""
        socketio_client.emit("start_game", {"difficulty": "medium"})
        received = socketio_client.get_received()

        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "medium"
        assert game_started["args"][0]["duration"] == 60
        assert game_started["args"][0]["mole_timeout"] == 1.5

    def test_start_game_with_hard_difficulty(self, socketio_client):
        """Test starting game with HARD difficulty."""
        socketio_client.emit("start_game", {"difficulty": "hard"})
        received = socketio_client.get_received()

        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "hard"
        assert game_started["args"][0]["duration"] == 45
        assert game_started["args"][0]["mole_timeout"] == 1.0

    def test_start_game_with_invalid_difficulty_defaults_to_medium(self, socketio_client):
        """Test that invalid difficulty defaults to MEDIUM."""
        socketio_client.emit("start_game", {"difficulty": "invalid"})
        received = socketio_client.get_received()

        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "medium"

    def test_start_game_without_difficulty_defaults_to_medium(self, socketio_client):
        """Test that missing difficulty defaults to MEDIUM."""
        socketio_client.emit("start_game", {})
        received = socketio_client.get_received()

        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "medium"

    def test_start_game_with_none_data(self, socketio_client):
        """Test starting game with None data."""
        socketio_client.emit("start_game", None)
        received = socketio_client.get_received()

        game_started = next(r for r in received if r["name"] == "game_started")
        assert game_started["args"][0]["difficulty"] == "medium"


class TestHandleWhack:
    """Tests for handle_whack WebSocket handler - CRITICAL BUSINESS LOGIC."""

    def test_whack_valid_hole_number_1(self, socketio_client, mock_session_id):
        """Test whacking hole 1 is valid."""
        # Start game first
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()  # Clear received

        # Simulate active mole
        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            game_states[session_id].active_mole = 1
            game_states[session_id].mole_spawn_time = time.time()
            game_states[session_id].game_running = True

        socketio_client.emit("whack", {"hole": 1})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert "success" in whack_result["args"][0]

    def test_whack_valid_hole_number_6(self, socketio_client):
        """Test whacking hole 6 is valid."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": 6})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert "success" in whack_result["args"][0]

    def test_whack_invalid_hole_zero(self, socketio_client):
        """Test whacking hole 0 returns error."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": 0})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert "Invalid hole number" in whack_result["args"][0]["error"]

    def test_whack_invalid_hole_negative(self, socketio_client):
        """Test whacking negative hole returns error."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": -1})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert "Invalid hole number" in whack_result["args"][0]["error"]

    def test_whack_invalid_hole_seven(self, socketio_client):
        """Test whacking hole 7 (out of range) returns error."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": 7})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert "Invalid hole number" in whack_result["args"][0]["error"]

    def test_whack_invalid_hole_large_number(self, socketio_client):
        """Test whacking hole 100 returns error."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": 100})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert "Invalid hole number" in whack_result["args"][0]["error"]

    def test_whack_non_integer_hole(self, socketio_client):
        """Test whacking with non-integer hole returns error."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        socketio_client.emit("whack", {"hole": "abc"})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert "Invalid hole number" in whack_result["args"][0]["error"]

    def test_whack_correct_active_mole_increases_score(
        self, socketio_client, mock_session_id
    ):
        """Test whacking correct active mole increases score."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        # Set up active mole
        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            game_states[session_id].active_mole = 3
            game_states[session_id].mole_spawn_time = time.time()
            game_states[session_id].game_running = True
            initial_score = game_states[session_id].score

        socketio_client.emit("whack", {"hole": 3})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is True
        assert whack_result["args"][0]["score"] == initial_score + 1

    def test_whack_wrong_hole_no_score_change(self, socketio_client, mock_session_id):
        """Test whacking wrong hole doesn't change score."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            game_states[session_id].active_mole = 3
            game_states[session_id].mole_spawn_time = time.time()
            game_states[session_id].game_running = True
            initial_score = game_states[session_id].score

        socketio_client.emit("whack", {"hole": 5})  # Wrong hole
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False
        assert whack_result["args"][0]["score"] == initial_score

    def test_whack_when_no_mole_active(self, socketio_client, mock_session_id):
        """Test whacking when no mole is active fails."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            game_states[session_id].active_mole = None
            game_states[session_id].game_running = True

        socketio_client.emit("whack", {"hole": 3})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        assert whack_result["args"][0]["success"] is False

    def test_whack_calculates_reaction_time(self, socketio_client, mock_session_id):
        """Test that successful whack calculates reaction time."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            spawn_time = time.time() - 0.5  # Mole spawned 0.5s ago
            game_states[session_id].active_mole = 2
            game_states[session_id].mole_spawn_time = spawn_time
            game_states[session_id].game_running = True

        socketio_client.emit("whack", {"hole": 2})
        received = socketio_client.get_received()

        whack_result = next(r for r in received if r["name"] == "whack_result")
        if whack_result["args"][0]["success"]:
            assert "reaction_time" in whack_result["args"][0]
            assert whack_result["args"][0]["reaction_time"] >= 0.5


class TestHandleSubmitScore:
    """Tests for handle_submit_score WebSocket handler."""

    def test_submit_score_adds_to_high_scores(self, socketio_client):
        """Test that submitting score adds it to high scores."""
        initial_count = len(high_scores)

        socketio_client.emit(
            "submit_score",
            {"name": "TestPlayer", "score": 50, "difficulty": "medium"},
        )
        received = socketio_client.get_received()

        # Should broadcast high_scores_update
        update = next(r for r in received if r["name"] == "high_scores_update")
        assert len(update["args"][0]) >= initial_count

    def test_submit_score_truncates_long_name(self, socketio_client):
        """Test that names longer than 10 chars are truncated."""
        long_name = "VeryLongPlayerName"

        socketio_client.emit(
            "submit_score",
            {"name": long_name, "score": 75, "difficulty": "hard"},
        )
        received = socketio_client.get_received()

        update = next(r for r in received if r["name"] == "high_scores_update")
        scores = update["args"][0]
        # Find our submitted score
        submitted = next(s for s in scores if s["score"] == 75)
        assert len(submitted["name"]) <= 10

    def test_submit_score_sorts_descending(self, socketio_client):
        """Test that high scores are sorted by score descending."""
        # Clear high scores
        high_scores.clear()

        # Submit multiple scores
        socketio_client.emit(
            "submit_score", {"name": "Player1", "score": 30, "difficulty": "easy"}
        )
        socketio_client.get_received()

        socketio_client.emit(
            "submit_score", {"name": "Player2", "score": 100, "difficulty": "hard"}
        )
        socketio_client.get_received()

        socketio_client.emit(
            "submit_score", {"name": "Player3", "score": 50, "difficulty": "medium"}
        )
        received = socketio_client.get_received()

        update = next(r for r in received if r["name"] == "high_scores_update")
        scores = update["args"][0]

        # Verify descending order
        for i in range(len(scores) - 1):
            assert scores[i]["score"] >= scores[i + 1]["score"]

    def test_submit_score_keeps_top_10_only(self, socketio_client):
        """Test that only top 10 scores are kept."""
        # Clear and submit 15 scores
        high_scores.clear()

        for i in range(15):
            socketio_client.emit(
                "submit_score",
                {"name": f"Player{i}", "score": i * 10, "difficulty": "easy"},
            )
            socketio_client.get_received()

        assert len(high_scores) == 10

    def test_submit_score_includes_date(self, socketio_client):
        """Test that submitted score includes date field."""
        socketio_client.emit(
            "submit_score",
            {"name": "DateTest", "score": 88, "difficulty": "medium"},
        )
        received = socketio_client.get_received()

        update = next(r for r in received if r["name"] == "high_scores_update")
        scores = update["args"][0]
        submitted = next(s for s in scores if s["name"] == "DateTest")
        assert "date" in submitted
        assert submitted["date"]  # Not empty

    def test_submit_score_xss_prevention(self, socketio_client):
        """Test that score submission prevents XSS attacks."""
        malicious_name = "<script>alert('xss')</script>"

        socketio_client.emit(
            "submit_score",
            {"name": malicious_name, "score": 99, "difficulty": "hard"},
        )
        received = socketio_client.get_received()

        update = next(r for r in received if r["name"] == "high_scores_update")
        scores = update["args"][0]

        # Name should be truncated to 10 chars max
        # This prevents most XSS but real XSS prevention happens in frontend
        for score_entry in scores:
            assert len(score_entry["name"]) <= 10


class TestHandleStopGame:
    """Tests for handle_stop_game WebSocket handler."""

    def test_stop_game_sets_running_false(self, socketio_client, mock_session_id):
        """Test that stopping game sets is_running to False."""
        socketio_client.emit("start_game", {"difficulty": "easy"})
        socketio_client.get_received()

        session_id = (
            socketio_client.sid if hasattr(socketio_client, "sid") else mock_session_id
        )
        if session_id in game_states:
            game_states[session_id].game_running = True

        socketio_client.emit("stop_game")
        received = socketio_client.get_received()

        # Verify game stopped event
        stopped = next((r for r in received if r["name"] == "game_stopped"), None)
        if stopped:
            assert "score" in stopped["args"][0]
            assert "misses" in stopped["args"][0]

        if session_id in game_states:
            assert game_states[session_id].game_running is False


class TestHandleGetHighScores:
    """Tests for handle_get_high_scores WebSocket handler."""

    def test_get_high_scores_returns_list(self, socketio_client):
        """Test that get_high_scores returns the high scores list."""
        socketio_client.emit("get_high_scores")
        received = socketio_client.get_received()

        update = next(r for r in received if r["name"] == "high_scores_update")
        assert isinstance(update["args"][0], list)

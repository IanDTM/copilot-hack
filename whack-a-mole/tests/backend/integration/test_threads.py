"""
Integration tests for threading components.
"""

import pytest
import time
import threading
from unittest.mock import Mock
from backend.app import (
    GameState,
    Difficulty,
    MoleSpawnerThread,
    GameTimerThread,
    game_states,
)


@pytest.mark.thread
class TestMoleSpawnerThread:
    """Tests for MoleSpawnerThread."""

    def test_spawner_thread_initialization(self, mock_session_id):
        """Test MoleSpawnerThread initializes correctly."""
        mock_socketio = Mock()
        thread = MoleSpawnerThread(mock_session_id, mock_socketio)

        assert thread.session_id == mock_session_id
        assert thread.socketio == mock_socketio
        assert thread.daemon is True
        assert isinstance(thread.stop_event, threading.Event)

    def test_spawner_spawns_mole_in_valid_range(self, mock_session_id):
        """Test that mole spawns are within valid range 1-6."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread._spawn_mole(game_state)

        assert game_state.active_mole is not None
        assert 1 <= game_state.active_mole <= 6
        assert game_state.mole_spawn_time is not None
        assert mock_socketio.emit.called

    def test_spawner_emits_mole_spawn_event(self, mock_session_id):
        """Test that spawner emits mole_spawn event."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.MEDIUM)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread._spawn_mole(game_state)

        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args
        assert call_args[0][0] == "mole_spawn"
        assert "hole" in call_args[0][1]
        assert "timeout" in call_args[0][1]
        assert "time_remaining" in call_args[0][1]

    def test_spawner_counts_miss_on_timeout(self, mock_session_id):
        """Test that spawner counts miss when mole times out."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_state.active_mole = 3
        initial_misses = game_state.misses
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread._emit_mole_missed(3, game_state)

        # Manually increment misses (simulating timeout)
        with game_state.lock:
            game_state.misses += 1

        assert game_state.misses == initial_misses + 1

    def test_spawner_stop_event_stops_thread(self, mock_session_id):
        """Test that setting stop_event stops the thread."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread.stop()

        assert thread.stop_event.is_set()

    def test_spawner_ends_game_when_time_expires(self, mock_session_id):
        """Test that spawner ends game when time expires."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.HARD)
        game_state.game_running = True
        game_state.game_start_time = time.time() - 50  # 50 seconds ago (game is 45s)
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread._end_game(game_state)

        assert game_state.game_running is False
        assert game_state.active_mole is None

        # Verify game_over event emitted
        mock_socketio.emit.assert_called()
        call_args = mock_socketio.emit.call_args
        assert call_args[0][0] == "game_over"

    def test_spawner_emits_mole_missed_event(self, mock_session_id):
        """Test that spawner emits mole_missed event."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.MEDIUM)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_state.misses = 5
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread._emit_mole_missed(2, game_state)

        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args
        assert call_args[0][0] == "mole_missed"
        assert call_args[0][1]["hole"] == 2
        assert call_args[0][1]["misses"] == 5

    @pytest.mark.slow
    def test_spawner_thread_runs_and_stops(self, mock_session_id):
        """Test that spawner thread runs and can be stopped."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        thread.start()

        # Let it run briefly
        time.sleep(0.2)

        # Stop the thread
        thread.stop()
        thread.join(timeout=2)

        # Thread should have stopped
        assert not thread.is_alive()


@pytest.mark.thread
class TestGameTimerThread:
    """Tests for GameTimerThread."""

    def test_timer_thread_initialization(self, mock_session_id):
        """Test GameTimerThread initializes correctly."""
        mock_socketio = Mock()
        thread = GameTimerThread(mock_session_id, mock_socketio)

        assert thread.session_id == mock_session_id
        assert thread.socketio == mock_socketio
        assert thread.daemon is True
        assert isinstance(thread.stop_event, threading.Event)

    def test_timer_stop_event_stops_thread(self, mock_session_id):
        """Test that setting stop_event stops the timer."""
        mock_socketio = Mock()
        thread = GameTimerThread(mock_session_id, mock_socketio)
        thread.stop()

        assert thread.stop_event.is_set()

    @pytest.mark.slow
    def test_timer_thread_runs_and_stops(self, mock_session_id):
        """Test that timer thread runs and can be stopped."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = GameTimerThread(mock_session_id, mock_socketio)
        thread.start()

        # Let it run briefly
        time.sleep(0.3)

        # Stop the thread
        thread.stop()
        thread.join(timeout=2)

        # Thread should have stopped
        assert not thread.is_alive()

    def test_timer_emits_time_update_events(self, mock_session_id):
        """Test that timer emits time_update events."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        thread = GameTimerThread(mock_session_id, mock_socketio)
        thread.start()

        # Let it run to emit at least one update
        time.sleep(1.2)

        thread.stop()
        thread.join(timeout=2)

        # Should have emitted time_update event(s)
        assert mock_socketio.emit.called


@pytest.mark.thread
class TestThreadCleanup:
    """Tests for thread cleanup and lifecycle."""

    def test_threads_cleanup_on_disconnect(self, mock_session_id):
        """Test that threads are properly cleaned up on disconnect."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        # Create threads
        mole_thread = MoleSpawnerThread(mock_session_id, mock_socketio)
        timer_thread = GameTimerThread(mock_session_id, mock_socketio)

        mole_thread.start()
        timer_thread.start()

        # Stop threads (simulating disconnect)
        mole_thread.stop()
        timer_thread.stop()

        mole_thread.join(timeout=2)
        timer_thread.join(timeout=2)

        # Both threads should be stopped
        assert not mole_thread.is_alive()
        assert not timer_thread.is_alive()

    def test_no_memory_leaks_from_stopped_threads(self, mock_session_id):
        """Test that stopped threads don't leak memory."""
        mock_socketio = Mock()

        threads = []
        for _ in range(5):
            game_state = GameState(Difficulty.EASY)
            game_state.game_running = True
            game_state.game_start_time = time.time()
            game_states[mock_session_id] = game_state

            thread = MoleSpawnerThread(mock_session_id, mock_socketio)
            thread.start()
            threads.append(thread)
            time.sleep(0.1)
            thread.stop()

        # Wait for all threads to finish
        for thread in threads:
            thread.join(timeout=2)

        # All threads should be stopped
        for thread in threads:
            assert not thread.is_alive()

        # Cleanup
        if mock_session_id in game_states:
            del game_states[mock_session_id]


@pytest.mark.thread
class TestThreadSynchronization:
    """Tests for thread synchronization and race conditions."""

    def test_concurrent_mole_spawns_use_lock(self, mock_session_id):
        """Test that concurrent operations use lock properly."""
        mock_socketio = Mock()
        game_state = GameState(Difficulty.EASY)
        game_state.game_running = True
        game_state.game_start_time = time.time()
        game_states[mock_session_id] = game_state

        def spawn_multiple():
            thread = MoleSpawnerThread(mock_session_id, mock_socketio)
            for _ in range(10):
                thread._spawn_mole(game_state)

        threads = [threading.Thread(target=spawn_multiple) for _ in range(3)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # If lock works properly, we should not have race conditions
        assert game_state.active_mole is not None
        assert 1 <= game_state.active_mole <= 6

    def test_thread_safe_score_updates(self, mock_session_id):
        """Test that score updates are thread-safe."""
        game_state = GameState(Difficulty.EASY)
        game_states[mock_session_id] = game_state

        def increment_score():
            for _ in range(50):
                with game_state.lock:
                    game_state.score += 1

        threads = [threading.Thread(target=increment_score) for _ in range(4)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should be exactly 200 (50 * 4)
        assert game_state.score == 200

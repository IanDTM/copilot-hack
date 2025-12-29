"""
Unit tests for GameState class.
"""

import threading
import time
from backend.app import Difficulty


class TestGameStateInitialization:
    """Tests for GameState initialization."""

    def test_default_initialization(self, game_state):
        """Test GameState initializes with default values."""
        assert game_state.score == 0
        assert game_state.misses == 0
        assert game_state.difficulty == Difficulty.MEDIUM
        assert game_state.is_running is False
        assert game_state.active_mole is None
        assert game_state.mole_spawn_time is None
        assert isinstance(game_state.lock, type(threading.Lock()))

    def test_initialization_with_easy_difficulty(self, game_state_easy):
        """Test GameState initializes with EASY difficulty."""
        assert game_state_easy.difficulty == Difficulty.EASY
        assert game_state_easy.score == 0

    def test_initialization_with_medium_difficulty(self, game_state_medium):
        """Test GameState initializes with MEDIUM difficulty."""
        assert game_state_medium.difficulty == Difficulty.MEDIUM

    def test_initialization_with_hard_difficulty(self, game_state_hard):
        """Test GameState initializes with HARD difficulty."""
        assert game_state_hard.difficulty == Difficulty.HARD


class TestGameStateProperties:
    """Tests for GameState property methods."""

    def test_settings_property_easy(self, game_state_easy):
        """Test settings property returns correct values for EASY."""
        settings = game_state_easy.settings
        assert settings["game_duration"] == 60
        assert settings["mole_timeout"] == 2.0
        assert settings["min_delay"] == 1.0
        assert settings["max_delay"] == 2.5

    def test_settings_property_medium(self, game_state_medium):
        """Test settings property returns correct values for MEDIUM."""
        settings = game_state_medium.settings
        assert settings["game_duration"] == 60
        assert settings["mole_timeout"] == 1.5

    def test_settings_property_hard(self, game_state_hard):
        """Test settings property returns correct values for HARD."""
        settings = game_state_hard.settings
        assert settings["game_duration"] == 45
        assert settings["mole_timeout"] == 1.0

    def test_game_duration_easy(self, game_state_easy):
        """Test game_duration property for EASY difficulty."""
        assert game_state_easy.game_duration == 60

    def test_game_duration_medium(self, game_state_medium):
        """Test game_duration property for MEDIUM difficulty."""
        assert game_state_medium.game_duration == 60

    def test_game_duration_hard(self, game_state_hard):
        """Test game_duration property for HARD difficulty."""
        assert game_state_hard.game_duration == 45

    def test_mole_timeout_easy(self, game_state_easy):
        """Test mole_timeout property for EASY difficulty."""
        assert game_state_easy.mole_timeout == 2.0

    def test_mole_timeout_medium(self, game_state_medium):
        """Test mole_timeout property for MEDIUM difficulty."""
        assert game_state_medium.mole_timeout == 1.5

    def test_mole_timeout_hard(self, game_state_hard):
        """Test mole_timeout property for HARD difficulty."""
        assert game_state_hard.mole_timeout == 1.0

    def test_min_delay_easy(self, game_state_easy):
        """Test min_delay property for EASY difficulty."""
        assert game_state_easy.min_delay == 1.0

    def test_min_delay_medium(self, game_state_medium):
        """Test min_delay property for MEDIUM difficulty."""
        assert game_state_medium.min_delay == 0.75

    def test_min_delay_hard(self, game_state_hard):
        """Test min_delay property for HARD difficulty."""
        assert game_state_hard.min_delay == 0.5

    def test_max_delay_easy(self, game_state_easy):
        """Test max_delay property for EASY difficulty."""
        assert game_state_easy.max_delay == 2.5

    def test_max_delay_medium(self, game_state_medium):
        """Test max_delay property for MEDIUM difficulty."""
        assert game_state_medium.max_delay == 2.0

    def test_max_delay_hard(self, game_state_hard):
        """Test max_delay property for HARD difficulty."""
        assert game_state_hard.max_delay == 1.5


class TestGameStateReset:
    """Tests for GameState reset method."""

    def test_reset_clears_score(self, game_state):
        """Test that reset clears the score."""
        game_state.score = 10
        game_state.reset()
        assert game_state.score == 0

    def test_reset_clears_misses(self, game_state):
        """Test that reset clears misses."""
        game_state.misses = 5
        game_state.reset()
        assert game_state.misses == 0

    def test_reset_clears_active_mole(self, game_state):
        """Test that reset clears active mole."""
        game_state.active_mole = 3
        game_state.reset()
        assert game_state.active_mole is None

    def test_reset_clears_spawn_time(self, game_state):
        """Test that reset clears spawn time."""
        game_state.mole_spawn_time = time.time()
        game_state.reset()
        assert game_state.mole_spawn_time is None

    def test_reset_sets_running_false(self, game_state):
        """Test that reset sets is_running to False."""
        game_state.is_running = True
        game_state.reset()
        assert game_state.is_running is False

    def test_reset_without_difficulty_preserves_difficulty(self, game_state_hard):
        """Test reset without parameter preserves current difficulty."""
        original_difficulty = game_state_hard.difficulty
        game_state_hard.reset()
        assert game_state_hard.difficulty == original_difficulty

    def test_reset_with_difficulty_changes_difficulty(self, game_state_easy):
        """Test reset with difficulty parameter changes difficulty."""
        game_state_easy.reset(Difficulty.HARD)
        assert game_state_easy.difficulty == Difficulty.HARD

    def test_reset_full_state_cleanup(self, game_state):
        """Test that reset clears all state properly."""
        # Set up dirty state
        game_state.score = 15
        game_state.misses = 8
        game_state.active_mole = 2
        game_state.mole_spawn_time = time.time()
        game_state.is_running = True

        # Reset and verify all fields cleared
        game_state.reset(Difficulty.HARD)
        assert game_state.score == 0
        assert game_state.misses == 0
        assert game_state.active_mole is None
        assert game_state.mole_spawn_time is None
        assert game_state.is_running is False
        assert game_state.difficulty == Difficulty.HARD


class TestGameStateThreadSafety:
    """Tests for GameState thread safety."""

    def test_lock_exists(self, game_state):
        """Test that lock object exists."""
        assert hasattr(game_state, "lock")
        assert isinstance(game_state.lock, type(threading.Lock()))

    def test_concurrent_score_updates(self, game_state):
        """Test that concurrent score updates are thread-safe."""
        iterations = 100
        num_threads = 10

        def increment_score():
            for _ in range(iterations):
                with game_state.lock:
                    game_state.score += 1

        threads = [threading.Thread(target=increment_score) for _ in range(num_threads)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should be exactly iterations * num_threads if thread-safe
        assert game_state.score == iterations * num_threads

    def test_concurrent_reset_operations(self, game_state):
        """Test that concurrent resets don't cause race conditions."""
        game_state.score = 100

        def reset_state():
            for _ in range(50):
                game_state.reset()

        threads = [threading.Thread(target=reset_state) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Score should be 0 after all resets
        assert game_state.score == 0
        assert game_state.misses == 0

    def test_lock_can_be_acquired(self, game_state):
        """Test that lock can be acquired and released."""
        acquired = game_state.lock.acquire(timeout=1)
        assert acquired is True
        game_state.lock.release()

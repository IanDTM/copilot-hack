"""
Unit tests for Difficulty enum and DIFFICULTY_SETTINGS.
"""

from backend.app import Difficulty, DIFFICULTY_SETTINGS


class TestDifficultyEnum:
    """Tests for the Difficulty enum."""

    def test_difficulty_enum_values(self):
        """Test that all difficulty levels are defined."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.HARD.value == "hard"

    def test_difficulty_enum_members(self):
        """Test that all expected members exist."""
        assert hasattr(Difficulty, "EASY")
        assert hasattr(Difficulty, "MEDIUM")
        assert hasattr(Difficulty, "HARD")

    def test_difficulty_enum_count(self):
        """Test that there are exactly 3 difficulty levels."""
        assert len(Difficulty) == 3


class TestDifficultySettings:
    """Tests for DIFFICULTY_SETTINGS configuration."""

    def test_all_difficulties_have_settings(self):
        """Test that all difficulty levels have settings defined."""
        for difficulty in Difficulty:
            assert difficulty in DIFFICULTY_SETTINGS

    def test_easy_settings(self):
        """Test EASY difficulty settings."""
        settings = DIFFICULTY_SETTINGS[Difficulty.EASY]
        assert settings["game_duration"] == 60
        assert settings["mole_timeout"] == 2.0
        assert settings["min_delay"] == 1.0
        assert settings["max_delay"] == 2.5

    def test_medium_settings(self):
        """Test MEDIUM difficulty settings."""
        settings = DIFFICULTY_SETTINGS[Difficulty.MEDIUM]
        assert settings["game_duration"] == 60
        assert settings["mole_timeout"] == 1.5
        assert settings["min_delay"] == 0.75
        assert settings["max_delay"] == 2.0

    def test_hard_settings(self):
        """Test HARD difficulty settings."""
        settings = DIFFICULTY_SETTINGS[Difficulty.HARD]
        assert settings["game_duration"] == 45
        assert settings["mole_timeout"] == 1.0
        assert settings["min_delay"] == 0.5
        assert settings["max_delay"] == 1.5

    def test_all_settings_have_required_keys(self):
        """Test that all settings have required keys."""
        required_keys = {"game_duration", "mole_timeout", "min_delay", "max_delay"}
        for difficulty, settings in DIFFICULTY_SETTINGS.items():
            assert set(settings.keys()) == required_keys, (
                f"{difficulty} missing required keys"
            )

    def test_settings_values_are_positive(self):
        """Test that all timing values are positive."""
        for difficulty, settings in DIFFICULTY_SETTINGS.items():
            assert settings["game_duration"] > 0
            assert settings["mole_timeout"] > 0
            assert settings["min_delay"] > 0
            assert settings["max_delay"] > 0

    def test_min_delay_less_than_max_delay(self):
        """Test that min_delay is always less than max_delay."""
        for difficulty, settings in DIFFICULTY_SETTINGS.items():
            assert settings["min_delay"] < settings["max_delay"], (
                f"{difficulty} has invalid delay range"
            )

    def test_difficulty_progression(self):
        """Test that difficulty increases from EASY to HARD."""
        easy = DIFFICULTY_SETTINGS[Difficulty.EASY]
        medium = DIFFICULTY_SETTINGS[Difficulty.MEDIUM]
        hard = DIFFICULTY_SETTINGS[Difficulty.HARD]

        # Mole timeout should decrease (less time to react)
        assert easy["mole_timeout"] > medium["mole_timeout"] > hard["mole_timeout"]

        # Max delay should decrease (moles appear faster)
        assert easy["max_delay"] > medium["max_delay"] > hard["max_delay"]

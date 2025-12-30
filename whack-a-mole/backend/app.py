"""
Whack-a-Mole Game Backend
Multi-threaded Flask server with WebSocket support for real-time game communication.
"""

import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(
    __name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates",
)
app.config["SECRET_KEY"] = "whack-a-mole-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


class Difficulty(Enum):
    """Game difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Difficulty settings: mole_timeout, min_delay, max_delay, game_duration
DIFFICULTY_SETTINGS: dict[Difficulty, dict] = {
    Difficulty.EASY: {
        "mole_timeout": 2.0,
        "min_delay": 1.0,
        "max_delay": 1.5,
        "game_duration": 60,
    },
    Difficulty.MEDIUM: {
        "mole_timeout": 1.5,
        "min_delay": 0.3,
        "max_delay": 1.0,
        "game_duration": 60,
    },
    Difficulty.HARD: {
        "mole_timeout": 1.0,
        "min_delay": 0.1,
        "max_delay": 0.5,
        "game_duration": 45,
    },
}


@dataclass
class GameState:
    """Thread-safe game state management."""

    score: int = 0
    misses: int = 0
    active_mole: Optional[int] = None
    mole_spawn_time: float = 0.0
    game_running: bool = False
    game_start_time: float = 0.0
    difficulty: Difficulty = Difficulty.MEDIUM
    max_holes: int = 6
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def settings(self) -> dict:
        """Get current difficulty settings."""
        return DIFFICULTY_SETTINGS[self.difficulty]

    @property
    def game_duration(self) -> int:
        """Get game duration based on difficulty."""
        return self.settings["game_duration"]

    @property
    def mole_timeout(self) -> float:
        """Get mole timeout based on difficulty."""
        return self.settings["mole_timeout"]

    @property
    def min_delay(self) -> float:
        """Get minimum delay between moles."""
        return self.settings["min_delay"]

    @property
    def max_delay(self) -> float:
        """Get maximum delay between moles."""
        return self.settings["max_delay"]

    def reset(self, difficulty: Optional[Difficulty] = None) -> None:
        """Reset game state for a new game."""
        with self.lock:
            self.score = 0
            self.misses = 0
            self.active_mole = None
            self.mole_spawn_time = 0.0
            self.game_running = False
            self.game_start_time = 0.0
            if difficulty:
                self.difficulty = difficulty


# Global game state per session
game_states: dict[str, GameState] = {}

# Global high scores
# List of dicts: {'name': str, 'score': int, 'difficulty': str, 'date': str}
high_scores: list[dict] = []


class MoleSpawnerThread(threading.Thread):
    """
    Background thread that spawns moles at random intervals.
    This demonstrates multi-threaded backend architecture.
    """

    def __init__(self, session_id: str, socketio_instance: SocketIO):
        super().__init__(daemon=True)
        self.session_id = session_id
        self.socketio = socketio_instance
        self.stop_event = threading.Event()

    def run(self):
        """Main loop for spawning moles."""
        game_state = game_states.get(self.session_id)
        if not game_state:
            return

        while not self.stop_event.is_set() and game_state.game_running:
            # Check if game time is up
            elapsed = time.time() - game_state.game_start_time
            if elapsed >= game_state.game_duration:
                self._end_game(game_state)
                break

            # Spawn a new mole
            self._spawn_mole(game_state)

            # Wait for mole timeout based on difficulty
            mole_timeout = game_state.mole_timeout
            mole_wait_start = time.time()
            while time.time() - mole_wait_start < mole_timeout:
                if self.stop_event.is_set() or not game_state.game_running:
                    return
                time.sleep(0.05)  # Check every 50ms

            # If mole wasn't whacked, count as miss
            with game_state.lock:
                if game_state.active_mole is not None:
                    game_state.misses += 1
                    old_mole = game_state.active_mole
                    game_state.active_mole = None
                    self._emit_mole_missed(old_mole, game_state)

            # Random delay before next mole based on difficulty
            delay = random.uniform(game_state.min_delay, game_state.max_delay)
            delay_start = time.time()
            while time.time() - delay_start < delay:
                if self.stop_event.is_set() or not game_state.game_running:
                    return
                time.sleep(0.05)

    def _spawn_mole(self, game_state: GameState):
        """Spawn a mole in a random hole."""
        with game_state.lock:
            hole = random.randint(1, game_state.max_holes)
            game_state.active_mole = hole
            game_state.mole_spawn_time = time.time()

        elapsed = time.time() - game_state.game_start_time
        remaining = max(0, game_state.game_duration - elapsed)

        self.socketio.emit(
            "mole_spawn",
            {
                "hole": hole,
                "timeout": game_state.mole_timeout,
                "time_remaining": remaining,
            },
            to=self.session_id,
        )

    def _emit_mole_missed(self, hole: int, game_state: GameState):
        """Emit event when mole was missed."""
        elapsed = time.time() - game_state.game_start_time
        remaining = max(0, game_state.game_duration - elapsed)

        self.socketio.emit(
            "mole_missed",
            {
                "hole": hole,
                "score": game_state.score,
                "misses": game_state.misses,
                "time_remaining": remaining,
            },
            to=self.session_id,
        )

    def _end_game(self, game_state: GameState):
        """End the game and emit final results."""
        with game_state.lock:
            game_state.game_running = False
            game_state.active_mole = None

        self.socketio.emit(
            "game_over",
            {
                "score": game_state.score,
                "misses": game_state.misses,
                "total_attempts": game_state.score + game_state.misses,
            },
            to=self.session_id,
        )

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()


class GameTimerThread(threading.Thread):
    """
    Background thread that sends periodic time updates.
    Another example of multi-threaded backend.
    """

    def __init__(self, session_id: str, socketio_instance: SocketIO):
        super().__init__(daemon=True)
        self.session_id = session_id
        self.socketio = socketio_instance
        self.stop_event = threading.Event()

    def run(self):
        """Send time updates every second."""
        game_state = game_states.get(self.session_id)
        if not game_state:
            return

        while not self.stop_event.is_set() and game_state.game_running:
            elapsed = time.time() - game_state.game_start_time
            remaining = max(0, game_state.game_duration - elapsed)

            self.socketio.emit(
                "time_update",
                {"time_remaining": remaining, "elapsed": elapsed},
                to=self.session_id,
            )

            if remaining <= 0:
                break

            # Wait 1 second
            for _ in range(10):
                if self.stop_event.is_set():
                    return
                time.sleep(0.1)

    def stop(self):
        """Signal the thread to stop."""
        self.stop_event.set()


# Store active threads per session
active_threads: dict[str, dict] = {}


@app.route("/")
def index():
    """Serve the main game page."""
    return render_template("index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


@socketio.on("connect")
def handle_connect():
    """Handle new WebSocket connection."""
    session_id = request.sid
    game_states[session_id] = GameState()
    print(f"[Thread-{threading.current_thread().name}] Client connected: {session_id}")
    emit("connected", {"session_id": session_id})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    session_id = request.sid

    # Stop any active game threads
    if session_id in active_threads:
        for thread in active_threads[session_id].values():
            thread.stop()
        del active_threads[session_id]

    if session_id in game_states:
        del game_states[session_id]

    print(f"[Thread-{threading.current_thread().name}] Client disconnected: {session_id}")


@socketio.on("start_game")
def handle_start_game(data=None):
    """
    Start a new game with specified difficulty.

    This WebSocket event handler initializes a new game session. It stops any existing
    game threads, resets the game state, and spawns new background threads
    (MoleSpawnerThread and GameTimerThread) to manage the game loop. The difficulty
    level determines game parameters like mole timeout, spawn delays, and game
    duration.

    Args:
        data (dict, optional): Dictionary containing game initialization data.
            Expected keys:
                - difficulty (str): Difficulty level ('easy', 'medium', or 'hard').
                                   Defaults to 'medium' if not provided or invalid.

    Emits:
        game_started (dict): Confirmation that the game has started.
            - duration (int): Total game duration in seconds
            - difficulty (str): Selected difficulty level
            - mole_timeout (float): Time window to whack each mole (seconds)
            - message (str): Informational message about the game start

    Side Effects:
        - Stops and cleans up any existing game threads for this session
        - Resets the GameState for this session
        - Creates and starts two daemon threads:
            * MoleSpawnerThread: Spawns moles at random intervals
            * GameTimerThread: Broadcasts time updates every second
        - Joins the session-specific room for targeted WebSocket emits

    Thread Safety:
        Creates new background threads that will safely interact with shared
        game state using the GameState.lock mutex.

    Examples:
        Client sends: {"difficulty": "hard"}
        Server emits: {
            "duration": 45,
            "difficulty": "hard",
            "mole_timeout": 1.0,
            "message": "Game started on HARD mode!"
        }
    """
    session_id = request.sid

    # Parse difficulty from request
    difficulty_str = (data or {}).get("difficulty", "medium")
    try:
        difficulty = Difficulty(difficulty_str)
    except ValueError:
        difficulty = Difficulty.MEDIUM

    # Stop existing threads if any
    if session_id in active_threads:
        for thread in active_threads[session_id].values():
            thread.stop()

    # Reset game state with chosen difficulty
    game_state = game_states.get(session_id)
    if not game_state:
        game_state = GameState()
        game_states[session_id] = game_state

    game_state.reset(difficulty=difficulty)
    game_state.game_running = True
    game_state.game_start_time = time.time()

    # Join the session room for targeted emits
    join_room(session_id)

    # Create and start game threads
    mole_thread = MoleSpawnerThread(session_id, socketio)
    timer_thread = GameTimerThread(session_id, socketio)

    active_threads[session_id] = {"mole": mole_thread, "timer": timer_thread}

    mole_thread.start()
    timer_thread.start()

    print(
        f"[Thread-{threading.current_thread().name}] Game started for: {session_id} "
        f"on {difficulty.value.upper()} difficulty"
    )

    emit(
        "game_started",
        {
            "duration": game_state.game_duration,
            "difficulty": difficulty.value,
            "mole_timeout": game_state.mole_timeout,
            "message": f"Game started on {difficulty.value.upper()} mode!",
        },
    )


def _process_whack_attempt(game_state: GameState, hole: int, current_time: float) -> dict:
    """
    Process a whack attempt and return the result data.

    Args:
        game_state: The current game state
        hole: The hole number that was clicked
        current_time: The current timestamp

    Returns:
        dict: Result data containing success status, scores, and timing info
    """
    with game_state.lock:
        if game_state.active_mole == hole:
            # Successful whack!
            game_state.score += 1
            reaction_time = current_time - game_state.mole_spawn_time
            game_state.active_mole = None
            elapsed = current_time - game_state.game_start_time
            remaining = max(0, game_state.game_duration - elapsed)

            # Capture values before releasing lock
            score = game_state.score
            misses = game_state.misses

            return {
                "success": True,
                "hole": hole,
                "score": score,
                "misses": misses,
                "reaction_time": reaction_time,
                "time_remaining": remaining,
            }
        else:
            # Missed - wrong hole or no mole
            active_mole = game_state.active_mole
            score = game_state.score
            misses = game_state.misses

            return {
                "success": False,
                "hole": hole,
                "score": score,
                "misses": misses,
                "active_mole": active_mole,
            }


@socketio.on("whack")
def handle_whack(data):
    """
    Handle a whack attempt from the player.

    This WebSocket event handler processes player clicks on mole holes. It validates
    the attempt, checks if the player hit an active mole, updates the score/misses,
    and emits the result back to the client.

    Args:
        data (dict): Dictionary containing the whack attempt data.
            Expected keys:
                - hole (int): The hole number (1-6) that was clicked.

    Emits:
        whack_result (dict): Result of the whack attempt.
            On success:
                - success (bool): True
                - hole (int): The hole that was whacked
                - score (int): Updated player score
                - misses (int): Current miss count
                - reaction_time (float): Time taken to whack the mole (seconds)
                - time_remaining (float): Remaining game time (seconds)
            On failure:
                - success (bool): False
                - hole (int): The hole that was clicked
                - active_mole (int|None): The actual active mole hole (if any)
                - score (int): Current player score
                - misses (int): Current miss count
                - error (str): Error message (if validation failed)

    Thread Safety:
        Uses game_state.lock to ensure thread-safe access to shared game state,
        preventing race conditions with the MoleSpawnerThread.

    Validation:
        - Checks if hole number is valid (1 to max_holes)
        - Verifies game state exists
        - Confirms game is currently running
    """
    session_id = request.sid
    thread_name = threading.current_thread().name

    hole = data.get("hole")
    game_state = game_states.get(session_id)
    if not game_state:
        emit("whack_result", {"success": False, "error": "Game not found"})
        return

    if not isinstance(hole, int) or hole < 1 or hole > game_state.max_holes:
        emit("whack_result", {"success": False, "error": "Invalid hole number"})
        return

    if not game_state.game_running:
        emit("whack_result", {"success": False, "error": "Game not running"})
        return

    # Process the whack attempt
    current_time = time.time()
    result = _process_whack_attempt(game_state, hole, current_time)

    # Log the result
    if result["success"]:
        print(
            f"[Thread-{thread_name}] Whack success!"
            f" Hole {hole}, Time: {result['reaction_time']:.3f}s"
        )
    else:
        print(
            f"[Thread-{thread_name}] Whack miss! "
            f"Hole {hole}, Active: {result['active_mole']}"
        )

    emit("whack_result", result)


@socketio.on("stop_game")
def handle_stop_game():
    """Stop the current game."""
    session_id = request.sid

    game_state = game_states.get(session_id)
    if game_state:
        game_state.game_running = False

    if session_id in active_threads:
        for thread in active_threads[session_id].values():
            thread.stop()
        del active_threads[session_id]

    if game_state:
        emit("game_stopped", {"score": game_state.score, "misses": game_state.misses})


@socketio.on("get_high_scores")
def handle_get_high_scores():
    """Send current high scores to the client."""
    emit("high_scores_update", high_scores)


@socketio.on("submit_score")
def handle_submit_score(data):
    """Handle high score submission."""
    name = data.get("name", "Anonymous")
    score = data.get("score", 0)
    difficulty = data.get("difficulty", "medium")

    # Add new score
    new_entry = {
        "name": name[:10],  # Limit name length
        "score": score,
        "difficulty": difficulty,
        "date": time.strftime("%Y-%m-%d"),
    }
    high_scores.append(new_entry)

    # Sort by score (descending) and keep top 10
    high_scores.sort(key=lambda x: x["score"], reverse=True)
    del high_scores[10:]

    # Broadcast updated scores to all clients
    emit("high_scores_update", high_scores, broadcast=True)


if __name__ == "__main__":
    print("=" * 50)
    print("Whack-a-Mole Game Server")
    print("Multi-threaded backend with WebSocket support")
    print("=" * 50)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)

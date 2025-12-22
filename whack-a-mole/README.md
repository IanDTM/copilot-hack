# 🔨 Whack-a-Mole Game 🐹

A multi-threaded web application featuring a classic Whack-a-Mole game with both a multi-threaded backend (Python/Flask) and multi-threaded frontend (Web Workers).

## Features

- **6 Randomly Positioned Mole Holes**: Each game session arranges the holes at random non-overlapping positions
- **Keyboard Controls**: Use number keys 1-6 to whack moles
- **1.5 Second Timer**: You have 1.5 seconds to whack each mole before it disappears
- **60 Second Game Duration**: Try to score as many points as possible in 60 seconds
- **Real-time WebSocket Communication**: Instant response between frontend and backend
- **Multi-threaded Architecture**: Both frontend and backend use threading for responsive gameplay

## Architecture

### Backend (Multi-threaded Python/Flask)

- **Flask-SocketIO**: Real-time bidirectional communication
- **MoleSpawnerThread**: Background thread that spawns moles at random intervals
- **GameTimerThread**: Background thread that manages game duration and sends time updates
- **Thread-safe GameState**: Proper locking for concurrent access to game state

### Frontend (Multi-threaded JavaScript)

- **Web Worker (gameWorker.js)**: Handles timing operations off the main thread
  - Mole visibility countdown
  - Smooth progress updates
  - Game timer management
- **Main Thread (game.js)**: Handles UI, WebSocket communication, and user input

## Project Structure

```
whack-a-mole/
├── backend/
│   └── app.py              # Flask server with threading
├── frontend/
│   ├── templates/
│   │   └── index.html      # Main game page
│   └── static/
│       ├── css/
│       │   └── style.css   # Game styles
│       └── js/
│           ├── game.js     # Main game logic
│           └── gameWorker.js # Web Worker for timing
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Install Python dependencies** (using UV):
   ```bash
   cd whack-a-mole
   uv sync
   ```

2. **Run the server**:
   ```bash
   uv run python backend/app.py
   ```

3. **Open your browser**:
   Navigate to `http://localhost:5000`

## How to Play

1. Click **Start Game** or wait for the game to begin
2. Watch for moles to pop up in any of the 6 holes
3. Press the corresponding number key (1-6) to whack the mole
4. You have **1.5 seconds** to hit each mole
5. Score as many points as possible in **60 seconds**
6. Your final score and accuracy are displayed at the end

## Controls

| Key | Action |
|-----|--------|
| 1-6 | Whack mole in corresponding hole |
| Click | Also works for whacking moles |

## Technical Details

### Threading Model

**Backend Threads:**
1. Main Flask thread (handles HTTP/WebSocket requests)
2. MoleSpawnerThread (one per active game session)
3. GameTimerThread (one per active game session)

**Frontend Threads:**
1. Main UI thread (React to user input, update DOM)
2. Web Worker thread (timing calculations, progress updates)

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `start_game` | Client → Server | Start a new game |
| `stop_game` | Client → Server | Stop current game |
| `whack` | Client → Server | Attempt to whack a mole |
| `game_started` | Server → Client | Game has started |
| `mole_spawn` | Server → Client | A mole appeared |
| `mole_missed` | Server → Client | Player missed a mole |
| `whack_result` | Server → Client | Result of whack attempt |
| `time_update` | Server → Client | Timer update |
| `game_over` | Server → Client | Game ended |

## License

MIT License - Feel free to modify and use for your own projects!

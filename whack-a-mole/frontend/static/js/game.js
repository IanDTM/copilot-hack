/**
 * Whack-a-Mole Game - Main JavaScript
 * Handles game initialization, UI updates, WebSocket communication,
 * and coordination with the Web Worker for multi-threaded timing.
 */

class WhackAMoleGame {
    constructor() {
        // DOM Elements
        this.gameArea = document.getElementById('game-area');
        this.scoreElement = document.getElementById('score');
        this.missesElement = document.getElementById('misses');
        this.timerElement = document.getElementById('timer');
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.gameStatus = document.getElementById('game-status');
        this.gameOverModal = document.getElementById('game-over-modal');
        this.finalScoreElement = document.getElementById('final-score');
        this.finalMissesElement = document.getElementById('final-misses');
        this.accuracyElement = document.getElementById('accuracy');
        this.playAgainBtn = document.getElementById('play-again-btn');
        this.difficultySelector = document.getElementById('difficulty-selector');
        this.difficultyDisplay = document.getElementById('difficulty-display');
        this.currentDifficultyElement = document.getElementById('current-difficulty');
        this.finalDifficultyElement = document.getElementById('final-difficulty');
        this.sessionIdElement = document.getElementById('session-id');

        // High Score Elements
        this.submitScoreBtn = document.getElementById('submit-score-btn');
        this.playerNameInput = document.getElementById('player-name');
        this.highScoreList = document.getElementById('high-score-list');

        // Game State
        this.holes = [];
        this.activeMole = null;
        this.score = 0;
        this.misses = 0;
        this.isGameRunning = false;
        this.socket = null;
        this.worker = null;
        this.selectedDifficulty = 'medium';
        this.currentMoleTimeout = 1.5;

        // Initialize
        this.init();
    }

    /**
     * Initialize the game
     */
    init() {
        this.createHoles();
        this.initWorker();
        this.initSocket();
        this.bindEvents();
        this.addConnectionStatus();
    }

    /**
     * Create 6 mole holes at random non-overlapping positions
     */
    createHoles() {
        const positions = this.generateRandomPositions(6);

        for (let i = 0; i < 6; i++) {
            const hole = this.createHoleElement(i + 1, positions[i]);
            this.gameArea.appendChild(hole);
            this.holes.push(hole);
        }
    }

    /**
     * Generate random non-overlapping positions for holes
     */
    generateRandomPositions(count) {
        const positions = [];
        const minDistance = 140; // Minimum distance between hole centers
        const padding = 80; // Padding from edges

        const areaRect = this.gameArea.getBoundingClientRect();
        const width = areaRect.width || 800;
        const height = areaRect.height || 500;

        const maxAttempts = 1000;

        for (let i = 0; i < count; i++) {
            let attempts = 0;
            let position;

            do {
                position = {
                    x: padding + Math.random() * (width - 2 * padding),
                    y: padding + Math.random() * (height - 2 * padding)
                };
                attempts++;
            } while (
                !this.isPositionValid(position, positions, minDistance) &&
                attempts < maxAttempts
            );

            // Fallback to grid layout if random fails
            if (attempts >= maxAttempts) {
                const cols = 3;
                const rows = 2;
                const col = i % cols;
                const row = Math.floor(i / cols);

                position = {
                    x: (width / (cols + 1)) * (col + 1),
                    y: (height / (rows + 1)) * (row + 1)
                };
            }

            positions.push(position);
        }

        return positions;
    }

    /**
     * Check if a position is valid (doesn't overlap with existing positions)
     */
    isPositionValid(newPos, existingPositions, minDistance) {
        for (const pos of existingPositions) {
            const dx = newPos.x - pos.x;
            const dy = newPos.y - pos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < minDistance) {
                return false;
            }
        }
        return true;
    }

    /**
     * Create a single mole hole element
     */
    createHoleElement(number, position) {
        const hole = document.createElement('div');
        hole.className = 'mole-hole';
        hole.dataset.hole = number;
        hole.style.left = `${position.x}px`;
        hole.style.top = `${position.y}px`;

        hole.innerHTML = `
            <div class="hole-container">
                <div class="hole-label">${number}</div>
                <div class="mole" id="mole-${number}">
                    <div class="mole-body">
                        <div class="mole-face">
                            <div class="mole-eyes">
                                <div class="mole-eye"></div>
                                <div class="mole-eye"></div>
                            </div>
                            <div class="mole-nose"></div>
                        </div>
                    </div>
                </div>
                <div class="hole"></div>
            </div>
        `;

        // Click handler for mobile/mouse
        hole.addEventListener('click', () => {
            if (this.isGameRunning) {
                this.whackMole(number);
            }
        });

        return hole;
    }

    /**
     * Initialize the Web Worker for multi-threaded timing
     */
    initWorker() {
        try {
            this.worker = new Worker('/static/js/gameWorker.js');

            this.worker.onmessage = (event) => {
                this.handleWorkerMessage(event.data);
            };

            this.worker.onerror = (error) => {
                console.error('Worker error:', error);
                this.updateStatus('Worker error - falling back to main thread', 'error');
            };
        } catch (error) {
            console.warn('Web Workers not supported, using fallback timing');
        }
    }

    /**
     * Handle messages from the Web Worker
     */
    handleWorkerMessage(message) {
        const { type, data } = message;

        switch (type) {
            case 'WORKER_READY':
                console.log('Game worker ready');
                break;

            case 'MOLE_TIMER_UPDATE':
                this.updateMoleProgress(data);
                break;

            case 'MOLE_TIMEOUT':
                // Worker-side timeout (backup for server timeout)
                break;

            case 'GAME_TIMER_UPDATE':
                // Worker can provide additional timer updates
                if (data.isEnding) {
                    this.timerElement.classList.add('timer-warning');
                }
                break;

            case 'MOLE_WHACK_CONFIRMED':
                console.log('Worker confirmed whack on hole', data.hole);
                break;

            case 'ALL_STOPPED':
                console.log('All worker timers stopped');
                break;
        }
    }

    /**
     * Update visual progress for active mole (e.g., urgency indicator)
     */
    updateMoleProgress(data) {
        const { hole, isExpiring } = data;
        const moleElement = document.getElementById(`mole-${hole}`);

        if (moleElement && isExpiring) {
            moleElement.style.filter = 'brightness(1.2) saturate(1.3)';
        }
    }

    /**
     * Initialize WebSocket connection to backend
     */
    initSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = `${window.location.protocol}//${window.location.host}`;

        this.socket = io(socketUrl, {
            transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
            console.log('Connected to game server');
            this.updateConnectionStatus(true);
            this.updateStatus('Connected to server. Ready to play!');
            this.socket.emit('get_high_scores');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from game server');
            this.updateConnectionStatus(false);
            this.updateStatus('Disconnected from server', 'error');
            this.stopGame();
        });

        this.socket.on('connected', (data) => {
            console.log('Session ID:', data.session_id);
            this.sessionId = data.session_id;
            if (this.sessionIdElement) {
                this.sessionIdElement.textContent = data.session_id;
            }
        });

        this.socket.on('game_started', (data) => {
            console.log('Game started:', data.message);
            this.updateStatus(data.message);
            this.currentMoleTimeout = data.mole_timeout;

            // Update difficulty display
            this.updateDifficultyDisplay(data.difficulty);

            // Start worker game timer
            if (this.worker) {
                this.worker.postMessage({
                    type: 'START_GAME_TIMER',
                    data: { duration: data.duration }
                });
            }
        });

        this.socket.on('mole_spawn', (data) => {
            this.showMole(data.hole, data.timeout);
            this.updateTimer(data.time_remaining);
        });

        this.socket.on('mole_missed', (data) => {
            this.hideMole(data.hole, false);
            this.misses = data.misses;
            this.updateUI();
            this.updateTimer(data.time_remaining);
        });

        this.socket.on('whack_result', (data) => {
            if (data.success) {
                this.onWhackSuccess(data);
            } else {
                this.onWhackFail(data);
            }
        });

        this.socket.on('time_update', (data) => {
            this.updateTimer(data.time_remaining);
        });

        this.socket.on('game_over', (data) => {
            this.onGameOver(data);
        });

        this.socket.on('game_stopped', (data) => {
            this.updateStatus('Game stopped');
            this.isGameRunning = false;
            this.updateButtonStates();
            this.showDifficultySelector();
        });

        this.socket.on('high_scores_update', (data) => {
            this.updateHighScores(data);
        });
    }

    /**
     * Bind UI events
     */
    bindEvents() {
        // Start button
        this.startBtn.addEventListener('click', () => {
            this.startGame();
        });

        // Stop button
        this.stopBtn.addEventListener('click', () => {
            this.stopGame();
        });

        // Play again button
        this.playAgainBtn.addEventListener('click', () => {
            this.gameOverModal.classList.add('hidden');
            this.startGame();
        });

        // Difficulty selection
        document.querySelectorAll('.diff-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (this.isGameRunning) return; // Don't change during game

                document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedDifficulty = btn.dataset.difficulty;
                this.updateStatus(`Difficulty set to ${this.selectedDifficulty.toUpperCase()}`);
            });
        });

        // Keyboard events (1-6 to whack)
        document.addEventListener('keydown', (event) => {
            if (!this.isGameRunning) return;

            const key = event.key;
            if (key >= '1' && key <= '6') {
                const holeNumber = parseInt(key);
                this.whackMole(holeNumber);
            }
        });

        // Handle window resize - reposition holes
        window.addEventListener('resize', () => {
            this.repositionHoles();
        });

        // Submit Score Button
        if (this.submitScoreBtn) {
            this.submitScoreBtn.addEventListener('click', () => {
                this.submitScore();
            });
        }
    }

    /**
     * Add connection status indicator
     */
    addConnectionStatus() {
        const status = document.createElement('div');
        status.id = 'connection-status';
        status.className = 'connection-status disconnected';
        status.textContent = 'Disconnected';
        document.body.appendChild(status);
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        if (status) {
            status.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            status.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    /**
     * Update difficulty display during game
     */
    updateDifficultyDisplay(difficulty) {
        const difficultyNames = {
            'easy': 'EASY 🐢',
            'medium': 'MEDIUM 🐇',
            'hard': 'HARD 🦅'
        };

        if (this.currentDifficultyElement) {
            this.currentDifficultyElement.textContent = difficultyNames[difficulty] || difficulty.toUpperCase();
        }

        if (this.difficultyDisplay) {
            this.difficultyDisplay.classList.remove('hidden');
        }

        if (this.difficultySelector) {
            this.difficultySelector.classList.add('hidden');
        }
    }

    /**
     * Show difficulty selector (when game ends or stops)
     */
    showDifficultySelector() {
        if (this.difficultySelector) {
            this.difficultySelector.classList.remove('hidden');
        }
        if (this.difficultyDisplay) {
            this.difficultyDisplay.classList.add('hidden');
        }
    }

    /**
     * Start a new game
     */
    startGame() {
        if (!this.socket?.connected) {
            this.updateStatus('Cannot start - not connected to server', 'error');
            return;
        }

        // Reset UI
        this.score = 0;
        this.misses = 0;
        this.updateUI();
        this.timerElement.classList.remove('timer-warning');

        // Set initial timer based on difficulty
        const durations = { easy: 60, medium: 60, hard: 45 };
        this.timerElement.textContent = durations[this.selectedDifficulty] || 60;

        this.hideAllMoles();

        // Update state
        this.isGameRunning = true;
        this.updateButtonStates();

        // Tell server to start with selected difficulty
        this.socket.emit('start_game', { difficulty: this.selectedDifficulty });
        this.updateStatus(`Starting ${this.selectedDifficulty.toUpperCase()} game...`);
    }

    /**
     * Stop the current game
     */
    stopGame() {
        this.isGameRunning = false;
        this.updateButtonStates();

        // Stop worker
        if (this.worker) {
            this.worker.postMessage({ type: 'STOP_ALL' });
        }

        // Tell server to stop
        if (this.socket?.connected) {
            this.socket.emit('stop_game');
        }

        this.hideAllMoles();
        this.showDifficultySelector();
    }

    /**
     * Show a mole in the specified hole
     */
    showMole(holeNumber, timeout) {
        // Hide any currently active mole
        if (this.activeMole && this.activeMole !== holeNumber) {
            this.hideMole(this.activeMole, false);
        }

        this.activeMole = holeNumber;
        const moleElement = document.getElementById(`mole-${holeNumber}`);

        if (moleElement) {
            moleElement.classList.remove('whacked', 'missed');
            moleElement.style.filter = '';
            moleElement.classList.add('active');

            // Start worker timer
            if (this.worker) {
                this.worker.postMessage({
                    type: 'START_MOLE_TIMER',
                    data: {
                        hole: holeNumber,
                        timeout: timeout,
                        startTime: Date.now()
                    }
                });
            }
        }
    }

    /**
     * Hide a mole from the specified hole
     */
    hideMole(holeNumber, wasWhacked) {
        const moleElement = document.getElementById(`mole-${holeNumber}`);

        if (moleElement) {
            moleElement.classList.remove('active');
            moleElement.style.filter = '';

            if (wasWhacked) {
                moleElement.classList.add('whacked');
                this.showHitEffect(holeNumber, '💥');
            } else {
                moleElement.classList.add('missed');
            }

            // Clear animation classes after animation completes
            setTimeout(() => {
                moleElement.classList.remove('whacked', 'missed');
            }, 300);
        }

        if (this.activeMole === holeNumber) {
            this.activeMole = null;
        }

        // Cancel worker timer
        if (this.worker) {
            this.worker.postMessage({ type: 'CANCEL_MOLE_TIMER' });
        }
    }

    /**
     * Hide all moles
     */
    hideAllMoles() {
        for (let i = 1; i <= 6; i++) {
            const moleElement = document.getElementById(`mole-${i}`);
            if (moleElement) {
                moleElement.classList.remove('active', 'whacked', 'missed');
                moleElement.style.filter = '';
            }
        }
        this.activeMole = null;
    }

    /**
     * Show hit effect animation
     */
    showHitEffect(holeNumber, emoji) {
        const hole = this.holes[holeNumber - 1];
        if (!hole) return;

        const effect = document.createElement('div');
        effect.className = 'hit-effect';
        effect.textContent = emoji;
        hole.appendChild(effect);

        setTimeout(() => {
            effect.remove();
        }, 500);
    }

    /**
     * Attempt to whack a mole
     */
    whackMole(holeNumber) {
        if (!this.isGameRunning) return;

        // Add visual feedback for the attempt
        const hole = this.holes[holeNumber - 1];
        if (hole) {
            hole.style.transform = 'translate(-50%, -50%) scale(0.95)';
            setTimeout(() => {
                hole.style.transform = '';
            }, 100);
        }

        // Send to server
        this.socket.emit('whack', { hole: holeNumber });

        // Notify worker
        if (this.worker) {
            this.worker.postMessage({
                type: 'MOLE_WHACKED',
                data: { hole: holeNumber }
            });
        }
    }

    /**
     * Handle successful whack
     */
    onWhackSuccess(data) {
        this.hideMole(data.hole, true);
        this.score = data.score;
        this.misses = data.misses;
        this.updateUI();
        this.updateTimer(data.time_remaining);

        const reactionTime = (data.reaction_time * 1000).toFixed(0);
        this.updateStatus(`Nice! ${reactionTime}ms reaction time! 🎯`);
    }

    /**
     * Handle failed whack
     */
    onWhackFail(data) {
        // Show miss effect on the wrong hole
        this.showHitEffect(data.hole, '❌');
        this.updateStatus('Missed! Wrong hole or no mole there.');
    }

    /**
     * Handle game over
     */
    onGameOver(data) {
        this.isGameRunning = false;
        this.updateButtonStates();

        // Stop worker
        if (this.worker) {
            this.worker.postMessage({ type: 'STOP_ALL' });
        }

        this.hideAllMoles();
        this.showDifficultySelector();

        // Calculate accuracy
        const total = data.score + data.misses;
        const accuracy = total > 0 ? Math.round((data.score / total) * 100) : 0;

        // Update modal
        this.finalScoreElement.textContent = data.score;
        this.finalMissesElement.textContent = data.misses;
        this.accuracyElement.textContent = accuracy;

        // Show difficulty in results
        if (this.finalDifficultyElement) {
            this.finalDifficultyElement.textContent = this.selectedDifficulty.toUpperCase();
        }

        // Show modal
        this.gameOverModal.classList.remove('hidden');

        // Reset submit button state
        if (this.submitScoreBtn) {
            this.submitScoreBtn.disabled = false;
            this.submitScoreBtn.textContent = 'Submit Score';
        }
    }

    /**
     * Update score and misses display
     */
    updateUI() {
        this.scoreElement.textContent = this.score;
        this.missesElement.textContent = this.misses;
    }

    /**
     * Update timer display
     */
    updateTimer(seconds) {
        const rounded = Math.ceil(seconds);
        this.timerElement.textContent = rounded;

        if (rounded <= 10) {
            this.timerElement.classList.add('timer-warning');
        } else {
            this.timerElement.classList.remove('timer-warning');
        }
    }

    /**
     * Update button enabled/disabled states
     */
    updateButtonStates() {
        this.startBtn.disabled = this.isGameRunning;
        this.stopBtn.disabled = !this.isGameRunning;
    }

    /**
     * Update game status message
     */
    updateStatus(message, type = 'info') {
        this.gameStatus.textContent = message;
        this.gameStatus.style.color = type === 'error' ? '#f87171' : '#4ade80';
    }

    /**
     * Submit high score
     */
    submitScore() {
        const name = this.playerNameInput.value.trim();
        if (!name) {
            alert('Please enter your name!');
            return;
        }

        if (this.socket?.connected) {
            this.socket.emit('submit_score', {
                name: name,
                score: parseInt(this.finalScoreElement.textContent) || 0
            });

            // Disable button to prevent double submission
            this.submitScoreBtn.disabled = true;
            this.submitScoreBtn.textContent = 'Submitted!';

            setTimeout(() => {
                this.gameOverModal.classList.add('hidden');
                this.submitScoreBtn.disabled = false;
                this.submitScoreBtn.textContent = 'Submit Score';
                this.playerNameInput.value = '';
            }, 1000);
        }
    }

    /**
     * Update high score list in sidebar
     */
    updateHighScores(scores) {
        if (!this.highScoreList) return;

        this.highScoreList.innerHTML = '';

        if (scores.length === 0) {
            this.highScoreList.innerHTML = '<li style="text-align:center; color:#94a3b8; padding:20px;">No scores yet!</li>';
            return;
        }

        scores.forEach((score, index) => {
            const li = document.createElement('li');
            li.className = `high-score-item rank-${index + 1}`;

            const rank = index + 1;
            let rankDisplay = rank;
            if (rank === 1) rankDisplay = '🥇';
            if (rank === 2) rankDisplay = '🥈';
            if (rank === 3) rankDisplay = '🥉';

            li.innerHTML = `
                <span class="score-rank">${rankDisplay}</span>
                <span class="score-name">${this.escapeHtml(score.name)}</span>
                <span class="score-val">${score.score}</span>
            `;

            this.highScoreList.appendChild(li);
        });
    }

    /**
     * Helper to escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Reposition holes on window resize
     */
    repositionHoles() {
        const positions = this.generateRandomPositions(6);

        this.holes.forEach((hole, index) => {
            hole.style.left = `${positions[index].x}px`;
            hole.style.top = `${positions[index].y}px`;
        });
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Whack-a-Mole game...');
    window.game = new WhackAMoleGame();
});

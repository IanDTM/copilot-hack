/**
 * Whack-a-Mole Game Worker
 * Multi-threaded frontend component for handling game timing and animations.
 * 
 * This Web Worker handles:
 * - Countdown timers for mole visibility
 * - Background timing without blocking the main thread
 * - Periodic state updates
 */

// Worker state
let activeMoleTimer = null;
let moleTimeoutId = null;
let gameTimerId = null;
let isRunning = false;

/**
 * Handle messages from the main thread
 */
self.onmessage = function (event) {
    const { type, data } = event.data;

    switch (type) {
        case 'START_MOLE_TIMER':
            startMoleTimer(data);
            break;

        case 'CANCEL_MOLE_TIMER':
            cancelMoleTimer();
            break;

        case 'START_GAME_TIMER':
            startGameTimer(data);
            break;

        case 'STOP_GAME_TIMER':
            stopGameTimer();
            break;

        case 'MOLE_WHACKED':
            handleMoleWhacked(data);
            break;

        case 'STOP_ALL':
            stopAll();
            break;

        default:
            console.warn('Unknown message type:', type);
    }
};

/**
 * Start a timer for the active mole
 * Sends progress updates and notifies when time is up
 */
function startMoleTimer(data) {
    const { hole, timeout, startTime } = data;
    const timeoutMs = timeout * 1000;
    const updateInterval = 50; // Update every 50ms for smooth progress

    // Cancel any existing timer
    cancelMoleTimer();

    isRunning = true;
    let elapsed = 0;

    // Send periodic progress updates
    activeMoleTimer = setInterval(() => {
        if (!isRunning) {
            cancelMoleTimer();
            return;
        }

        elapsed += updateInterval;
        const progress = Math.min(elapsed / timeoutMs, 1);
        const remaining = Math.max(timeoutMs - elapsed, 0);

        self.postMessage({
            type: 'MOLE_TIMER_UPDATE',
            data: {
                hole,
                progress,
                remaining: remaining / 1000,
                isExpiring: remaining < 500 // Last 500ms
            }
        });
    }, updateInterval);

    // Set timeout for when mole should hide
    moleTimeoutId = setTimeout(() => {
        cancelMoleTimer();
        self.postMessage({
            type: 'MOLE_TIMEOUT',
            data: {
                hole,
                message: 'Mole escaped!'
            }
        });
    }, timeoutMs);
}

/**
 * Cancel the active mole timer
 */
function cancelMoleTimer() {
    if (activeMoleTimer) {
        clearInterval(activeMoleTimer);
        activeMoleTimer = null;
    }

    if (moleTimeoutId) {
        clearTimeout(moleTimeoutId);
        moleTimeoutId = null;
    }
}

/**
 * Start the main game timer
 */
function startGameTimer(data) {
    const { duration } = data;
    const startTime = Date.now();
    const durationMs = duration * 1000;

    // Cancel any existing game timer
    stopGameTimer();

    gameTimerId = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(durationMs - elapsed, 0);
        const remainingSeconds = Math.ceil(remaining / 1000);

        self.postMessage({
            type: 'GAME_TIMER_UPDATE',
            data: {
                remaining: remainingSeconds,
                elapsed: elapsed / 1000,
                isEnding: remainingSeconds <= 10
            }
        });

        if (remaining <= 0) {
            stopGameTimer();
            self.postMessage({
                type: 'GAME_TIME_UP',
                data: {
                    message: 'Time is up!'
                }
            });
        }
    }, 100); // Update every 100ms for smooth countdown
}

/**
 * Stop the game timer
 */
function stopGameTimer() {
    if (gameTimerId) {
        clearInterval(gameTimerId);
        gameTimerId = null;
    }
}

/**
 * Handle when a mole is successfully whacked
 */
function handleMoleWhacked(data) {
    const { hole } = data;

    // Cancel the mole timer immediately
    cancelMoleTimer();

    // Send confirmation back to main thread
    self.postMessage({
        type: 'MOLE_WHACK_CONFIRMED',
        data: {
            hole,
            timestamp: Date.now()
        }
    });
}

/**
 * Stop all timers and reset state
 */
function stopAll() {
    isRunning = false;
    cancelMoleTimer();
    stopGameTimer();

    self.postMessage({
        type: 'ALL_STOPPED',
        data: {
            message: 'All timers stopped'
        }
    });
}

// Signal that the worker is ready
self.postMessage({
    type: 'WORKER_READY',
    data: {
        message: 'Game worker initialized and ready'
    }
});

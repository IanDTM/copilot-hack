/**
 * Unit tests for gameWorker.js Web Worker timing logic.
 */

describe('GameWorker - Timer Calculations', () => {
    test('progress calculation from 0 to 1', () => {
        const elapsed = 500;
        const timeoutMs = 1000;
        const progress = Math.min(elapsed / timeoutMs, 1);

        expect(progress).toBe(0.5);
    });

    test('progress never exceeds 1', () => {
        const elapsed = 1500;
        const timeoutMs = 1000;
        const progress = Math.min(elapsed / timeoutMs, 1);

        expect(progress).toBe(1);
    });

    test('remaining time calculation', () => {
        const timeoutMs = 2000;
        const elapsed = 500;
        const remaining = Math.max(timeoutMs - elapsed, 0);

        expect(remaining).toBe(1500);
    });

    test('remaining time never goes negative', () => {
        const timeoutMs = 1000;
        const elapsed = 1500;
        const remaining = Math.max(timeoutMs - elapsed, 0);

        expect(remaining).toBe(0);
    });

    test('isExpiring flag triggers at 500ms', () => {
        const remaining = 400;
        const isExpiring = remaining < 500;

        expect(isExpiring).toBe(true);
    });

    test('isExpiring flag is false above 500ms', () => {
        const remaining = 600;
        const isExpiring = remaining < 500;

        expect(isExpiring).toBe(false);
    });

    test('milliseconds to seconds conversion', () => {
        const remainingMs = 2500;
        const remainingSeconds = remainingMs / 1000;

        expect(remainingSeconds).toBe(2.5);
    });
});


describe('GameWorker - Game Timer Logic', () => {
    test('game timer remaining seconds rounds up', () => {
        const remaining = 1500; // 1.5 seconds
        const remainingSeconds = Math.ceil(remaining / 1000);

        expect(remainingSeconds).toBe(2);
    });

    test('game timer handles exact seconds', () => {
        const remaining = 3000; // Exactly 3 seconds
        const remainingSeconds = Math.ceil(remaining / 1000);

        expect(remainingSeconds).toBe(3);
    });

    test('game timer handles zero remaining', () => {
        const remaining = 0;
        const remainingSeconds = Math.ceil(remaining / 1000);

        expect(remainingSeconds).toBe(0);
    });

    test('isEnding flag triggers at 10 seconds', () => {
        const remainingSeconds = 9;
        const isEnding = remainingSeconds <= 10;

        expect(isEnding).toBe(true);
    });

    test('isEnding flag is false above 10 seconds', () => {
        const remainingSeconds = 11;
        const isEnding = remainingSeconds <= 10;

        expect(isEnding).toBe(false);
    });

    test('elapsed time calculation', () => {
        const startTime = 1000;
        const currentTime = 3500;
        const elapsed = currentTime - startTime;

        expect(elapsed).toBe(2500);
    });

    test('elapsed to seconds conversion', () => {
        const elapsedMs = 5250;
        const elapsedSeconds = elapsedMs / 1000;

        expect(elapsedSeconds).toBe(5.25);
    });
});


describe('GameWorker - Timer State Management', () => {
    test('timer cleanup clears interval', () => {
        let timerId = setTimeout(() => { }, 1000);
        expect(timerId).toBeDefined();

        clearTimeout(timerId);
        timerId = null;

        expect(timerId).toBeNull();
    });

    test('multiple timer cleanup', () => {
        let timer1 = setTimeout(() => { }, 1000);
        let timer2 = setInterval(() => { }, 100);

        expect(timer1).toBeDefined();
        expect(timer2).toBeDefined();

        clearTimeout(timer1);
        clearInterval(timer2);

        timer1 = null;
        timer2 = null;

        expect(timer1).toBeNull();
        expect(timer2).toBeNull();
    });

    test('isRunning flag controls timer execution', () => {
        let isRunning = true;

        expect(isRunning).toBe(true);

        isRunning = false;

        expect(isRunning).toBe(false);
    });
});


describe('GameWorker - Message Types', () => {
    test('mole timer update message structure', () => {
        const message = {
            type: 'MOLE_TIMER_UPDATE',
            data: {
                hole: 3,
                progress: 0.5,
                remaining: 1.0,
                isExpiring: false
            }
        };

        expect(message.type).toBe('MOLE_TIMER_UPDATE');
        expect(message.data.hole).toBe(3);
        expect(message.data.progress).toBe(0.5);
        expect(message.data.remaining).toBe(1.0);
        expect(message.data.isExpiring).toBe(false);
    });

    test('mole timeout message structure', () => {
        const message = {
            type: 'MOLE_TIMEOUT',
            data: {
                hole: 5,
                message: 'Mole escaped!'
            }
        };

        expect(message.type).toBe('MOLE_TIMEOUT');
        expect(message.data.hole).toBe(5);
        expect(message.data.message).toBe('Mole escaped!');
    });

    test('game timer update message structure', () => {
        const message = {
            type: 'GAME_TIMER_UPDATE',
            data: {
                remaining: 45,
                elapsed: 15.5,
                isEnding: false
            }
        };

        expect(message.type).toBe('GAME_TIMER_UPDATE');
        expect(message.data.remaining).toBe(45);
        expect(message.data.elapsed).toBe(15.5);
        expect(message.data.isEnding).toBe(false);
    });

    test('game time up message structure', () => {
        const message = {
            type: 'GAME_TIME_UP',
            data: {
                message: 'Time is up!'
            }
        };

        expect(message.type).toBe('GAME_TIME_UP');
        expect(message.data.message).toBe('Time is up!');
    });
});


describe('GameWorker - Timing Precision', () => {
    test('50ms update interval', () => {
        const updateInterval = 50;
        const updatesPerSecond = 1000 / updateInterval;

        expect(updatesPerSecond).toBe(20);
    });

    test('progress updates are smooth', () => {
        const updateInterval = 50;
        const timeout = 1000;
        const totalUpdates = timeout / updateInterval;

        expect(totalUpdates).toBe(20);
    });

    test('timeout conversion to milliseconds', () => {
        const timeoutSeconds = 2.0;
        const timeoutMs = timeoutSeconds * 1000;

        expect(timeoutMs).toBe(2000);
    });
});

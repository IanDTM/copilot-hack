/**
 * Jest setup file for frontend tests.
 * Runs before each test file.
 */

// Mock Socket.IO client
global.io = jest.fn(() => ({
    on: jest.fn(),
    emit: jest.fn(),
    off: jest.fn(),
    disconnect: jest.fn(),
    connected: false
}));

// Mock Web Worker
class MockWorker {
    constructor() {
        this.onmessage = null;
        this.postMessage = jest.fn();
        this.terminate = jest.fn();
    }
}
global.Worker = MockWorker;

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
};

// Clean up after each test
afterEach(() => {
    jest.clearAllMocks();
});

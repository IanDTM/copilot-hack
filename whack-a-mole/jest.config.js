module.exports = {
    testEnvironment: 'jsdom',
    testMatch: ['**/tests/frontend/**/*.test.js'],
    collectCoverageFrom: [
        'frontend/static/js/**/*.js',
        '!frontend/static/js/**/*.test.js'
    ],
    coverageDirectory: 'coverage/frontend',
    setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],
    moduleFileExtensions: ['js'],
    testPathIgnorePatterns: ['/node_modules/', '/backend/'],
    verbose: true
};

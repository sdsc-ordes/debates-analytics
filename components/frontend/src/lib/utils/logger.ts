import pino from 'pino';

// --- Configuration ---
const config = {
    // Set base log level
    level: 'debug',

    browser: {
        asObject: false,
    },
};

// Initialize the logger
export const logger = pino(config);

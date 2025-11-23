import pino from 'pino';

// --- Configuration ---
const config = {
    // Set base log level (e.g., 'info', 'debug', 'trace')
    level: 'debug',
    // Set browser level (pino-browser)
    browser: {
        level: 'debug',
        // Use console.log for pretty printing in the browser
        asObject: false,
        transport: {
            target: 'pino-pretty',
            options: {
                // Ignore the system default time (ts) and show only message and level
                ignore: 'pid,hostname,time',
            },
        },
    },
    // Set transport options for Node/SSR environment
    transport: {
        target: 'pino-pretty',
        options: {
            colorize: true,
            ignore: 'pid,hostname',
        },
    },
};

// Initialize the logger
export const logger = pino(config);

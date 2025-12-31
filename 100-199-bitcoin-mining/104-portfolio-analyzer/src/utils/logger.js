/**
 * Logger utility for environment-aware logging
 * Provides different log levels and suppresses debug logs in production
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

const LOG_LEVEL_NAMES = {
  [LOG_LEVELS.DEBUG]: 'DEBUG',
  [LOG_LEVELS.INFO]: 'INFO',
  [LOG_LEVELS.WARN]: 'WARN',
  [LOG_LEVELS.ERROR]: 'ERROR',
};

/**
 * Get current log level from environment or default to INFO
 * @returns {number} Current log level
 */
const getLogLevel = () => {
  const envLevel = process.env.REACT_APP_LOG_LEVEL?.toLowerCase();
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  // In production, only show warnings and errors
  if (!isDevelopment) {
    return LOG_LEVELS.WARN;
  }
  
  // Map environment variable to log level
  switch (envLevel) {
    case 'debug':
      return LOG_LEVELS.DEBUG;
    case 'info':
      return LOG_LEVELS.INFO;
    case 'warn':
      return LOG_LEVELS.WARN;
    case 'error':
      return LOG_LEVELS.ERROR;
    default:
      return LOG_LEVELS.INFO;
  }
};

const currentLogLevel = getLogLevel();

/**
 * Check if a log level should be displayed
 * @param {number} level - Log level to check
 * @returns {boolean} Whether the log should be displayed
 */
const shouldLog = (level) => {
  return level >= currentLogLevel;
};

/**
 * Format log message with timestamp and level
 * @param {string} level - Log level name
 * @param {string} message - Log message
 * @param {any} [data] - Additional data to log
 * @returns {string} Formatted log message
 */
/**
 * Format log message with timestamp and level
 * @param {string} level - Log level name
 * @param {string} message - Log message
 * @returns {string} Formatted log message
 */
const formatMessage = (level, message) => {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level}] ${message}`;
};

/**
 * Logger object with methods for different log levels
 */
const logger = {
  /**
   * Log debug messages (only in development)
   * @param {string} message - Debug message
   * @param {any} [data] - Additional data
   */
  debug: (message, data) => {
    if (shouldLog(LOG_LEVELS.DEBUG)) {
      const formatted = formatMessage(LOG_LEVEL_NAMES[LOG_LEVELS.DEBUG], message);
      if (data !== undefined) {
        console.log(formatted, data);
      } else {
        console.log(formatted);
      }
    }
  },

  /**
   * Log info messages
   * @param {string} message - Info message
   * @param {any} [data] - Additional data
   */
  info: (message, data) => {
    if (shouldLog(LOG_LEVELS.INFO)) {
      const formatted = formatMessage(LOG_LEVEL_NAMES[LOG_LEVELS.INFO], message);
      if (data !== undefined) {
        console.info(formatted, data);
      } else {
        console.info(formatted);
      }
    }
  },

  /**
   * Log warning messages
   * @param {string} message - Warning message
   * @param {any} [data] - Additional data
   */
  warn: (message, data) => {
    if (shouldLog(LOG_LEVELS.WARN)) {
      const formatted = formatMessage(LOG_LEVEL_NAMES[LOG_LEVELS.WARN], message);
      if (data !== undefined) {
        console.warn(formatted, data);
      } else {
        console.warn(formatted);
      }
    }
  },

  /**
   * Log error messages
   * @param {string} message - Error message
   * @param {Error|any} [error] - Error object or additional data
   */
  error: (message, error) => {
    if (shouldLog(LOG_LEVELS.ERROR)) {
      const formatted = formatMessage(LOG_LEVEL_NAMES[LOG_LEVELS.ERROR], message);
      
      if (error instanceof Error) {
        console.error(formatted, error);
        // In production, you might want to send this to an error tracking service
        // Example: Sentry.captureException(error);
      } else if (error !== undefined) {
        console.error(formatted, error);
      } else {
        console.error(formatted);
      }
    }
  },
};

export default logger;


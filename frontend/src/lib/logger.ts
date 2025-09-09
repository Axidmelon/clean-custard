// Centralized logging utility
import { isDebugMode } from './constants';

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

class Logger {
  private shouldLog(level: LogLevel): boolean {
    // Always log errors in production
    if (level === LogLevel.ERROR) return true;
    
    // Only log debug/info/warn in development or when debug mode is enabled
    return isDebugMode();
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.log(`[DEBUG] ${message}`, ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog(LogLevel.INFO)) {
      console.log(`[INFO] ${message}`, ...args);
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog(LogLevel.WARN)) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  }

  error(message: string, error?: Error | unknown, ...args: unknown[]): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      console.error(`[ERROR] ${message}`, error, ...args);
    }
  }

  // Special method for API responses (only in development)
  apiResponse(message: string, data: unknown): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.log(`[API] ${message}`, data);
    }
  }

  // Special method for user actions (only in development)
  userAction(action: string, details?: unknown): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.log(`[USER] ${action}`, details);
    }
  }
}

// Export a singleton instance
export const logger = new Logger();

// Convenience functions for common use cases
export const logApiResponse = (endpoint: string, response: unknown) => {
  logger.apiResponse(`${endpoint} response:`, response);
};

export const logUserAction = (action: string, details?: unknown) => {
  logger.userAction(action, details);
};

export const logError = (context: string, error: Error | unknown) => {
  logger.error(`${context}:`, error);
};

export const logDebug = (message: string, ...args: unknown[]) => {
  logger.debug(message, ...args);
};

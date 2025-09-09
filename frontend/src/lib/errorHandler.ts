// Global error handling utilities
import { logError, logDebug } from './logger';

export interface ErrorReport {
  errorId: string;
  message: string;
  stack?: string;
  userAgent: string;
  url: string;
  timestamp: string;
  userId?: string;
  sessionId?: string;
}

class GlobalErrorHandler {
  private errorCount = 0;
  private maxErrors = 10; // Prevent error spam
  private errorWindow = 60000; // 1 minute window
  private lastErrorTime = 0;

  constructor() {
    this.setupGlobalHandlers();
  }

  private setupGlobalHandlers() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(event.reason, 'Unhandled Promise Rejection');
    });

    // Handle uncaught errors
    window.addEventListener('error', (event) => {
      this.handleError(event.error, 'Uncaught Error', {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.handleError(
          new Error(`Resource loading error: ${event.target}`),
          'Resource Error',
          {
            tagName: (event.target as Element)?.tagName,
            src: (event.target as HTMLImageElement)?.src || (event.target as HTMLLinkElement)?.href
          }
        );
      }
    }, true);
  }

  private handleError(error: Error | unknown, type: string, context?: Record<string, unknown>) {
    // Rate limiting
    const now = Date.now();
    if (now - this.lastErrorTime < this.errorWindow) {
      this.errorCount++;
      if (this.errorCount > this.maxErrors) {
        logDebug('Too many errors, suppressing further error reports');
        return;
      }
    } else {
      this.errorCount = 1;
      this.lastErrorTime = now;
    }

    const errorReport = this.createErrorReport(error, type, context);
    this.logError(errorReport);
  }

  private createErrorReport(error: Error | unknown, type: string, context?: Record<string, unknown>): ErrorReport {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      errorId,
      message: error?.message || String(error) || 'Unknown error',
      stack: error?.stack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      userId: this.getUserId(),
      sessionId: this.getSessionId(),
      ...context
    };
  }

  private getUserId(): string | undefined {
    try {
      const user = localStorage.getItem('user');
      if (user) {
        const parsedUser = JSON.parse(user);
        return parsedUser.id;
      }
    } catch (error) {
      // Ignore parsing errors
    }
    return undefined;
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }

  private logError(errorReport: ErrorReport) {
    logError(`[${errorReport.errorId}] ${errorReport.message}`, errorReport);
    
    // In production, you would send this to an error reporting service
    // For now, we'll just log it
    if (process.env.NODE_ENV === 'production') {
      // Example: sendToErrorService(errorReport);
      console.error('Error Report:', errorReport);
    }
  }

  // Public method to manually report errors
  public reportError(error: Error | unknown, context?: Record<string, unknown>) {
    this.handleError(error, 'Manual Error Report', context);
  }

  // Public method to get current session info
  public getSessionInfo() {
    return {
      sessionId: this.getSessionId(),
      userId: this.getUserId(),
      errorCount: this.errorCount,
      lastErrorTime: this.lastErrorTime
    };
  }
}

// Create singleton instance
export const globalErrorHandler = new GlobalErrorHandler();

// Convenience functions
export const reportError = (error: Error | unknown, context?: Record<string, unknown>) => {
  globalErrorHandler.reportError(error, context);
};

export const getSessionInfo = () => {
  return globalErrorHandler.getSessionInfo();
};

// React error boundary helper
export const createErrorReport = (error: Error, errorInfo: { componentStack?: string }) => {
  return {
    errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    message: error.message,
    stack: error.stack,
    componentStack: errorInfo.componentStack,
    userAgent: navigator.userAgent,
    url: window.location.href,
    timestamp: new Date().toISOString(),
    userId: globalErrorHandler.getSessionInfo().userId,
    sessionId: globalErrorHandler.getSessionInfo().sessionId
  };
};

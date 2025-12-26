import React from 'react';
import { AlertCircle } from 'lucide-react';
import logger from '../utils/logger';

/**
 * Error Boundary component to catch and handle React component errors
 * Provides user-friendly error display and error reporting
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  /**
   * Update state when an error is caught
   * @param {Error} error - The error that was thrown
   * @param {Object} errorInfo - Additional error information
   */
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  /**
   * Log error details when component catches an error
   * @param {Error} error - The error that was thrown
   * @param {Object} errorInfo - Component stack trace information
   */
  componentDidCatch(error, errorInfo) {
    // Log error for debugging
    logger.error('ErrorBoundary caught an error:', error);
    logger.error('Error info:', errorInfo);
    
    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // In production, you might want to send this to an error tracking service
    // Example: Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  /**
   * Reset error state and retry rendering
   */
  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center gap-4 mb-6">
              <AlertCircle className="w-12 h-12 text-red-500" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Something went wrong</h1>
                <p className="text-gray-600 mt-1">
                  We're sorry, but something unexpected happened. Please try refreshing the page.
                </p>
              </div>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mt-6 p-4 bg-red-50 rounded-lg border border-red-200">
                <h2 className="font-semibold text-red-900 mb-2">Error Details (Development Only)</h2>
                <pre className="text-xs text-red-800 overflow-auto max-h-64">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Reload Page
              </button>
            </div>

            <div className="mt-6 text-sm text-gray-500">
              <p>
                If this problem persists, please check your browser console for more details
                or contact support if available.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;


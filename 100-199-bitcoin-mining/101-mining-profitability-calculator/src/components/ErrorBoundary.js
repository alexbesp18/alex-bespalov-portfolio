/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 */

import React from 'react';
import PropTypes from 'prop-types';
import { AlertCircle } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Calculator error:', error, errorInfo);
    // You could log to an error reporting service here
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center p-8 bg-red-50 rounded-lg">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-600 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">Please refresh the page to try again</p>
          {this.state.error && (
            <details className="mb-4 text-left max-w-md mx-auto">
              <summary className="cursor-pointer text-sm text-gray-700 mb-2">
                Error details
              </summary>
              <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto">
                {this.state.error.toString()}
              </pre>
            </details>
          )}
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired
};

export default ErrorBoundary;

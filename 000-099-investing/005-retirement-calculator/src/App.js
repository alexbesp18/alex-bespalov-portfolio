import React from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import RetirementInflationCalculator from './components/RetirementInflationCalculator';
import './App.css';

/**
 * Root application component
 * 
 * Wraps the calculator in an error boundary for graceful error handling.
 */
function App() {
  return (
    <ErrorBoundary>
      <div className="App">
        <RetirementInflationCalculator />
      </div>
    </ErrorBoundary>
  );
}

export default App;

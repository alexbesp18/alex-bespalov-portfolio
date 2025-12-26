import React from 'react';
import PortfolioAnalyzer from './components/PortfolioAnalyzer';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <div className="App">
        <PortfolioAnalyzer />
      </div>
    </ErrorBoundary>
  );
}

export default App;
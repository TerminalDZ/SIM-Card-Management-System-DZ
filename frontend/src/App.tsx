import React from 'react';
import SimpleDashboard from './components/SimpleDashboard';
import { ErrorBoundary } from './components/ErrorBoundary';
import './index.css';

function App() {
  return (
    <div className="App">
      <ErrorBoundary>
        <SimpleDashboard />
      </ErrorBoundary>
    </div>
  );
}

export default App;

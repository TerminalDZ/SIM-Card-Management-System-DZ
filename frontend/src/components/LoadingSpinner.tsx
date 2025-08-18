import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export function LoadingSpinner({ size = 'md', text, className = '' }: LoadingSpinnerProps) {
  const sizeStyles = {
    sm: { width: '16px', height: '16px' },
    md: { width: '32px', height: '32px' },
    lg: { width: '48px', height: '48px' }
  };

  const spinnerStyle = {
    ...sizeStyles[size],
    border: '2px solid #f3f3f3',
    borderTop: '2px solid #3498db',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} className={className}>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      <div style={spinnerStyle}></div>
      {text && <span style={{ fontSize: '14px', color: '#666' }}>{text}</span>}
    </div>
  );
}

export function LoadingScreen({ text = 'Loading...' }: { text?: string }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}

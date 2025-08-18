import React from 'react';

interface ErrorAlertProps {
  error: string | null;
  onDismiss?: () => void;
  className?: string;
  variant?: 'error' | 'warning' | 'info';
}

export function ErrorAlert({ error, onDismiss, className = '', variant = 'error' }: ErrorAlertProps) {
  if (!error) return null;

  const variantStyles = {
    error: { backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b' },
    warning: { backgroundColor: '#fffbeb', border: '1px solid #fed7aa', color: '#92400e' },
    info: { backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af' }
  };

  const iconColors = {
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  };

  return (
    <div 
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '16px',
        borderRadius: '8px',
        ...variantStyles[variant]
      }}
      className={className}
    >
      <div style={{ 
        width: '20px', 
        height: '20px', 
        borderRadius: '50%', 
        backgroundColor: iconColors[variant],
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        marginTop: '2px'
      }}>
        ⚠
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: '14px', fontWeight: '500', margin: 0 }}>
          {variant === 'error' && 'Error'}
          {variant === 'warning' && 'Warning'}
          {variant === 'info' && 'Information'}
        </p>
        <p style={{ fontSize: '14px', margin: '4px 0 0 0' }}>
          {error}
        </p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            width: '24px',
            height: '24px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          ×
        </button>
      )}
    </div>
  );
}

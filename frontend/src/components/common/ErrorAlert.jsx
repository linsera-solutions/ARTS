import React from 'react'

export function ErrorAlert({ message, error, onRetry }) {
  const displayMsg = message || error?.message || 'An unexpected error occurred.'
  
  return (
    <div className="error-alert-container">
      <div className="error-alert-content">
        <span className="error-alert-icon">⚠️</span>
        <div className="error-alert-text">
          <strong className="error-alert-title">Request Failed</strong>
          <p className="error-alert-message">{displayMsg}</p>
        </div>
      </div>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn btn-outline btn-sm">
          Retry
        </button>
      )}
    </div>
  )
}

import React from 'react'

export function LoadingSpinner({ message = 'Loading...', size = 'md' }) {
  return (
    <div className={`loading-container loading-${size}`}>
      <div className="spinner" />
      {message && <p className="loading-message">{message}</p>}
    </div>
  )
}

export function SkeletonRow({ cols = 4 }) {
  return (
    <div className="skeleton-row">
      {Array.from({ length: cols }).map((_, idx) => (
        <div key={idx} className="skeleton-cell" />
      ))}
    </div>
  )
}

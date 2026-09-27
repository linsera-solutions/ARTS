import React from 'react'

const STATUS_VARIANTS = {
  // Application Lifecycle Statuses
  Received: { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
  'Under Review': { bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
  Shortlisted: { bg: '#e0e7ff', text: '#4338ca', border: '#c7d2fe' },
  'Discussion / Interview': { bg: '#f3e8ff', text: '#7e22ce', border: '#e9d5ff' },
  Selected: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },
  'Not Selected': { bg: '#fee2e2', text: '#b91c1c', border: '#fecaca' },
  Withdrawn: { bg: '#f1f5f9', text: '#475569', border: '#e2e8f0' },

  // Role / Team Statuses
  Open: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },
  Closed: { bg: '#f1f5f9', text: '#475569', border: '#e2e8f0' },
  Filled: { bg: '#e0f2fe', text: '#0369a1', border: '#bae6fd' },
  Forming: { bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
  Active: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },

  // Recommendation
  Advance: { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' },
  Reject: { bg: '#fee2e2', text: '#b91c1c', border: '#fecaca' },
  Waitlist: { bg: '#fef3c7', text: '#b45309', border: '#fde68a' },
  'Needs Discussion': { bg: '#f3e8ff', text: '#7e22ce', border: '#e9d5ff' },
}

export function Badge({ children, variant, className = '' }) {
  const statusKey = variant || children
  const style = STATUS_VARIANTS[statusKey] || {
    bg: '#f1f5f9',
    text: '#334155',
    border: '#e2e8f0',
  }

  return (
    <span
      className={`arts-badge ${className}`}
      style={{
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        padding: '0.2rem 0.6rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: '600',
        display: 'inline-flex',
        alignItems: 'center',
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  )
}

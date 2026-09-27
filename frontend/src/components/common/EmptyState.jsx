import React from 'react'

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="empty-state-container">
      {Icon && (
        <div className="empty-state-icon">
          <Icon size={40} />
        </div>
      )}
      <h4 className="empty-state-title">{title || 'No records found'}</h4>
      {description && <p className="empty-state-description">{description}</p>}
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  )
}

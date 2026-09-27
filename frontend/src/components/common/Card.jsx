import React from 'react'

export function Card({ children, title, subtitle, action, className = '', style = {} }) {
  return (
    <div className={`arts-card ${className}`} style={style}>
      {(title || subtitle || action) && (
        <div className="arts-card-header">
          <div>
            {title && <h3 className="arts-card-title">{title}</h3>}
            {subtitle && <p className="arts-card-subtitle">{subtitle}</p>}
          </div>
          {action && <div className="arts-card-action">{action}</div>}
        </div>
      )}
      <div className="arts-card-body">{children}</div>
    </div>
  )
}

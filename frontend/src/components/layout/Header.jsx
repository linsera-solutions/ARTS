import React, { useState, useEffect } from 'react'
import { healthService } from '../../api/services'
import { Activity, ShieldCheck } from 'lucide-react'

export function Header() {
  const [backendState, setBackendState] = useState({
    connected: false,
    checked: false,
  })

  useEffect(() => {
    healthService
      .getHealth()
      .then((data) => {
        setBackendState({
          connected: data?.status === 'healthy',
          checked: true,
        })
      })
      .catch(() => {
        setBackendState({
          connected: false,
          checked: true,
        })
      })
  }, [])

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="cycle-badge">
          <span className="cycle-pulse" />
          <span>NASA Space Apps Challenge — 2026 Recruitment</span>
        </div>
      </div>

      <div className="header-right">
        <div className="system-status-indicator">
          <Activity size={15} className="status-icon" />
          <span>
            API:{' '}
            <strong
              style={{
                color: backendState.connected ? '#16a34a' : '#dc2626',
              }}
            >
              {backendState.connected ? 'Online' : 'Offline / Mock'}
            </strong>
          </span>
        </div>

        <div className="security-notice">
          <ShieldCheck size={15} />
          <span>Human-in-the-Loop Mode</span>
        </div>
      </div>
    </header>
  )
}

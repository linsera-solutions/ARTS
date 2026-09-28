import React, { useState, useEffect } from 'react'
import { healthService } from '../../api/services'
import { useAuth } from '../../context/AuthContext'
import { Activity, ShieldCheck, LogOut, User } from 'lucide-react'

export function Header() {
  const { user, logout } = useAuth()
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
          <span>Decision-Support Mode</span>
        </div>

        {user && (
          <div className="user-profile-menu">
            <div className="user-info">
              <span className="user-name-label">{user.full_name || user.email}</span>
              <span className="user-role-label">{user.user_role || 'Team Lead'}</span>
            </div>
            <button
              type="button"
              className="btn-signout"
              onClick={logout}
              title="Sign Out of ARTS Console"
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

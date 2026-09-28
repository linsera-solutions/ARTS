import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Sparkles, Lock, Mail, AlertCircle, ArrowRight, ShieldCheck, Key } from 'lucide-react'

export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoading, authError } = useAuth()

  const [email, setEmail] = useState('lead@nasa.org')
  const [password, setPassword] = useState('NasaSpaceApps2026!')
  const [errorMessage, setErrorMessage] = useState('')

  const from = location.state?.from?.pathname || '/'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrorMessage('')

    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.')
      return
    }

    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setErrorMessage(err.message || 'Invalid email or password.')
    }
  }

  const handleQuickFill = () => {
    setEmail('lead@nasa.org')
    setPassword('NasaSpaceApps2026!')
    setErrorMessage('')
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <div className="login-brand">
            <div className="login-icon-box">
              <Sparkles size={24} className="login-icon" />
            </div>
            <div>
              <h1 className="login-title">ARTS Console</h1>
              <span className="login-subtitle">Applicant Review & Team Selection System</span>
            </div>
          </div>
          <div className="login-event-tag">
            <span>NASA Space Apps Challenge 2026</span>
          </div>
        </div>

        {/* Error Alert */}
        {(errorMessage || authError) && (
          <div className="login-error-alert">
            <AlertCircle size={18} className="error-alert-icon" />
            <span>{errorMessage || authError}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Recruiter Email
            </label>
            <div className="input-with-icon">
              <Mail size={17} className="field-icon" />
              <input
                id="email"
                type="email"
                className="form-control field-input"
                placeholder="lead@nasa.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <div className="input-with-icon">
              <Lock size={17} className="field-icon" />
              <input
                id="password"
                type="password"
                className="form-control field-input"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg login-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>Sign In to Console</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Quick Credential Helper for MVP Testing */}
        <div className="login-quickfill-box">
          <div className="quickfill-header">
            <Key size={14} />
            <span>Default Team Lead Account (MVP)</span>
          </div>
          <div className="quickfill-creds">
            <code>lead@nasa.org</code> / <code>NasaSpaceApps2026!</code>
          </div>
          <button
            type="button"
            className="quickfill-btn"
            onClick={handleQuickFill}
          >
            Auto-fill credentials
          </button>
        </div>

        {/* Footer Security Notice */}
        <div className="login-footer">
          <ShieldCheck size={15} />
          <span>Internal system for authorized Team Leads. No public applicant accounts.</span>
        </div>
      </div>
    </div>
  )
}

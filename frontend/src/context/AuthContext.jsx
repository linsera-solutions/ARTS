import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authService } from '../api/services'

const AuthContext = createContext(null)

const TOKEN_KEY = 'arts_auth_token'
const USER_KEY = 'arts_auth_user'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null)
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(USER_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  // Verify token on initial application mount
  useEffect(() => {
    async function verifySession() {
      const savedToken = localStorage.getItem(TOKEN_KEY)
      if (!savedToken) {
        setIsLoading(false)
        return
      }

      try {
        const currentUser = await authService.getMe()
        setUser(currentUser)
        localStorage.setItem(USER_KEY, JSON.stringify(currentUser))
      } catch (err) {
        console.warn('Session expired or invalid token:', err)
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    verifySession()
  }, [])

  // Login handler
  const login = useCallback(async (email, password) => {
    setIsLoading(true)
    setAuthError(null)
    try {
      const response = await authService.login({ email, password })
      const accessToken = response.access_token
      const userData = response.user

      localStorage.setItem(TOKEN_KEY, accessToken)
      localStorage.setItem(USER_KEY, JSON.stringify(userData))

      setToken(accessToken)
      setUser(userData)
      return userData
    } catch (err) {
      const message = err.message || 'Authentication failed. Please check your credentials.'
      setAuthError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Logout handler
  const logout = useCallback(async () => {
    try {
      if (token) {
        await authService.logout().catch(() => {})
      }
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      setToken(null)
      setUser(null)
      setAuthError(null)
    }
  }, [token])

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    authError,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Centralized API client for ARTS backend communication with Bearer JWT support.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'arts_auth_token'

class ApiError extends Error {
  constructor(message, code = 'API_ERROR', status = 500, details = null) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem(TOKEN_KEY)

  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const config = {
    ...options,
    headers,
  }

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }

  try {
    const response = await fetch(url, config)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const errorMsg = data?.error?.message || `HTTP ${response.status}: Request failed`
      const errorCode = data?.error?.code || `HTTP_${response.status}`
      const errorDetails = data?.error?.details || null

      // Automatically trigger token cleanup if 401 occurs on protected routes
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem('arts_auth_user')
      }

      throw new ApiError(errorMsg, errorCode, response.status, errorDetails)
    }

    return data?.data !== undefined ? data.data : data
  } catch (err) {
    if (err instanceof ApiError) {
      throw err
    }
    throw new ApiError(
      err.message || 'Unable to connect to the backend server.',
      'NETWORK_ERROR',
      0
    )
  }
}

export const apiClient = {
  get: (endpoint, params = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val)
      }
    })
    const queryString = query.toString() ? `?${query.toString()}` : ''
    return request(`${endpoint}${queryString}`, { method: 'GET' })
  },
  post: (endpoint, body) => request(endpoint, { method: 'POST', body }),
  patch: (endpoint, body) => request(endpoint, { method: 'PATCH', body }),
  delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
}

export { ApiError }

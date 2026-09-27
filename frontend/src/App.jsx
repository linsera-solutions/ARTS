import { useState, useEffect } from 'react'
import './App.css'

const APPROVED_ROLES = [
  { id: 1, title: 'Team Lead + Product/Game Concept Lead / Research & Presentation' },
  { id: 2, title: 'Game/App Developer' },
  { id: 3, title: 'UI/UX & Visual Designer' },
  { id: 4, title: 'Space/Science Research + Game Logic' }
]

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking backend...')
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

  useEffect(() => {
    fetch(`${apiBaseUrl}/status`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setBackendStatus(`Connected (${data.service || 'ARTS API'} v${data.version || '0.1.0'})`)
      })
      .catch((err) => {
        setBackendStatus(`Backend offline or unreachable (${err.message})`)
      })
  }, [apiBaseUrl])

  return (
    <div className="app-container">
      <div className="header-card">
        <span className="badge">NASA Space Apps Challenge Recruitment</span>
        <h1>ARTS MVP</h1>
        <p className="subtitle">Applicant Review & Team Selection System</p>
        
        <div className="status-card">
          <strong>Backend API Status: </strong>
          <span>{backendStatus}</span>
        </div>

        <h3 style={{ marginTop: '2rem', marginBottom: '0.5rem', textAlign: 'left', color: '#1e293b' }}>
          Approved Team Roles
        </h3>
        <div className="roles-grid">
          {APPROVED_ROLES.map((role) => (
            <div key={role.id} className="role-card">
              <span className="role-number">Role #{role.id}</span>
              <p className="role-title">{role.title}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App

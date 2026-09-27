import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { rolesService, applicationsService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import {
  Users,
  BookmarkCheck,
  MessageSquare,
  Award,
  ArrowRight,
  Sparkles,
} from 'lucide-react'

export function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [roles, setRoles] = useState([])
  const [applications, setApplications] = useState([])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [rolesData, appsData] = await Promise.all([
        rolesService.list(),
        applicationsService.list(),
      ])
      setRoles(rolesData || [])
      setApplications(appsData || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return <LoadingSpinner message="Loading recruitment overview..." />
  }

  if (error) {
    return <ErrorAlert error={error} onRetry={loadData} />
  }

  const counts = {
    total: applications.length,
    received: applications.filter((a) => a.current_status === 'Received').length,
    underReview: applications.filter((a) => a.current_status === 'Under Review').length,
    shortlisted: applications.filter((a) => a.current_status === 'Shortlisted').length,
    interviews: applications.filter((a) => a.current_status === 'Discussion / Interview').length,
    selected: applications.filter((a) => a.current_status === 'Selected').length,
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Recruitment Dashboard</h1>
          <p className="page-subtitle">
            Applicant Review & Team Selection Overview for NASA Space Apps Challenge
          </p>
        </div>
        <Link to="/applications">
          <Button icon={ArrowRight}>View All Applications</Button>
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Total Applications</span>
            <Users size={18} className="text-blue-500" />
          </div>
          <div className="metric-value">{counts.total}</div>
          <span className="metric-meta">From Google Forms intake</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Under Review</span>
            <Sparkles size={18} className="text-amber-500" />
          </div>
          <div className="metric-value">{counts.underReview + counts.received}</div>
          <span className="metric-meta">{counts.received} awaiting initial screening</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Shortlisted</span>
            <BookmarkCheck size={18} className="text-indigo-500" />
          </div>
          <div className="metric-value">{counts.shortlisted}</div>
          <span className="metric-meta">Candidate pool for discussion</span>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Team Confirmed</span>
            <Award size={18} className="text-emerald-500" />
          </div>
          <div className="metric-value">{counts.selected} / 4</div>
          <span className="metric-meta">Approved roster positions</span>
        </div>
      </div>

      {/* Roles Progress Grid */}
      <div style={{ marginTop: '2rem' }}>
        <h2 className="section-title">Target Team Roles (4 Positions)</h2>
        <div className="roles-overview-grid">
          {roles.map((role) => {
            const roleApps = applications.filter((a) => a.role_id === role.id)
            const roleShortlisted = roleApps.filter((a) => a.current_status === 'Shortlisted').length
            const roleSelected = roleApps.some((a) => a.current_status === 'Selected')

            return (
              <Card
                key={role.id}
                title={role.role_name}
                subtitle={`${role.number_of_openings} opening • ${roleApps.length} applicants`}
                action={<Badge variant={roleSelected ? 'Filled' : role.role_status}>{roleSelected ? 'Filled' : role.role_status}</Badge>}
              >
                <p className="role-card-description">{role.role_description}</p>
                <div className="role-stats-footer">
                  <div className="stat-pill">
                    <strong>{roleShortlisted}</strong> Shortlisted
                  </div>
                  <Link to={`/applications?role=${role.id}`} className="link-action">
                    Review ({roleApps.length}) &rarr;
                  </Link>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}

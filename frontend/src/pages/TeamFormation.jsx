import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { rolesService, applicationsService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Award, UserCheck, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react'

export function TeamFormation() {
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
      setRoles(rolesData?.items || rolesData || [])
      setApplications(appsData?.items || appsData || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) return <LoadingSpinner message="Loading team roster assembly..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />

  const selectedApps = applications.filter((a) => a.current_status === 'Selected')
  const filledCount = roles.filter((r) =>
    selectedApps.some((a) => a.role_id === r.id)
  ).length

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Team Formation & Composition</h1>
          <p className="page-subtitle">
            4-Member NASA Space Apps Challenge Project Team Roster (SCR-08)
          </p>
        </div>
      </div>

      {/* Roster Completion Status Banner */}
      <div className="team-status-banner">
        <div className="banner-icon">
          {filledCount === 4 ? (
            <CheckCircle2 size={28} className="text-emerald-500" />
          ) : (
            <Award size={28} className="text-indigo-500" />
          )}
        </div>
        <div className="banner-content">
          <h3>
            Team Roster Status: {filledCount} of 4 Positions Filled
          </h3>
          <p>
            {filledCount === 4
              ? 'All 4 target team roles have confirmed selected candidates.'
              : 'Complete evaluations and candidate discussions to finalize the team roster.'}
          </p>
        </div>
      </div>

      {/* 4 Approved Roles Roster Grid */}
      <div className="roster-grid">
        {roles.map((role, idx) => {
          const assignedCandidate = selectedApps.find((a) => a.role_id === role.id)

          return (
            <Card
              key={role.id}
              className={`roster-slot-card ${assignedCandidate ? 'slot-filled' : 'slot-vacant'}`}
            >
              <div className="slot-header">
                <span className="slot-number">Position #{idx + 1}</span>
                {assignedCandidate ? (
                  <Badge variant="Selected">Confirmed Roster Slot</Badge>
                ) : (
                  <Badge variant="Open">Position Vacant</Badge>
                )}
              </div>

              <h3 className="slot-role-title">{role.role_name}</h3>
              <p className="slot-role-desc">{role.role_description}</p>

              <div className="slot-assignment-area">
                {assignedCandidate ? (
                  <div className="assigned-candidate-box">
                    <div className="assigned-cand-header">
                      <UserCheck size={20} className="text-emerald-600" />
                      <div>
                        <strong>{assignedCandidate.applicant?.full_name}</strong>
                        <span className="assigned-cand-meta">
                          {assignedCandidate.applicant?.email} • {assignedCandidate.applicant?.location || 'Location not specified'}
                        </span>
                      </div>
                    </div>
                    <div style={{ marginTop: '0.75rem', textAlign: 'right' }}>
                      <Link to={`/applications/${assignedCandidate.id}`}>
                        <Button size="sm" variant="outline">
                          View Selected Profile
                        </Button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="vacant-slot-box">
                    <div className="vacant-prompt">
                      <AlertCircle size={18} className="text-amber-500" />
                      <span>No candidate selected for this slot yet.</span>
                    </div>
                    <Link to={`/applications?role=${role.id}`}>
                      <Button size="sm" variant="secondary" icon={ArrowRight}>
                        Review Candidates for Role
                      </Button>
                    </Link>
                  </div>
                )}
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

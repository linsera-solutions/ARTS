import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { applicationsService, rolesService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { EmptyState } from '../components/common/EmptyState'
import { BookmarkCheck, MessageSquare, ArrowRight, Award } from 'lucide-react'

export function Shortlist() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [shortlistedApps, setShortlistedApps] = useState([])
  const [roles, setRoles] = useState([])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [appsData, rolesData] = await Promise.all([
        applicationsService.list({ status: 'Shortlisted' }),
        rolesService.list(),
      ])
      setShortlistedApps(appsData?.items || appsData || [])
      setRoles(rolesData?.items || rolesData || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleAdvanceToInterview = async (appId) => {
    try {
      await applicationsService.updateStatus(appId, {
        new_status: 'Discussion / Interview',
        reason: 'Advanced from Shortlist to Discussion/Interview',
      })
      loadData()
    } catch (err) {
      alert(`Failed: ${err.message}`)
    }
  }

  const handleSelectCandidate = async (appId) => {
    const confirm = window.confirm(
      'Confirm selection of candidate for this role slot? Final decision is human-owned.'
    )
    if (!confirm) return
    try {
      await applicationsService.updateStatus(appId, {
        new_status: 'Selected',
        reason: 'Confirmed human selection for team roster',
      })
      loadData()
    } catch (err) {
      alert(`Failed: ${err.message}`)
    }
  }

  if (loading) return <LoadingSpinner message="Loading candidate shortlist..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Candidate Shortlist</h1>
          <p className="page-subtitle">
            Curated candidates under active consideration for target team roles (SCR-06)
          </p>
        </div>
      </div>

      {shortlistedApps.length === 0 ? (
        <EmptyState
          icon={BookmarkCheck}
          title="Shortlist is currently empty"
          description="Review applications and advance top candidates to 'Shortlisted' status to manage them here."
          action={
            <Link to="/applications">
              <Button icon={ArrowRight}>Go to Applications</Button>
            </Link>
          }
        />
      ) : (
        <div className="shortlist-roles-stack">
          {roles.map((role) => {
            const roleShortlist = shortlistedApps.filter((a) => a.role_id === role.id)

            return (
              <Card
                key={role.id}
                title={role.role_name}
                subtitle={`${roleShortlist.length} candidate(s) shortlisted`}
                className="mb-4"
              >
                {roleShortlist.length === 0 ? (
                  <p className="empty-text">No candidates currently shortlisted for this role.</p>
                ) : (
                  <div className="shortlist-candidate-grid">
                    {roleShortlist.map((app) => (
                      <div key={app.id} className="shortlist-candidate-card">
                        <div className="shortlist-cand-header">
                          <div>
                            <strong className="cand-name">{app.applicant?.full_name}</strong>
                            <p className="cand-sub">{app.applicant?.email} • {app.applicant?.location || 'Location not specified'}</p>
                          </div>
                          <Badge variant="Shortlisted">Shortlisted</Badge>
                        </div>

                        {app.motivation_statement && (
                          <p className="cand-snippet">
                            &ldquo;{app.motivation_statement.slice(0, 140)}...&rdquo;
                          </p>
                        )}

                        <div className="shortlist-cand-actions">
                          <Link to={`/applications/${app.id}`}>
                            <Button size="sm" variant="outline">
                              View Profile
                            </Button>
                          </Link>
                          <Button
                            size="sm"
                            variant="secondary"
                            icon={MessageSquare}
                            onClick={() => handleAdvanceToInterview(app.id)}
                          >
                            Schedule Discussion
                          </Button>
                          <Button
                            size="sm"
                            variant="primary"
                            icon={Award}
                            onClick={() => handleSelectCandidate(app.id)}
                          >
                            Select for Team
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { applicationsService, interviewsService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { EmptyState } from '../components/common/EmptyState'
import { Modal } from '../components/common/Modal'
import { MessageSquare, Calendar, Video, CheckCircle2, User, ArrowRight } from 'lucide-react'

export function Interviews() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [interviewApps, setInterviewApps] = useState([])

  // Discussion outcome modal
  const [selectedApp, setSelectedApp] = useState(null)
  const [outcomeSummary, setOutcomeSummary] = useState('')
  const [nextDecision, setNextDecision] = useState('Selected')
  const [savingOutcome, setSavingOutcome] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await applicationsService.list({ status: 'Discussion / Interview' })
      setInterviewApps(data || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleOutcomeSubmit = async (e) => {
    e.preventDefault()
    if (!selectedApp) return

    setSavingOutcome(true)
    try {
      // 1. Record interview outcome entry
      await interviewsService.create({
        application_id: selectedApp.id,
        scheduled_at: new Date().toISOString(),
        format: 'Video Call',
        status: 'Completed',
        outcome_summary: outcomeSummary,
      })

      // 2. Transition status based on human decision
      await applicationsService.updateStatus(selectedApp.id, {
        new_status: nextDecision,
        reason: `Interview outcome recorded: ${outcomeSummary}`,
      })

      setSelectedApp(null)
      setOutcomeSummary('')
      loadData()
    } catch (err) {
      alert(`Failed to save outcome: ${err.message}`)
    } finally {
      setSavingOutcome(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading candidate discussions..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Candidate Discussions & Interviews</h1>
          <p className="page-subtitle">
            Synchronous deliberations, structured discussions, and outcome tracking (SCR-07)
          </p>
        </div>
      </div>

      {interviewApps.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No active candidate discussions"
          description="Candidates advanced to 'Discussion / Interview' will appear here for deliberation and final outcome recording."
          action={
            <Link to="/shortlist">
              <Button icon={ArrowRight}>View Shortlist</Button>
            </Link>
          }
        />
      ) : (
        <div className="interviews-grid">
          {interviewApps.map((app) => (
            <Card
              key={app.id}
              title={app.applicant?.full_name}
              subtitle={`Role: ${app.role?.role_name}`}
              action={<Badge variant="Discussion / Interview">In Discussion</Badge>}
            >
              <div className="interview-card-details">
                <div className="interview-meta-item">
                  <User size={15} />
                  <span>Email: {app.applicant?.email}</span>
                </div>
                <div className="interview-meta-item">
                  <Video size={15} />
                  <span>Preferred Channel: Video / Online Call</span>
                </div>
                {app.availability_info && (
                  <div className="interview-meta-item">
                    <Calendar size={15} />
                    <span>Availability: {app.availability_info}</span>
                  </div>
                )}
              </div>

              <div className="interview-card-actions">
                <Link to={`/applications/${app.id}`}>
                  <Button size="sm" variant="outline">
                    View Evidence
                  </Button>
                </Link>
                <Button
                  size="sm"
                  variant="primary"
                  icon={CheckCircle2}
                  onClick={() => setSelectedApp(app)}
                >
                  Record Discussion Outcome
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Record Outcome Modal */}
      <Modal
        isOpen={Boolean(selectedApp)}
        onClose={() => setSelectedApp(null)}
        title="Record Discussion Outcome"
        footer={
          <>
            <Button variant="outline" onClick={() => setSelectedApp(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleOutcomeSubmit}
              loading={savingOutcome}
            >
              Confirm Decision
            </Button>
          </>
        }
      >
        {selectedApp && (
          <form onSubmit={handleOutcomeSubmit}>
            <p style={{ margin: '0 0 1rem 0', color: '#475569' }}>
              Candidate: <strong>{selectedApp.applicant?.full_name}</strong>
              <br />
              Target Role: <em>{selectedApp.role?.role_name}</em>
            </p>

            <div className="form-group">
              <label className="form-label">Discussion Summary & Findings</label>
              <textarea
                value={outcomeSummary}
                onChange={(e) => setOutcomeSummary(e.target.value)}
                placeholder="Summarize key discussion points, communication strength, alignment, and panel consensus..."
                rows={4}
                className="form-control"
                required
              />
            </div>

            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label className="form-label">Post-Discussion Action (Human Decision)</label>
              <select
                value={nextDecision}
                onChange={(e) => setNextDecision(e.target.value)}
                className="form-control"
                required
              >
                <option value="Selected">Selected — Confirm Candidate for Team Roster</option>
                <option value="Shortlisted">Shortlisted — Keep on Shortlist for Alternative Role/Slot</option>
                <option value="Not Selected">Not Selected — Do Not Advance</option>
              </select>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}

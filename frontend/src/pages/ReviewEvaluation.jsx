import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { applicationsService, evaluationsService } from '../api/services'
import { Card } from '../components/common/Card'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { LoadingSpinner } from '../components/common/Loading'
import { ErrorAlert } from '../components/common/ErrorAlert'
import { Sparkles, ArrowLeft, CheckCircle2, User } from 'lucide-react'

const RECOMMENDATIONS = [
  { value: 'Advance', label: 'Advance — Strong Candidate' },
  { value: 'Needs Discussion', label: 'Needs Discussion — Clarification Required' },
  { value: 'Waitlist', label: 'Waitlist — Backup for Role' },
  { value: 'Reject', label: 'Reject — Does Not Fit Requirements' },
]

export function ReviewEvaluation() {
  const [searchParams] = useSearchParams()
  const applicationId = searchParams.get('application_id')
  const navigate = useNavigate()

  const [loading, setLoading] = useState(Boolean(applicationId))
  const [error, setError] = useState(null)
  const [application, setApplication] = useState(null)
  const [existingEvaluations, setExistingEvaluations] = useState([])

  // Form fields
  const [recommendation, setRecommendation] = useState('Advance')
  const [overallComments, setOverallComments] = useState('')
  const [technicalScore, setTechnicalScore] = useState(85)
  const [communicationScore, setCommunicationScore] = useState(80)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!applicationId) return
    setLoading(true)
    Promise.all([
      applicationsService.get(applicationId),
      evaluationsService.listByApplication(applicationId),
    ])
      .then(([appData, evalsData]) => {
        setApplication(appData)
        setExistingEvaluations(evalsData || [])
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false))
  }, [applicationId])

  const handleSubmit = async (evalStatus = 'Submitted') => {
    if (!applicationId) return
    setSubmitting(true)
    try {
      await evaluationsService.create({
        application_id: applicationId,
        reviewer_id: application.applicant_id, // Reviewer fallback for MVP foundation
        overall_recommendation: recommendation,
        overall_comments: overallComments,
        evaluation_status: evalStatus,
      })
      alert(`Evaluation ${evalStatus.toLowerCase()} successfully!`)
      navigate(`/applications/${applicationId}`)
    } catch (err) {
      alert(`Failed to save evaluation: ${err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading review workspace..." />
  if (error) return <ErrorAlert error={error} />

  return (
    <div className="page-container">
      <div style={{ marginBottom: '1rem' }}>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="btn btn-outline btn-sm"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <ArrowLeft size={16} />
          <span>Back</span>
        </button>
      </div>

      <div className="page-header">
        <div>
          <h1 className="page-title">Candidate Review & Evaluation</h1>
          <p className="page-subtitle">
            Structured human review evaluation and qualitative assessment (SCR-04)
          </p>
        </div>
      </div>

      {application && (
        <Card className="mb-4" style={{ backgroundColor: '#f8fafc' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ fontSize: '1.15rem', color: '#0f172a' }}>
                {application.applicant?.full_name}
              </strong>
              <p style={{ margin: '0.2rem 0 0 0', color: '#64748b' }}>
                Target Role: <strong>{application.role?.role_name}</strong>
              </p>
            </div>
            <Badge>{application.current_status}</Badge>
          </div>
        </Card>
      )}

      <div className="eval-form-layout">
        <Card title="Evaluation & Recommendation">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSubmit('Submitted')
            }}
          >
            {/* Overall Recommendation */}
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="form-label">Overall Recommendation</label>
              <div className="recommendation-radio-group">
                {RECOMMENDATIONS.map((rec) => (
                  <label
                    key={rec.value}
                    className={`rec-radio-card ${recommendation === rec.value ? 'rec-radio-active' : ''}`}
                  >
                    <input
                      type="radio"
                      name="recommendation"
                      value={rec.value}
                      checked={recommendation === rec.value}
                      onChange={(e) => setRecommendation(e.target.value)}
                    />
                    <span>{rec.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Qualitative Assessment / Comments */}
            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="form-label">Reviewer Comments & Rationale</label>
              <textarea
                value={overallComments}
                onChange={(e) => setOverallComments(e.target.value)}
                placeholder="Provide qualitative notes, strengths, and role alignment assessment..."
                rows={4}
                className="form-control"
                required
              />
            </div>

            {/* Actions */}
            <div className="eval-form-actions">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleSubmit('Draft')}
                disabled={submitting}
              >
                Save as Draft
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={submitting}
                icon={CheckCircle2}
              >
                Submit Final Evaluation
              </Button>
            </div>
          </form>
        </Card>

        {/* Previous Evaluations Card */}
        {existingEvaluations.length > 0 && (
          <Card title="Recorded Evaluations for Application" style={{ marginTop: '1.5rem' }}>
            <div className="eval-history-list">
              {existingEvaluations.map((ev) => (
                <div key={ev.id} className="eval-history-item">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Badge variant={ev.overall_recommendation}>{ev.overall_recommendation}</Badge>
                    <span className="eval-status-badge">{ev.evaluation_status}</span>
                  </div>
                  <p className="eval-comments">{ev.overall_comments}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

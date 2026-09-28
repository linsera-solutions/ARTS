import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { applicationsService, rolesService, interviewsService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import { EmptyState } from "../components/common/EmptyState"
import { Modal } from "../components/common/Modal"
import {
  BookmarkCheck,
  MessageSquare,
  ArrowRight,
  Award,
  XCircle,
  Calendar,
  Video,
  User,
  ExternalLink,
  ShieldCheck,
} from "lucide-react"

export function Shortlist() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [shortlistedApps, setShortlistedApps] = useState([])
  const [roles, setRoles] = useState([])

  // Schedule Interview modal
  const [interviewModalApp, setInterviewModalApp] = useState(null)
  const [interviewDate, setInterviewDate] = useState("")
  const [interviewFormat, setInterviewFormat] = useState("Video Call")
  const [interviewNotes, setInterviewNotes] = useState("")
  const [scheduling, setScheduling] = useState(false)

  // Direct Selection modal
  const [selectModalApp, setSelectModalApp] = useState(null)
  const [selectionReason, setSelectionReason] = useState("")
  const [selecting, setSelecting] = useState(false)

  // Not Selected modal
  const [rejectModalApp, setRejectModalApp] = useState(null)
  const [rejectReason, setRejectReason] = useState("")
  const [rejecting, setRejecting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [appsData, rolesData] = await Promise.all([
        applicationsService.list({ status: "Shortlisted" }),
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

  const handleScheduleInterview = async (e) => {
    e.preventDefault()
    if (!interviewModalApp) return
    setScheduling(true)
    try {
      const dt = interviewDate ? new Date(interviewDate).toISOString() : new Date().toISOString()
      // 1. Create interview record
      await interviewsService.create({
        application_id: interviewModalApp.id,
        scheduled_at: dt,
        format: interviewFormat,
        status: "Scheduled",
        outcome_summary: interviewNotes || "Scheduled discussion",
      })

      // 2. Transition status: Shortlisted -> Discussion / Interview
      await applicationsService.updateStatus(interviewModalApp.id, {
        new_status: "Discussion / Interview",
        reason: `Invited to Discussion/Interview (${interviewFormat}): ${interviewNotes || "Technical & role alignment"}`,
      })

      setInterviewModalApp(null)
      setInterviewDate("")
      setInterviewNotes("")
      loadData()
    } catch (err) {
      alert(`Failed to schedule discussion: ${err.message}`)
    } finally {
      setScheduling(false)
    }
  }

  const handleSelectCandidate = async (e) => {
    e.preventDefault()
    if (!selectModalApp) return
    setSelecting(true)
    try {
      await applicationsService.updateStatus(selectModalApp.id, {
        new_status: "Selected",
        reason: selectionReason || "Confirmed human selection for team roster from shortlist",
      })
      setSelectModalApp(null)
      setSelectionReason("")
      loadData()
    } catch (err) {
      alert(`Failed to select candidate: ${err.message}`)
    } finally {
      setSelecting(false)
    }
  }

  const handleRejectCandidate = async (e) => {
    e.preventDefault()
    if (!rejectModalApp) return
    setRejecting(true)
    try {
      await applicationsService.updateStatus(rejectModalApp.id, {
        new_status: "Not Selected",
        reason: rejectReason || "Candidate not selected from shortlist",
      })
      setRejectModalApp(null)
      setRejectReason("")
      loadData()
    } catch (err) {
      alert(`Failed: ${err.message}`)
    } finally {
      setRejecting(false)
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

      {/* Decision-Support Banner */}
      <div
        style={{
          backgroundColor: "#eff6ff",
          border: "1px solid #bfdbfe",
          borderRadius: "8px",
          padding: "0.85rem 1.15rem",
          marginBottom: "1.25rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <ShieldCheck size={20} style={{ color: "#2563eb", flexShrink: 0 }} />
        <span style={{ color: "#1e3a8a", fontSize: "0.83rem" }}>
          Shortlisted candidates are ready for synchronous discussions or direct roster selection.
          All progression is authorized explicitly by the Team Lead.
        </span>
      </div>

      {shortlistedApps.length === 0 ? (
        <EmptyState
          icon={BookmarkCheck}
          title="Shortlist is currently empty"
          description="Review applications and advance vetted candidates to 'Shortlisted' status to manage deliberations here."
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
                    {roleShortlist.map((app) => {
                      const applicant = app.applicant || {}
                      return (
                        <div key={app.id} className="shortlist-candidate-card">
                          <div className="shortlist-cand-header">
                            <div>
                              <strong className="cand-name">{applicant.full_name}</strong>
                              <p className="cand-sub">
                                {applicant.email} {applicant.location ? `• ${applicant.location}` : ""}
                              </p>
                            </div>
                            <Badge variant="Shortlisted">Shortlisted</Badge>
                          </div>

                          {/* Claimed Skills */}
                          {applicant.applicant_skills && applicant.applicant_skills.length > 0 && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", margin: "0.5rem 0" }}>
                              {applicant.applicant_skills.slice(0, 4).map((s) => (
                                <span
                                  key={s.id}
                                  style={{
                                    fontSize: "0.72rem",
                                    padding: "0.15rem 0.45rem",
                                    backgroundColor: "#e2e8f0",
                                    borderRadius: "9999px",
                                    color: "#334155",
                                  }}
                                >
                                  {s.skill?.skill_name}
                                </span>
                              ))}
                            </div>
                          )}

                          {app.motivation_statement && (
                            <p className="cand-snippet" style={{ fontSize: "0.8rem", color: "#475569", margin: "0.4rem 0" }}>
                              &ldquo;{app.motivation_statement.slice(0, 130)}...&rdquo;
                            </p>
                          )}

                          <div className="shortlist-cand-actions" style={{ marginTop: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                            <Link to={`/applications/${app.id}`}>
                              <Button size="sm" variant="outline">
                                Full Profile
                              </Button>
                            </Link>
                            <Button
                              size="sm"
                              variant="secondary"
                              icon={MessageSquare}
                              onClick={() => setInterviewModalApp(app)}
                            >
                              Schedule Discussion
                            </Button>
                            <Button
                              size="sm"
                              variant="primary"
                              icon={Award}
                              onClick={() => setSelectModalApp(app)}
                            >
                              Select for Team
                            </Button>
                            <button
                              type="button"
                              onClick={() => setRejectModalApp(app)}
                              className="btn btn-outline btn-sm"
                              style={{ color: "#dc2626", borderColor: "#fca5a5" }}
                              title="Mark Not Selected"
                            >
                              <XCircle size={14} />
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {/* Schedule Discussion Modal */}
      <Modal
        isOpen={Boolean(interviewModalApp)}
        onClose={() => setInterviewModalApp(null)}
        title="Schedule Candidate Discussion"
        footer={
          <>
            <Button variant="outline" onClick={() => setInterviewModalApp(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleScheduleInterview} loading={scheduling}>
              Confirm & Move to Discussion
            </Button>
          </>
        }
      >
        {interviewModalApp && (
          <form onSubmit={handleScheduleInterview}>
            <p style={{ margin: "0 0 1rem 0", color: "#475569", fontSize: "0.88rem" }}>
              Candidate: <strong>{interviewModalApp.applicant?.full_name}</strong>
              <br />
              Role: <em>{interviewModalApp.role?.role_name}</em>
            </p>

            <div className="form-group" style={{ marginBottom: "0.9rem" }}>
              <label className="form-label">Discussion Format / Channel</label>
              <select
                value={interviewFormat}
                onChange={(e) => setInterviewFormat(e.target.value)}
                className="form-control"
              >
                <option value="Video Call">Video Call (Google Meet / Zoom / Discord)</option>
                <option value="Voice Call">Voice Call</option>
                <option value="Async Discussion / Chat">Async Discussion / Chat</option>
                <option value="In-Person">In-Person</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: "0.9rem" }}>
              <label className="form-label">Scheduled Date & Time (Optional)</label>
              <input
                type="datetime-local"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Discussion Objectives & Agenda Notes</label>
              <textarea
                value={interviewNotes}
                onChange={(e) => setInterviewNotes(e.target.value)}
                placeholder="Key topics, specific evidence to verify, and panel questions..."
                rows={3}
                className="form-control"
              />
            </div>
          </form>
        )}
      </Modal>

      {/* Direct Selection Confirmation Modal */}
      <Modal
        isOpen={Boolean(selectModalApp)}
        onClose={() => setSelectModalApp(null)}
        title="Confirm Candidate Selection"
        footer={
          <>
            <Button variant="outline" onClick={() => setSelectModalApp(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSelectCandidate} loading={selecting}>
              Confirm Selection for Roster
            </Button>
          </>
        }
      >
        {selectModalApp && (
          <form onSubmit={handleSelectCandidate}>
            <div
              style={{
                backgroundColor: "#f0fdf4",
                border: "1px solid #bbf7d0",
                borderRadius: "6px",
                padding: "0.75rem",
                marginBottom: "1rem",
              }}
            >
              <p style={{ margin: 0, fontSize: "0.85rem", color: "#166534" }}>
                You are selecting <strong>{selectModalApp.applicant?.full_name}</strong> for the role of{" "}
                <strong>{selectModalApp.role?.role_name}</strong>.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Selection Decision Note (Audit Trail)</label>
              <textarea
                value={selectionReason}
                onChange={(e) => setSelectionReason(e.target.value)}
                placeholder="State the rationale for final selection..."
                rows={3}
                className="form-control"
                required
              />
            </div>
          </form>
        )}
      </Modal>

      {/* Reject / Not Selected Modal */}
      <Modal
        isOpen={Boolean(rejectModalApp)}
        onClose={() => setRejectModalApp(null)}
        title="Mark Candidate Not Selected"
        footer={
          <>
            <Button variant="outline" onClick={() => setRejectModalApp(null)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={handleRejectCandidate}
              loading={rejecting}
              style={{ color: "#dc2626", borderColor: "#dc2626" }}
            >
              Confirm Not Selected
            </Button>
          </>
        }
      >
        {rejectModalApp && (
          <form onSubmit={handleRejectCandidate}>
            <p style={{ margin: "0 0 1rem 0", color: "#475569", fontSize: "0.85rem" }}>
              Move <strong>{rejectModalApp.applicant?.full_name}</strong> to <em>Not Selected</em>.
            </p>
            <div className="form-group">
              <label className="form-label">Audit Reason</label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="State the reason for not advancing the candidate..."
                rows={3}
                className="form-control"
                required
              />
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
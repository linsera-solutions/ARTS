import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { applicationsService, interviewsService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import { EmptyState } from "../components/common/EmptyState"
import { Modal } from "../components/common/Modal"
import {
  MessageSquare,
  Calendar,
  Video,
  CheckCircle2,
  User,
  ArrowRight,
  ShieldCheck,
  Clock,
  FileText,
} from "lucide-react"

export function Interviews() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [interviewApps, setInterviewApps] = useState([])
  const [allInterviews, setAllInterviews] = useState([])
  const [activeTab, setActiveTab] = useState("active") // "active" | "history"

  // Discussion outcome modal
  const [selectedApp, setSelectedApp] = useState(null)
  const [outcomeSummary, setOutcomeSummary] = useState("")
  const [nextDecision, setNextDecision] = useState("Selected")
  const [savingOutcome, setSavingOutcome] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [appsData, interviewsData] = await Promise.all([
        applicationsService.list({ status: "Discussion / Interview" }),
        interviewsService.list(),
      ])
      setInterviewApps(appsData?.items || appsData || [])
      setAllInterviews(interviewsData || [])
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
      // 1. Record completed interview entry
      await interviewsService.create({
        application_id: selectedApp.id,
        scheduled_at: new Date().toISOString(),
        format: "Video Call",
        status: "Completed",
        outcome_summary: outcomeSummary,
      })

      // 2. Transition application status based on human decision
      await applicationsService.updateStatus(selectedApp.id, {
        new_status: nextDecision,
        reason: `Discussion outcome recorded: ${outcomeSummary}`,
      })

      setSelectedApp(null)
      setOutcomeSummary("")
      loadData()
    } catch (err) {
      alert(`Failed to save outcome: ${err.message}`)
    } finally {
      setSavingOutcome(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading candidate discussions..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />

  const completedInterviews = allInterviews.filter((i) => i.status === "Completed")

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

      {/* Decision Support Banner */}
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
          Discussions allow structured alignment between candidate and recruiter. Outcoming
          decisions (Select, Return to Shortlist, or Not Select) are human-owned and logged in the audit trail.
        </span>
      </div>

      {/* View Tabs */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.5rem" }}>
        <button
          type="button"
          onClick={() => setActiveTab("active")}
          className={`btn btn-sm ${activeTab === "active" ? "btn-primary" : "btn-outline"}`}
        >
          Active in Discussion ({interviewApps.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("history")}
          className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-outline"}`}
        >
          Discussion History ({completedInterviews.length})
        </button>
      </div>

      {activeTab === "active" ? (
        interviewApps.length === 0 ? (
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

                <div className="interview-card-actions" style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
                  <Link to={`/applications/${app.id}`}>
                    <Button size="sm" variant="outline">
                      View Profile
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
        )
      ) : (
        /* Discussion History Tab */
        completedInterviews.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="No completed discussions recorded yet"
            description="When discussions are concluded and outcomes logged, their audit summaries will appear here."
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem" }}>
            {completedInterviews.map((item) => (
              <Card key={item.id}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                  <div>
                    <strong style={{ fontSize: "0.95rem", color: "#0f172a" }}>
                      {item.application?.applicant?.full_name || "Candidate"}
                    </strong>
                    <p style={{ margin: "0.15rem 0 0 0", fontSize: "0.82rem", color: "#64748b" }}>
                      Role: <strong>{item.application?.role?.role_name || "Team Role"}</strong> &bull; Format: {item.format || "Video Call"}
                    </p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Badge variant={item.application?.current_status || "default"}>
                      {item.application?.current_status || "Completed"}
                    </Badge>
                    <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                      {new Date(item.scheduled_at || item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {item.outcome_summary && (
                  <div style={{ backgroundColor: "#f8fafc", padding: "0.65rem 0.85rem", borderRadius: "6px", border: "1px solid #e2e8f0", marginTop: "0.5rem" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginBottom: "0.25rem" }}>
                      Discussion Outcome & Findings:
                    </div>
                    <p style={{ margin: 0, fontSize: "0.83rem", color: "#1e293b", lineHeight: "1.5" }}>
                      {item.outcome_summary}
                    </p>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )
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
            <p style={{ margin: "0 0 1rem 0", color: "#475569", fontSize: "0.88rem" }}>
              Candidate: <strong>{selectedApp.applicant?.full_name}</strong>
              <br />
              Target Role: <em>{selectedApp.role?.role_name}</em>
            </p>

            <div className="form-group" style={{ marginBottom: "1rem" }}>
              <label className="form-label">Discussion Summary & Key Observations</label>
              <textarea
                value={outcomeSummary}
                onChange={(e) => setOutcomeSummary(e.target.value)}
                placeholder="Summarize key discussion points, communication clarity, role commitment, and panel consensus..."
                rows={4}
                className="form-control"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Post-Discussion Status Transition (Human Decision)</label>
              <select
                value={nextDecision}
                onChange={(e) => setNextDecision(e.target.value)}
                className="form-control"
                required
              >
                <option value="Selected">Selected — Confirm Candidate for Team Roster Slot</option>
                <option value="Shortlisted">Shortlisted — Return to Shortlist (Backup / Re-evaluate)</option>
                <option value="Not Selected">Not Selected — Do Not Advance</option>
              </select>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
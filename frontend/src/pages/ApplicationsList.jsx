import React, { useState, useEffect } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { applicationsService, rolesService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import { EmptyState } from "../components/common/EmptyState"
import { Modal } from "../components/common/Modal"
import { Users, Search, Filter, ArrowRight, CheckCircle2 } from "lucide-react"

const APPROVED_STATUSES = [
  "Received",
  "Under Review",
  "Shortlisted",
  "Discussion / Interview",
  "Selected",
  "Not Selected",
  "Withdrawn",
]

export function ApplicationsList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const roleFilter = searchParams.get("role") || ""
  const statusFilter = searchParams.get("status") || ""

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [applications, setApplications] = useState([])
  const [roles, setRoles] = useState([])
  const [searchQuery, setSearchQuery] = useState("")

  // Quick status update modal state
  const [selectedApp, setSelectedApp] = useState(null)
  const [allowedTransitions, setAllowedTransitions] = useState([])
  const [newStatus, setNewStatus] = useState("")
  const [statusReason, setStatusReason] = useState("")
  const [updating, setUpdating] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [appsData, rolesData] = await Promise.all([
        applicationsService.list({
          role_id: roleFilter || undefined,
          status: statusFilter || undefined,
          page_size: 100,
        }),
        rolesService.list(),
      ])
      setApplications(appsData?.items || appsData || [])
      setRoles(rolesData?.items || rolesData || [])
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [roleFilter, statusFilter])

  const handleOpenStatusModal = async (app) => {
    setSelectedApp(app)
    setStatusReason("")
    try {
      const trans = await applicationsService.getAllowedTransitions(app.id)
      const allowed = trans?.allowed_transitions || []
      setAllowedTransitions(allowed)
      setNewStatus(allowed[0] || "")
    } catch (err) {
      setAllowedTransitions([])
      setNewStatus("")
    }
  }

  const handleStatusChangeSubmit = async (e) => {
    e.preventDefault()
    if (!selectedApp || !newStatus) return

    setUpdating(true)
    try {
      await applicationsService.updateStatus(selectedApp.id, {
        new_status: newStatus,
        reason: statusReason || "Status update via application list",
      })
      setSelectedApp(null)
      setNewStatus("")
      setStatusReason("")
      loadData()
    } catch (err) {
      alert(`Failed to update status: ${err.message}`)
    } finally {
      setUpdating(false)
    }
  }

  const filteredApps = applications.filter((app) => {
    const candidateName = app.applicant?.full_name?.toLowerCase() || ""
    const candidateEmail = app.applicant?.email?.toLowerCase() || ""
    const query = searchQuery.toLowerCase()
    return candidateName.includes(query) || candidateEmail.includes(query)
  })

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Applications Intake & Review</h1>
          <p className="page-subtitle">
            Recruiter evaluation console for candidate submissions
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="search-input-wrapper">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search candidates by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-select-group">
          <select
            value={roleFilter}
            onChange={(e) => setSearchParams({ role: e.target.value, status: statusFilter })}
            className="filter-select"
          >
            <option value="">All Roles (4 Positions)</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.role_name}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setSearchParams({ role: roleFilter, status: e.target.value })}
            className="filter-select"
          >
            <option value="">All Statuses</option>
            {APPROVED_STATUSES.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorAlert error={error} onRetry={loadData} />}

      {loading ? (
        <LoadingSpinner message="Loading applications..." />
      ) : filteredApps.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No applications match your criteria"
          description={
            searchQuery || roleFilter || statusFilter
              ? "Try resetting your search or filter options."
              : "Google Forms applicant submissions will appear here."
          }
        />
      ) : (
        <div className="table-responsive">
          <table className="arts-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Target Role</th>
                <th>Location</th>
                <th>Status</th>
                <th>Submitted</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredApps.map((app) => (
                <tr key={app.id}>
                  <td>
                    <div className="table-candidate-cell">
                      <strong className="candidate-name">
                        {app.applicant?.full_name || "Anonymous Applicant"}
                      </strong>
                      <span className="candidate-email">{app.applicant?.email}</span>
                    </div>
                  </td>
                  <td>
                    <span className="role-tag">
                      {app.role?.role_name || "Role Reference"}
                    </span>
                  </td>
                  <td>
                    <span className="location-text">
                      {app.applicant?.location || "—"}
                    </span>
                  </td>
                  <td>
                    <Badge>{app.current_status}</Badge>
                  </td>
                  <td>
                    <span className="date-text">
                      {new Date(app.submission_date).toLocaleDateString()}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div className="action-buttons-group">
                      <button
                        type="button"
                        onClick={() => handleOpenStatusModal(app)}
                        className="btn btn-outline btn-sm"
                        title="Update candidate lifecycle status"
                      >
                        Advance
                      </button>
                      <Link to={`/applications/${app.id}`}>
                        <Button size="sm" variant="secondary" icon={ArrowRight}>
                          Review
                        </Button>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Quick Status Modal */}
      <Modal
        isOpen={Boolean(selectedApp)}
        onClose={() => setSelectedApp(null)}
        title="Update Application Status"
        footer={
          <>
            <Button variant="outline" onClick={() => setSelectedApp(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleStatusChangeSubmit}
              loading={updating}
              disabled={allowedTransitions.length === 0}
            >
              Confirm Status Change
            </Button>
          </>
        }
      >
        {selectedApp && (
          <form onSubmit={handleStatusChangeSubmit} className="status-modal-form">
            <p style={{ margin: "0 0 1rem 0", color: "#475569" }}>
              Candidate: <strong>{selectedApp.applicant?.full_name}</strong>
              <br />
              Role: <em>{selectedApp.role?.role_name}</em>
              <br />
              Current Status: <strong>{selectedApp.current_status}</strong>
            </p>

            {allowedTransitions.length === 0 ? (
              <div style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "1rem" }}>
                This application is in a terminal status and cannot be transitioned further.
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Permitted Next Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="form-control"
                    required
                  >
                    {allowedTransitions.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginTop: "1rem" }}>
                  <label className="form-label">Decision Note / Rationale</label>
                  <textarea
                    value={statusReason}
                    onChange={(e) => setStatusReason(e.target.value)}
                    placeholder="Provide rationale for advancing or modifying candidate status..."
                    rows={3}
                    className="form-control"
                  />
                </div>
              </>
            )}
          </form>
        )}
      </Modal>
    </div>
  )
}
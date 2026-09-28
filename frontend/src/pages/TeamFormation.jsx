import React, { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { teamsService } from "../api/services"
import { Card } from "../components/common/Card"
import { Badge } from "../components/common/Badge"
import { Button } from "../components/common/Button"
import { LoadingSpinner } from "../components/common/Loading"
import { ErrorAlert } from "../components/common/ErrorAlert"
import { EmptyState } from "../components/common/EmptyState"
import { Modal } from "../components/common/Modal"
import {
  Award,
  UserCheck,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  RefreshCw,
  Trash2,
  Users,
  PlusCircle,
  Calendar,
  Sparkles,
} from "lucide-react"

export function TeamFormation() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [teamOverview, setTeamOverview] = useState(null)

  // Assign Candidate Modal
  const [assignModalOpen, setAssignModalOpen] = useState(false)
  const [targetRoleId, setTargetRoleId] = useState("")
  const [selectedApplicationId, setSelectedApplicationId] = useState("")
  const [assigning, setAssigning] = useState(false)

  // Reassign Member Modal
  const [reassignModalMember, setReassignModalMember] = useState(null)
  const [newRoleId, setNewRoleId] = useState("")
  const [reassignReason, setReassignReason] = useState("")
  const [reassigning, setReassigning] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await teamsService.getOverview()
      setTeamOverview(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleOpenAssignModal = (roleId = "", appId = "") => {
    setTargetRoleId(roleId)
    setSelectedApplicationId(appId)
    setAssignModalOpen(true)
  }

  const handleAssignSubmit = async (e) => {
    e.preventDefault()
    if (!selectedApplicationId || !targetRoleId || !teamOverview) return
    setAssigning(true)
    try {
      await teamsService.assignMember(teamOverview.team_id, {
        application_id: selectedApplicationId,
        role_id: targetRoleId,
      })
      setAssignModalOpen(false)
      setSelectedApplicationId("")
      setTargetRoleId("")
      loadData()
    } catch (err) {
      alert(`Failed to assign candidate: ${err.message}`)
    } finally {
      setAssigning(false)
    }
  }

  const handleReassignSubmit = async (e) => {
    e.preventDefault()
    if (!reassignModalMember || !newRoleId) return
    setReassigning(true)
    try {
      await teamsService.reassignMember(reassignModalMember.id, {
        target_role_id: newRoleId,
        reason: reassignReason || "Role slot rebalanced by Team Lead",
      })
      setReassignModalMember(null)
      setNewRoleId("")
      setReassignReason("")
      loadData()
    } catch (err) {
      alert(`Failed to reassign member: ${err.message}`)
    } finally {
      setReassigning(false)
    }
  }

  const handleRemoveMember = async (member) => {
    const confirm = window.confirm(
      `Remove ${member.applicant?.full_name} from the ${member.role?.role_name} roster slot? The slot will become vacant.`
    )
    if (!confirm) return
    try {
      await teamsService.removeMember(member.id, "Removed from roster slot by Team Lead")
      loadData()
    } catch (err) {
      alert(`Failed to remove member: ${err.message}`)
    }
  }

  if (loading) return <LoadingSpinner message="Loading 4-member team composition..." />
  if (error) return <ErrorAlert error={error} onRetry={loadData} />
  if (!teamOverview) return <ErrorAlert message="Unable to load team overview." />

  const { slots, filled_slots_count, total_slots, is_team_complete, unassigned_selected_candidates } = teamOverview
  const vacantSlots = slots.filter((s) => !s.is_filled)

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
          Team Formation is a human-controlled decision process. The Team Lead explicitly confirms
          slot assignments, balances skills, and handles reassignments without algorithmic automation.
        </span>
      </div>

      {/* Roster Completion Status Banner */}
      <div className="team-status-banner" style={{ marginBottom: "1.5rem" }}>
        <div className="banner-icon">
          {is_team_complete ? (
            <CheckCircle2 size={32} style={{ color: "#16a34a" }} />
          ) : (
            <Award size={32} style={{ color: "#4f46e5" }} />
          )}
        </div>
        <div className="banner-content">
          <h3 style={{ margin: "0 0 0.25rem 0", fontSize: "1.1rem" }}>
            Team Roster Status: {filled_slots_count} of {total_slots} Positions Filled
          </h3>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#475569" }}>
            {is_team_complete
              ? "All 4 target team roles have confirmed selected members. Team is fully assembled for the challenge!"
              : `${total_slots - filled_slots_count} slot(s) remaining. Assign confirmed candidates to complete the roster.`}
          </p>
        </div>
      </div>

      {/* 4 Approved Roles Roster Grid */}
      <h2 style={{ fontSize: "1.1rem", fontWeight: "700", color: "#1e293b", marginBottom: "0.75rem" }}>
        Team Roster Slots ({slots.length})
      </h2>
      <div className="roster-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.25rem", marginBottom: "2rem" }}>
        {slots.map((slot, idx) => {
          const isFilled = slot.is_filled
          const member = slot.assigned_member
          const applicant = member?.applicant || {}

          return (
            <Card
              key={slot.role_id}
              className={`roster-slot-card ${isFilled ? "slot-filled" : "slot-vacant"}`}
              style={{
                border: isFilled ? "2px solid #86efac" : "1px dashed #cbd5e1",
                backgroundColor: isFilled ? "#ffffff" : "#f8fafc",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>
                    Position #{idx + 1}
                  </span>
                  {isFilled ? (
                    <Badge variant="Selected">Confirmed Roster Slot</Badge>
                  ) : (
                    <Badge variant="Open">Position Vacant</Badge>
                  )}
                </div>

                <h3 style={{ fontSize: "1.02rem", fontWeight: "700", color: "#0f172a", margin: "0 0 0.35rem 0" }}>
                  {slot.role_name}
                </h3>
                {slot.role_description && (
                  <p style={{ fontSize: "0.78rem", color: "#64748b", lineHeight: "1.45", margin: "0 0 1rem 0" }}>
                    {slot.role_description}
                  </p>
                )}
              </div>

              {/* Slot Occupant Area */}
              <div style={{ marginTop: "1rem" }}>
                {isFilled ? (
                  <div
                    style={{
                      padding: "0.85rem",
                      backgroundColor: "#f0fdf4",
                      border: "1px solid #bbf7d0",
                      borderRadius: "8px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem", marginBottom: "0.75rem" }}>
                      <UserCheck size={20} style={{ color: "#16a34a", flexShrink: 0, marginTop: "2px" }} />
                      <div>
                        <strong style={{ fontSize: "0.92rem", color: "#166534" }}>{applicant.full_name}</strong>
                        <div style={{ fontSize: "0.76rem", color: "#334155" }}>{applicant.email}</div>
                        {applicant.location && (
                          <div style={{ fontSize: "0.74rem", color: "#64748b" }}>{applicant.location}</div>
                        )}
                        <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                          Joined: {new Date(member.join_date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    {/* Member Actions */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", justifyContent: "flex-end", borderTop: "1px solid #bbf7d0", paddingTop: "0.5rem" }}>
                      <Link to={`/applications/${member.source_application_id}`}>
                        <Button size="sm" variant="outline">
                          Profile
                        </Button>
                      </Link>
                      {vacantSlots.length > 0 && (
                        <Button
                          size="sm"
                          variant="secondary"
                          icon={RefreshCw}
                          onClick={() => {
                            setReassignModalMember(member)
                            setNewRoleId(vacantSlots[0]?.role_id || "")
                          }}
                        >
                          Reassign
                        </Button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(member)}
                        className="btn btn-outline btn-sm"
                        style={{ color: "#dc2626", borderColor: "#fca5a5" }}
                        title="Remove from slot"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      padding: "1rem",
                      backgroundColor: "#ffffff",
                      border: "1px dashed #cbd5e1",
                      borderRadius: "8px",
                      textAlign: "center",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.4rem", color: "#d97706", fontSize: "0.82rem", marginBottom: "0.75rem" }}>
                      <AlertCircle size={16} />
                      <span>Slot currently open & unfilled.</span>
                    </div>
                    {unassigned_selected_candidates.length > 0 ? (
                      <Button
                        size="sm"
                        variant="primary"
                        icon={PlusCircle}
                        onClick={() => handleOpenAssignModal(slot.role_id, unassigned_selected_candidates[0]?.application_id)}
                      >
                        Assign Selected Candidate
                      </Button>
                    ) : (
                      <Link to={`/applications?status=Shortlisted`}>
                        <Button size="sm" variant="outline" icon={ArrowRight}>
                          Review Shortlist
                        </Button>
                      </Link>
                    )}
                  </div>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Unassigned Selected Candidates Pool */}
      <Card
        title="Unassigned Selected Candidates Pool"
        subtitle="Candidates confirmed in 'Selected' status ready to be placed into team roster slots"
      >
        {unassigned_selected_candidates.length === 0 ? (
          <p style={{ margin: 0, color: "#64748b", fontSize: "0.85rem" }}>
            No unassigned selected candidates. Candidates moved to &lsquo;Selected&rsquo; status in the recruitment workflow will appear here for placement.
          </p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "0.9rem" }}>
            {unassigned_selected_candidates.map((cand) => (
              <div
                key={cand.application_id}
                style={{
                  padding: "0.85rem",
                  backgroundColor: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.25rem" }}>
                    <strong style={{ fontSize: "0.92rem", color: "#0f172a" }}>{cand.full_name}</strong>
                    <Badge variant="Selected">Selected</Badge>
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "#475569" }}>
                    Applied: <em>{cand.original_applied_role}</em>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>{cand.email}</div>

                  {/* Skills */}
                  {cand.skills && cand.skills.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem", margin: "0.5rem 0" }}>
                      {cand.skills.slice(0, 3).map((sk, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: "0.7rem",
                            padding: "0.1rem 0.4rem",
                            backgroundColor: "#e2e8f0",
                            borderRadius: "9999px",
                            color: "#334155",
                          }}
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div style={{ marginTop: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Link to={`/applications/${cand.application_id}`} style={{ fontSize: "0.78rem", color: "#2563eb" }}>
                    View Profile
                  </Link>
                  {vacantSlots.length > 0 && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleOpenAssignModal(vacantSlots[0]?.role_id, cand.application_id)}
                    >
                      Assign to Slot
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Assign Candidate Modal */}
      <Modal
        isOpen={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Candidate to Team Role Slot"
        footer={
          <>
            <Button variant="outline" onClick={() => setAssignModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAssignSubmit} loading={assigning}>
              Confirm Slot Assignment
            </Button>
          </>
        }
      >
        <form onSubmit={handleAssignSubmit}>
          <div className="form-group" style={{ marginBottom: "1rem" }}>
            <label className="form-label">Select Candidate (from Selected Pool)</label>
            <select
              value={selectedApplicationId}
              onChange={(e) => setSelectedApplicationId(e.target.value)}
              className="form-control"
              required
            >
              <option value="">-- Choose Selected Candidate --</option>
              {unassigned_selected_candidates.map((cand) => (
                <option key={cand.application_id} value={cand.application_id}>
                  {cand.full_name} ({cand.original_applied_role}) - {cand.email}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Target Team Role Slot</label>
            <select
              value={targetRoleId}
              onChange={(e) => setTargetRoleId(e.target.value)}
              className="form-control"
              required
            >
              <option value="">-- Choose Role Slot --</option>
              {vacantSlots.map((slot) => (
                <option key={slot.role_id} value={slot.role_id}>
                  {slot.role_name} (Vacant)
                </option>
              ))}
            </select>
          </div>
        </form>
      </Modal>

      {/* Reassign Member Modal */}
      <Modal
        isOpen={Boolean(reassignModalMember)}
        onClose={() => setReassignModalMember(null)}
        title="Reassign Team Member Slot"
        footer={
          <>
            <Button variant="outline" onClick={() => setReassignModalMember(null)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleReassignSubmit} loading={reassigning}>
              Confirm Reassignment
            </Button>
          </>
        }
      >
        {reassignModalMember && (
          <form onSubmit={handleReassignSubmit}>
            <div style={{ backgroundColor: "#f8fafc", padding: "0.75rem", borderRadius: "6px", border: "1px solid #e2e8f0", marginBottom: "1rem" }}>
              Member: <strong>{reassignModalMember.applicant?.full_name}</strong>
              <br />
              Current Slot: <em>{reassignModalMember.role?.role_name}</em>
            </div>

            <div className="form-group" style={{ marginBottom: "1rem" }}>
              <label className="form-label">Select New Vacant Role Slot</label>
              <select
                value={newRoleId}
                onChange={(e) => setNewRoleId(e.target.value)}
                className="form-control"
                required
              >
                <option value="">-- Choose New Role Slot --</option>
                {vacantSlots.map((slot) => (
                  <option key={slot.role_id} value={slot.role_id}>
                    {slot.role_name} (Vacant)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Reassignment Rationale (Audit Note)</label>
              <textarea
                value={reassignReason}
                onChange={(e) => setReassignReason(e.target.value)}
                placeholder="State the reason for moving the candidate to a new role slot..."
                rows={3}
                className="form-control"
              />
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}